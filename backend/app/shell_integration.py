"""Shell TTS V3.4.4: confirmed sales, explicitly mapped to company vehicles."""

import calendar
import hashlib
import json
import os
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as m
from app.common.time import stamp
from app.database import get_db
from app.supplier_context import context, vehicle
from app.supplier_integrations import MAX_RESPONSE, MappingInput, NoRedirect, owner

router = APIRouter(
    prefix="/api/supplier-workspace/integrations/shell", tags=["Supplier integrations"]
)
ENDPOINT = "https://tts.turkiyeshell.com/TTS/TTSWebServices.asmx"
NAMESPACE = "https://tts.turkiyeshell.com"
METHOD = "GetCustomerSalesTransaction_with_rid"
LOCAL = ZoneInfo("Europe/Istanbul")


def credentials(sid):
    return {
        key: os.environ.get(f"SHELL_{sid}_{key.upper()}", "")
        for key in ("cust_code", "user_id", "password")
    }


class ShellConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    branch_code: str = Field("", max_length=10)


class SalesQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_range(self):
        today = datetime.now(LOCAL).date()
        month = today.year * 12 + today.month - 1 - 15
        year, month = divmod(month, 12)
        earliest = date(year, month + 1, min(today.day, calendar.monthrange(year, month + 1)[1]))
        if not earliest <= self.start_date <= self.end_date < today:
            raise ValueError("Tarih aralığı son 15 ay içinde olmalı ve en geç dün bitmelidir.")
        if (self.end_date - self.start_date).days >= 31:
            raise ValueError("Tek sorguda en fazla 31 günlük veri alınabilir.")
        return self


def config(db, sid):
    row = db.query(m.SupplierSetting).filter_by(supplier_id=sid).first()
    return (row.value or {}).get("shell") if row else None


def request_body(sid, cfg, query):
    fields = credentials(sid)
    if not all(fields.values()):
        raise HTTPException(503, "Shell sunucu erişim bilgileri yapılandırılmadı.")
    envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
    body = ET.SubElement(envelope, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
    call = ET.SubElement(body, f"{{{NAMESPACE}}}{METHOD}")
    fields.update(
        {
            "branch_code": cfg["branch_code"],
            "report_start_dt": datetime.combine(query.start_date, time.min).isoformat(),
            "report_end_dt": datetime.combine(query.end_date, time(23, 59, 59)).isoformat(),
            "plate_code": "",
            "department_code": "",
            "invoice_number": "",
            "customer_reference": "FleetRent",
        }
    )
    for key, value in fields.items():
        ET.SubElement(call, f"{{{NAMESPACE}}}{key}").text = value
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def fetch_sales(sid, cfg, query):
    request = urllib.request.Request(
        ENDPOINT,
        data=request_body(sid, cfg, query),
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{NAMESPACE}/{METHOD}"',
        },
        method="POST",
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=25) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError("Response too large")
            return raw
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise HTTPException(502, "Shell bağlantısı tamamlanamadı. Sunucu erişimini kontrol edin.")


def plate(value):
    result = "".join(value.upper().split())
    if not result or len(result) > 20 or not result.isalnum():
        raise ValueError("Geçersiz Shell plakası.")
    return result


def number(value, positive=False):
    result = Decimal(value)
    if not result.is_finite() or result < 0 or result > Decimal("1000000000"):
        raise ValueError("Geçersiz Shell sayısal alanı.")
    if positive and result == 0:
        raise ValueError("Yakıt miktarı ve tutarı pozitif olmalı.")
    return float(result)


