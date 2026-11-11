"""Bulk vehicle import for rental suppliers from Excel (.xlsx) or CSV exports.

Files are parsed with the standard library only. Headers are matched through
aliases so exports from different fleet systems map onto the same fields.
Only inventory data is imported: customer, rental and contract state stays in
the contract workflow, so a "KİRADA" row does not assign a customer.
"""

import csv
import io
import re
import zipfile
from datetime import date, datetime, timedelta
from xml.etree import ElementTree as ET

from fastapi import HTTPException

from app import models as m
from app.common.time import stamp

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 2000
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def norm(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").translate(TR).lower()).strip()


# field -> accepted header spellings (normalized). First match wins.
ALIASES = {
    "plate": ["plaka", "plaka no", "arac plakasi"],
    "chassis_no": ["sase", "sasi", "sase no", "sasi no", "sase numarasi", "vin"],
    "brand": ["marka"],
    "type_text": ["tip", "model", "arac tipi", "marka model"],
    "year": ["model yili", "yil", "uretim yili"],
    "fuel": ["yakit", "yakit tipi"],
    "color": ["renk"],
    "mileage": ["km", "kilometre", "guncel km", "arac km"],
    "transmission": ["sanziman", "vites", "vites tipi"],
    "engine_no": ["motor numarasi", "motor no"],
    "inspection_date": ["muayene bitis tarih", "muayene bitis tarihi", "muayene tarihi"],
    "registration_date": ["ilk tescil tarihi", "tescil tarihi"],
    "vehicle_segment": ["segment"],
    "vehicle_group": ["grup", "arac grubu"],
    "license_serial_no": ["ruhsat seri no", "ruhsat no", "belge seri no"],
    "casco_insurance_expiry_date": ["kasko bitis tarihi", "kasko bitis"],
    "traffic_insurance_expiry_date": ["trafik sigortasi bitis tarihi", "trafik bitis"],
    "hgs_no": ["hgs etiketi", "hgs no"],
    "erp_id": ["id", "erp id", "arac id"],
    "damaged": ["hasarli"],
    "in_service": ["serviste"],
    "stolen": ["calinti"],
}
DATE_FIELDS = {
    "inspection_date",
    "registration_date",
    "casco_insurance_expiry_date",
    "traffic_insurance_expiry_date",
}
# Fields an import may set or refresh on a vehicle.
INVENTORY_FIELDS = [
    "plate",
    "brand",
    "model",
    "version",
    "year",
    "fuel",
    "color",
    "transmission",
    "engine_no",
    "inspection_date",
    "registration_date",
    "vehicle_segment",
    "vehicle_group",
    "license_serial_no",
    "casco_insurance_expiry_date",
    "traffic_insurance_expiry_date",
    "hgs_no",
    "erp_id",
]
LABELS = {
    "plate": "Plaka",
    "chassis_no": "Şase",
    "brand": "Marka",
    "type_text": "Tip / Model",
    "year": "Model Yılı",
    "fuel": "Yakıt",
    "mileage": "KM",
    "inspection_date": "Muayene Bitiş",
}
REQUIRED = ["plate", "chassis_no", "brand", "type_text", "year", "fuel"]
FUELS = {
    "benzin": "Benzin",
    "dizel": "Dizel",
    "motorin": "Dizel",
    "lpg": "LPG",
    "hibrit": "Hibrit",
    "hybrid": "Hibrit",
    "elektrik": "Elektrik",
    "elektrikli": "Elektrik",
}


def _col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(content):
    try:
        book = zipfile.ZipFile(io.BytesIO(content))
        names = book.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(book.read("xl/sharedStrings.xml")).iter(NS + "si"):
                shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
        sheet = next(n for n in sorted(names) if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        rows = []
        for row in ET.fromstring(book.read(sheet)).iter(NS + "row"):
            values = {}
            for cell in row.iter(NS + "c"):
                kind, v = cell.get("t"), cell.find(NS + "v")
                if kind == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iter(NS + "t"))
                elif v is None or v.text is None:
                    continue
                elif kind == "s":
                    value = shared[int(v.text)]
                else:
                    value = v.text
                values[_col(cell.get("r"))] = value
            rows.append(values)
    except (zipfile.BadZipFile, StopIteration, ET.ParseError, KeyError, ValueError, IndexError):
        raise HTTPException(400, "Excel dosyası okunamadı. .xlsx veya .csv yükleyin.")
    if not rows:
        return []
    width = max((max(r) for r in rows if r), default=-1) + 1
    return [[str(r.get(i, "")) for i in range(width)] for r in rows]


def read_csv(content):
    text = None
    for encoding in ("utf-8-sig", "cp1254", "latin-1"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t") if text.strip() else csv.excel
    return [row for row in csv.reader(io.StringIO(text), dialect)]


def read_table(content, filename):
    if not content:
        raise HTTPException(400, "Dosya boş.")
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Dosya en fazla 5 MB olabilir.")
    name = (filename or "").lower()
    if name.endswith(".xls"):
        raise HTTPException(
            400, "Eski .xls biçimi desteklenmiyor. Dosyayı .xlsx olarak kaydedin."
        )
    return read_csv(content) if name.endswith(".csv") else read_xlsx(content)


def parse_date(value):
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "null", "none", "-"}:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", text):  # Excel serial date
        serial = float(text)
        if 20000 < serial < 80000:
            return (date(1899, 12, 30) + timedelta(days=int(serial))).isoformat()
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(text[:10], fmt).date()
            break
        except ValueError:
            continue
    else:
        return "invalid"
    return None if parsed.year <= 1970 else parsed.isoformat()  # 1970-01-01 = empty


def parse_int(value):
    text = str(value or "").strip().replace(" ", "")
    if not text or text.lower() == "nan":
        return None
    text = text.replace(".", "").replace(",", ".") if re.search(r"\d\.\d{3}", text) else text
    try:
        return int(float(text.replace(",", ".")))
    except ValueError:
        return "invalid"


def normalize_plate(value):
    raw = re.sub(r"\s+", "", str(value or "")).upper().replace("İ", "I")
    match = re.fullmatch(r"(\d{2})([A-Z]{1,3})(\d{2,5})", raw)
    return " ".join(match.groups()) if match else raw


def split_type(text, year):
    words = str(text or "").split()
    if words and year and words[-1] == str(year):
        words = words[:-1]
    return (words[0] if words else ""), " ".join(words[1:]) or None


def brand_name(value):
    text = str(value or "").strip()
    # Short brands are acronyms (BMW, DS, MG); longer ones read better title-cased.
    return (text.upper() if len(text) <= 3 else text.title()) or None


def yes(value):
    return norm(value) in {"evet", "var", "e", "yes", "true", "1"}


def map_headers(header):
    normalized = [norm(h) for h in header]
    mapping, used = {}, set()
    for field, names in ALIASES.items():
        for name in names:
            if name in normalized and normalized.index(name) not in used:
                mapping[field] = normalized.index(name)
                used.add(normalized.index(name))
                break
    ignored = [h for i, h in enumerate(header) if i not in used and str(h).strip()]
    return mapping, ignored


def build_rows(table):
    if len(table) < 2:
        raise HTTPException(400, "Dosyada başlık satırı ve en az bir araç olmalı.")
    header = table[0]
    mapping, ignored = map_headers(header)
    missing = [LABELS[f] for f in ("plate", "chassis_no") if f not in mapping]
    if missing:
        raise HTTPException(400, f"Zorunlu sütun bulunamadı: {', '.join(missing)}.")
    body = [r for r in table[1:] if any(str(c).strip() for c in r)]
    if len(body) > MAX_ROWS:
        raise HTTPException(400, f"Tek seferde en fazla {MAX_ROWS} araç yüklenebilir.")
    rows = []
    for index, raw in enumerate(table[1:], start=2):
        cell = {f: (raw[i].strip() if i < len(raw) else "") for f, i in mapping.items()}
        if not cell.get("plate") and not cell.get("chassis_no"):
            continue  # blank or totals row
        errors, warnings = [], []
        for field in REQUIRED:
            if not cell.get(field):
                errors.append(f"{LABELS[field]} boş.")
        year = parse_int(cell.get("year"))
        if year == "invalid" or (year and not 1950 <= year <= date.today().year + 1):
            errors.append("Model yılı geçersiz.")
            year = None
        mileage = parse_int(cell.get("mileage"))
        if mileage == "invalid" or (mileage is not None and mileage < 0):
            errors.append("KM geçersiz.")
            mileage = None
        values = {
            "chassis_no": re.sub(r"\s+", "", cell.get("chassis_no", "")).upper(),
            "plate": normalize_plate(cell.get("plate")),
            "brand": brand_name(cell.get("brand")),
            "year": year,
            "mileage": mileage,
        }
        values["model"], values["version"] = split_type(cell.get("type_text"), year)
        fuel = norm(cell.get("fuel"))
        values["fuel"] = FUELS.get(fuel, cell.get("fuel") or None)
        if cell.get("fuel") and fuel not in FUELS:
            warnings.append(f"Yakıt tipi tanınmadı: {cell['fuel']}.")
        for field in ("color", "transmission", "engine_no", "vehicle_segment", "vehicle_group"):
            values[field] = cell.get(field) or None
        for field in ("license_serial_no", "hgs_no", "erp_id"):
            values[field] = cell.get(field) or None
        for field in DATE_FIELDS:
            parsed = parse_date(cell.get(field))
            if parsed == "invalid":
                warnings.append(f"Tarih okunamadı: {cell.get(field)}.")
                parsed = None
            values[field] = parsed
        if values["chassis_no"] and not re.fullmatch(r"[A-Z0-9]{11,17}", values["chassis_no"]):
            errors.append("Şase numarası 11-17 harf/rakam olmalı.")
        if values["plate"] and not re.fullmatch(r"\d{2} [A-Z]{1,3} \d{2,5}", values["plate"]):
            warnings.append(f"Plaka biçimi alışılmadık: {values['plate']}.")
        if not values["inspection_date"]:
            warnings.append("Muayene tarihi yok.")
        status = "Aktif"
        if yes(cell.get("damaged")):
            status = "Hasar"
        elif yes(cell.get("in_service")):
            status = "Serviste"
        if yes(cell.get("stolen")):
            errors.append("Çalıntı olarak işaretli araç içe aktarılmaz.")
        values["status"] = status
        rows.append({"row": index, "values": values, "errors": errors, "warnings": warnings})
    return rows, ignored


def plan(db, ctx, rows):
    """Decide create/update per row against existing vehicles and within the file."""
    chassis = [r["values"]["chassis_no"] for r in rows if r["values"]["chassis_no"]]
    existing = {
        v.chassis_no: v
        for v in db.query(m.Vehicle).filter(m.Vehicle.chassis_no.in_(chassis)).all()
    }
    plates = {
        v.plate.replace(" ", ""): v
        for v in db.query(m.Vehicle).filter_by(supplier_id=ctx["id"]).all()
        if v.plate
    }
    seen_chassis, seen_plates = {}, {}
    for r in rows:
        v = r["values"]
        if v["chassis_no"] in seen_chassis:
            first = seen_chassis[v["chassis_no"]]
            r["errors"].append(f"Şase dosyada tekrar ediyor (satır {first}).")
        if v["plate"] in seen_plates:
            first = seen_plates[v["plate"]]
            r["errors"].append(f"Plaka dosyada tekrar ediyor (satır {first}).")
        seen_chassis.setdefault(v["chassis_no"], r["row"])
        seen_plates.setdefault(v["plate"], r["row"])
        car = existing.get(v["chassis_no"])
        if car and car.supplier_id != ctx["id"]:
            r["errors"].append("Bu şase başka bir hesapta kayıtlı.")
        same_plate = plates.get(v["plate"].replace(" ", ""))
        if same_plate and same_plate.chassis_no != v["chassis_no"]:
            r["errors"].append(f"Plaka başka bir araçta kayıtlı ({same_plate.chassis_no}).")
        if car and car.status == "Satıldı":
            r["errors"].append("Satışı tamamlanmış araç güncellenemez.")
        r["action"] = "error" if r["errors"] else ("update" if car else "create")
        if car and not r["errors"]:
            changes = [
                f
                for f in INVENTORY_FIELDS
                if v.get(f) not in (None, "") and getattr(car, f, None) != v[f]
            ]
            if v["mileage"] is not None and v["mileage"] > (car.mileage or 0):
                changes.append("mileage")
            elif v["mileage"] is not None and v["mileage"] < (car.mileage or 0):
                r["warnings"].append(
                    f"Dosyadaki KM ({v['mileage']}) kayıttakinden ({car.mileage}) düşük; "
                    "KM güncellenmez."
                )
            r["changes"] = changes
            if not changes:
                r["action"] = "unchanged"
    return rows


def summarize(rows, ignored):
    count = lambda action: sum(1 for r in rows if r["action"] == action)  # noqa: E731
    return {
        "total": len(rows),
        "create": count("create"),
        "update": count("update"),
        "unchanged": count("unchanged"),
        "error": count("error"),
        "warnings": sum(1 for r in rows if r["warnings"]),
        "ignored_columns": ignored,
        "rows": rows,
    }


def apply(db, ctx, rows):
    created = updated = 0
    for r in rows:
        v = r["values"]
        if r["action"] == "create":
            car = m.Vehicle(
                id=v["chassis_no"],
                supplier_id=ctx["id"],
                customer_id=None,
                is_active=True,
                last_service_mileage=0,
                **{f: v[f] for f in INVENTORY_FIELDS + ["chassis_no", "status"]},
                mileage=v["mileage"] or 0,
            )
            db.add(car)
            db.flush()
            db.add(
                m.VehicleMileageRecord(
                    vehicle_id=car.id,
                    mileage=car.mileage,
                    recorded_at=stamp(),
                    source="bulk_import",
                )
            )
            created += 1
        elif r["action"] == "update":
            car = db.get(m.Vehicle, v["chassis_no"])
            for field in r["changes"]:
                setattr(car, field, v[field])
            if "mileage" in r["changes"]:
                db.add(
                    m.VehicleMileageRecord(
                        vehicle_id=car.id,
                        mileage=car.mileage,
                        recorded_at=stamp(),
                        source="bulk_import",
                    )
                )
            updated += 1
    db.commit()
    return {"created": created, "updated": updated}