def parse_sales(raw):
    if (
        len(raw) > MAX_RESPONSE
        or b"\x00" in raw
        or b"<!DOCTYPE" in raw.upper()
        or b"<!ENTITY" in raw.upper()
    ):
        raise ValueError("Geçersiz Shell XML yanıtı.")
    root = ET.fromstring(raw)

    def name(e):
        return e.tag.split("}")[-1].lower()

    if any(name(e) == "fault" for e in root.iter()):
        raise ValueError("Shell servis hatası.")
    result = next((e for e in root.iter() if name(e) == f"{METHOD}Result".lower()), None)
    if result is None:
        raise ValueError("Shell sonuç alanı eksik.")
    success = next((e.text for e in result.iter() if name(e) == "success"), None)
    if (success or "").lower() not in {"true", "1"}:
        raise ValueError("Shell sorgusu başarısız.")
    count = next((e.text for e in result.iter() if name(e) == "countofsalestransactionlist"), None)
    sales = []
    for elem in result.iter():
        if name(elem) != "salestransactioninfo_with_rid":
            continue
        row = {name(c): (c.text or "").strip() for c in elem}
        rid = row["rid"]
        if not rid.isascii() or not rid.isdigit() or len(rid) > 100:
            raise ValueError("Shell RID eksik veya geçersiz.")
        value = row["transaction_date"]
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            moment = datetime.strptime(value, "%d.%m.%Y %H:%M:%S")
        moment = moment.replace(tzinfo=LOCAL) if moment.tzinfo is None else moment.astimezone(LOCAL)
        if moment.date() >= datetime.now(LOCAL).date():
            raise ValueError("Gün sonu onayı bekleyen kayıt.")
        km = number(row["vehicle_km"])
        if km > 10000000:
            raise ValueError("Geçersiz kilometre.")
        sales.append(
            {
                "rid": rid,
                "plate": plate(row["plate_cd"]),
                "occurred_at": moment.isoformat(),
                "liters": number(row["volume"], True),
                "amount": number(row["sales_total_amount"], True),
                "mileage": int(km),
                "fuel_type": row.get("fuel_name", ""),
                "station": row.get("retail_outlet_name", ""),
                "invoice_no": row.get("invoice_no", ""),
                "utts_id": row.get("utts_isutts", ""),
            }
        )
    if count is None or int(count) != len(sales):
        raise ValueError("Shell kayıt sayısı uyuşmuyor.")
    return sales


def process(db, ctx, event):
    data = event.payload
    mapping = (
        db.query(m.IntegrationMapping)
        .filter_by(supplier_id=ctx["id"], provider="shell", external_id=data["plate"])
        .first()
    )
    car = (
        db.query(m.Vehicle).filter_by(id=mapping.vehicle_id, supplier_id=ctx["id"]).first()
        if mapping
        else None
    )
    if not car:
        event.status, event.reason = (
            "Eşleştirme Bekliyor",
            "Shell plakasını bir filo aracıyla eşleyin.",
        )
        return
    if not car.is_active:
        event.status, event.reason = "İnceleme Bekliyor", "Araç pasif; yakıt gideri oluşturulmadı."
        return
    db.add(
        m.VehicleExpense(
            vehicle_id=car.id,
            kind="Yakıt",
            amount=data["amount"],
            date=datetime.fromisoformat(data["occurred_at"]).date().isoformat(),
            liters=data["liters"],
            mileage=data["mileage"],
            fuel_type=data["fuel_type"],
            station=data["station"],
            receipt_no=f'SHELL-{data["rid"]}',
            full_tank=False,
            note=f'Shell TTS · RID {data["rid"]} · Fatura {data["invoice_no"]}',
        )
    )
    event.vehicle_id, event.status, event.reason = car.id, "İşlendi", "Yakıt gideri oluşturuldu."
    event.processed_at = stamp()


def ingest(db, ctx, sales):
    counts = {"processed": 0, "duplicate": 0, "pending": 0}
    for data in sales:
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        existing = (
            db.query(m.IntegrationEvent)
            .filter_by(supplier_id=ctx["id"], provider="shell", external_id=data["rid"])
            .first()
        )
        if existing:
            if existing.payload_hash != digest:
                raise HTTPException(
                    409, "Aynı Shell RID farklı içerikle geldi. Kayıtları inceleyin."
                )
            counts["duplicate"] += 1
            continue
        event = m.IntegrationEvent(
            supplier_id=ctx["id"],
            provider="shell",
            external_id=data["rid"],
            payload=data,
            payload_hash=digest,
            occurred_at=data["occurred_at"],
            received_at=stamp(),
            status="Alındı",
        )
        db.add(event)
        process(db, ctx, event)
        db.flush()
        counts["processed" if event.status == "İşlendi" else "pending"] += 1
    return counts


@router.get("")
def overview(ctx=Depends(context), db: Session = Depends(get_db)):
    mappings = (
        db.query(m.IntegrationMapping).filter_by(supplier_id=ctx["id"], provider="shell").all()
    )
    events = (
        db.query(m.IntegrationEvent)
        .filter_by(supplier_id=ctx["id"], provider="shell")
        .order_by(m.IntegrationEvent.id.desc())
        .limit(100)
        .all()
    )
    return {
        "credentials_configured": all(credentials(ctx["id"]).values()),
        "config": config(db, ctx["id"]),
        "mappings": [{"external_id": r.external_id, "vehicle_id": r.vehicle_id} for r in mappings],
        "events": [
            {
                "id": r.id,
                "vehicle_id": r.vehicle_id,
                "status": r.status,
                "reason": r.reason,
                **r.payload,
            }
            for r in events
        ],
    }


@router.put("/config")
def save_config(data: ShellConfig, ctx=Depends(context), db: Session = Depends(get_db)):
    owner(ctx)
    row = db.query(m.SupplierSetting).filter_by(supplier_id=ctx["id"]).first()
    if not row:
        row = m.SupplierSetting(supplier_id=ctx["id"], value={})
        db.add(row)
    row.value = {**(row.value or {}), "shell": data.model_dump()}
    db.commit()
    return overview(ctx, db)


@router.put("/mappings")
def save_mapping(data: MappingInput, ctx=Depends(context), db: Session = Depends(get_db)):
    owner(ctx)
    vehicle(db, ctx, data.vehicle_id)
    try:
        external = plate(data.external_id)
    except ValueError:
        raise HTTPException(422, "Geçerli Shell plakası girin.")
    row = (
        db.query(m.IntegrationMapping)
        .filter_by(supplier_id=ctx["id"], provider="shell", external_id=external)
        .first()
    )
    if row and row.vehicle_id != data.vehicle_id:
        raise HTTPException(409, "Shell plakası başka araca bağlı; geçmiş eşleme değiştirilemez.")
    if not row:
        db.add(
            m.IntegrationMapping(
                supplier_id=ctx["id"],
                provider="shell",
                external_id=external,
                vehicle_id=data.vehicle_id,
                created_at=stamp(),
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Araç başka bir Shell plakasına bağlı.")
    return overview(ctx, db)


@router.post("/sync")
def sync(query: SalesQuery, ctx=Depends(context), db: Session = Depends(get_db)):
    owner(ctx)
    cfg = config(db, ctx["id"])
    if cfg is None:
        raise HTTPException(400, "Önce Shell bağlantı ayarlarını kaydedin.")
    raw = fetch_sales(ctx["id"], cfg, query)
    try:
        sales = parse_sales(raw)
        if any(
            not query.start_date
            <= datetime.fromisoformat(r["occurred_at"]).date()
            <= query.end_date
            for r in sales
        ):
            raise ValueError("Tarih aralığı dışında kayıt.")
    except (ValueError, KeyError, InvalidOperation, ET.ParseError):
        raise HTTPException(
            502, "Shell yanıtı doğrulanamadı. Servis yetkilerini ve sorguyu kontrol edin."
        )
    try:
        result = ingest(db, ctx, sales)
        db.commit()
        return result
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Eşzamanlı Shell işlemi algılandı. Tekrar deneyin.")
    except Exception:
        db.rollback()
        raise


@router.post("/events/{eid}/retry")
def retry(eid: int, ctx=Depends(context), db: Session = Depends(get_db)):
    owner(ctx)
    event = (
        db.query(m.IntegrationEvent)
        .filter_by(id=eid, supplier_id=ctx["id"], provider="shell")
        .with_for_update()
        .first()
    )
    if not event:
        raise HTTPException(404, "Shell kaydı bulunamadı.")
    if event.status == "İşlendi":
        raise HTTPException(409, "İşlenen kayıt tekrar uygulanamaz.")
    try:
        # SQLite ignores FOR UPDATE. A conditional write also serializes retries there.
        claimed = (
            db.query(m.IntegrationEvent)
            .filter_by(id=eid, supplier_id=ctx["id"], provider="shell")
            .filter(m.IntegrationEvent.status != "İşlendi")
            .update({"status": "İşleniyor"}, synchronize_session=False)
        )
        if claimed != 1:
            raise HTTPException(409, "Shell kaydı başka işlem tarafından işlendi.")
        db.refresh(event)
        process(db, ctx, event)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return overview(ctx, db)
