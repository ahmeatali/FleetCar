"""Tenant-scoped reports and real XLSX/PDF exports; missing tax data stays unknown."""

import os
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import models as m
from app.common.time import stamp
from app.database import get_db
from app.supplier_context import context
from app.supplier_operations import snapshot

router = APIRouter(prefix="/api/supplier-workspace/reports", tags=["Supplier reports"])
REPORTS = {
    "fleet": "Filo Envanteri",
    "occupancy": "Doluluk Durumu",
    "pool": "Havuz Araçlar",
    "usage": "Araç Kullanımı",
    "rented_vehicle": "Araç Bazlı Kiralama",
    "rented_customer": "Müşteri Bazlı Kiralama",
    "costs": "Maliyet Defteri",
    "profit_vehicle": "Araç Kârlılığı",
    "profit_customer": "Müşteri Kârlılığı",
    "service": "Servis ve Bakım",
    "tire": "Lastik",
    "damage": "Hasar",
    "hgs": "HGS",
    "fine": "Trafik Cezaları",
    "fuel": "Yakıt",
    "invoices": "Faturalar",
    "contract_expiry": "Sözleşme Bitişleri",
    "sales": "Araç Satışları",
}
LABELS = {
    "date": "Tarih",
    "number": "Kayıt No",
    "plate": "Plaka",
    "vehicle_name": "Araç",
    "customer_name": "Müşteri",
    "status": "Durum",
    "category": "Kategori",
    "amount": "Brüt Tutar (TL)",
    "net_amount": "Net Tutar (TL)",
    "tax_amount": "Vergi (TL)",
    "revenue": "Brüt Gelir (TL)",
    "cost": "Brüt Gider (TL)",
    "gross_margin": "Brüt Fark (TL)",
    "net_profit": "Net Kâr (TL)",
    "mileage": "Kilometre",
    "monthly_km": "Aylık Km",
    "end_date": "Bitiş",
    "note": "Açıklama",
    "count": "Araç Adedi",
}


def money(value):
    return round(float(value or 0), 2)


def financial_ledger(data):
    invoices = [
        r
        for r in data["records"]
        if r["kind"] == "invoice" and r["raw_status"] not in {"Taslak", "İptal"}
    ]
    replaced = {
        r["details"]["source_reference"]
        for r in invoices
        if r["details"].get("direction") == "gider" and r["details"].get("source_reference")
    }
    ledger = []

    def add(row, category, direction, key=None):
        if key in replaced or money(row["amount"]) <= 0:
            return
        details = row.get("details", {})
        gross = money(row["amount"])
        net = details.get("net_amount")
        known = net not in (None, "") and details.get("tax_rate") not in (None, "")
        net = money(net) if known else None
        allocations = details.get("vehicle_allocations") if row.get("kind") == "invoice" else None
        pieces = allocations or [{"vehicle_id": row.get("vehicle_id"), "amount": gross}]
        allocated_net = 0
        for index, part in enumerate(pieces):
            share = money(part["amount"])
            ratio = share / gross
            vid = part.get("vehicle_id")
            car = next((v for v in data["vehicles"] if v["id"] == vid), None)
            part_net = (
                (money(net - allocated_net) if index == len(pieces) - 1 else money(net * ratio))
                if known
                else None
            )
            if known:
                allocated_net = money(allocated_net + part_net)
            ledger.append(
                {
                    **row,
                    "vehicle_id": vid,
                    "plate": car["plate"] if car else "",
                    "amount": share,
                    "net_amount": part_net,
                    "tax_amount": money(share - part_net) if known else None,
                    "category": category,
                    "direction": direction,
                    "note": "Vergi ayrımı eksik" if not known else "",
                }
            )

    for row in data["fuel"]:
        add(row, row["details"].get("kind", "Yakıt"), "gider", row["id"])
    for row in data["hgs"]:
        if row["details"].get("type") == "Geçiş":
            add(row, "HGS", "gider", row["id"])
    for row in data["service"]:
        if row["status"] in {"Tamamlandı", "Teslimata Hazır"}:
            add(
                {**row, "date": row["details"].get("invoice_date") or row["date"]},
                {"lastik": "Lastik", "yol_yardim": "Yol Yardım"}.get(
                    row["details"].get("type"), "Servis"
                ),
                "gider",
                row["id"],
            )
    for row in data["records"]:
        if row["kind"] in {"policy", "damage", "fine"} and row["raw_status"] not in {
            "Taslak",
            "İptal",
            "Reddedildi",
        }:
            add(
                row,
                {"policy": "Sigorta", "damage": "Hasar", "fine": "TPC"}[row["kind"]],
                "gider",
                f'{row["kind"]}:{row["id"]}',
            )
    for row in invoices:
        add(
            row,
            "Gelir Faturası" if row["details"].get("direction") == "gelir" else "Gider Faturası",
            row["details"].get("direction"),
        )
    return ledger


def build_report(db, ctx, report, filters):
    if report not in REPORTS:
        raise HTTPException(404, "Rapor bulunamadı.")
    data = snapshot(ctx, db)
    cars = [
        v
        for v in data["vehicles"]
        if (not filters.get("vehicle") or v["id"] == filters["vehicle"])
        and all(
            not filters.get(key) or str(v.get(field, "")).casefold() == filters[key].casefold()
            for key, field in [("brand", "brand"), ("model", "model"), ("group", "vehicle_group")]
        )
    ]
    ids = {v["id"] for v in cars}

    def match(row, period=True):
        return (
            (
                not row.get("vehicle_id")
                and not any(filters.get(k) for k in ["vehicle", "brand", "model", "group"])
                or row.get("vehicle_id") in ids
            )
            and (not filters.get("customer") or row.get("customer_id") == filters["customer"])
            and (not filters.get("status") or row.get("status") == filters["status"])
            and (
                not filters.get("contract")
                or row.get("parent_id") == filters["contract"]
                or row.get("id") == filters["contract"]
                or row.get("details", {}).get("contract_id") == filters["contract"]
            )
            and (
                not period
                or (not filters.get("start") or str(row.get("date", ""))[:10] >= filters["start"])
                and (not filters.get("end") or str(row.get("date", ""))[:10] <= filters["end"])
            )
        )

    columns = [
        "date",
        "number",
        "plate",
        "customer_name",
        "status",
        "category",
        "amount",
        "net_amount",
        "tax_amount",
        "note",
    ]
    if report in {"fleet", "occupancy", "pool", "usage"}:
        rows = [
            {
                "date": v.get("delivery_date"),
                "vehicle_id": v["id"],
                "plate": v["plate"],
                "vehicle_name": f'{v.get("brand","")} {v.get("model","")}',
                "customer_id": v.get("customer_id"),
                "customer_name": v.get("customer_name"),
                "status": (
                    v.get("rental_status") or ("Kirada" if v.get("customer_id") else "Havuzda")
                    if v.get("status") == "Aktif"
                    else v.get("status")
                ),
                "mileage": v.get("mileage"),
                "monthly_km": v.get("current_month_km"),
                "end_date": v.get("contract_end_date"),
                "amount": v.get("monthly_rent") or 0,
            }
            for v in cars
        ]
        rows = [
            r for r in rows if match(r, False) and (report != "pool" or r["status"] == "Havuzda")
        ]
        columns = [
            "plate",
            "vehicle_name",
            "customer_name",
            "status",
            "mileage",
            "monthly_km",
            "end_date",
            "amount",
        ]
    elif report in {"rented_vehicle", "rented_customer"}:
        rows = [
            r
            for r in data["rentals"]
            if match(r, False)
            and (not filters.get("start") or r["end_date"] >= filters["start"])
            and (not filters.get("end") or r["date"] <= filters["end"])
        ]
        columns = ["number", "plate", "customer_name", "date", "end_date", "status", "amount"]
        if report == "rented_customer":
            grouped = {}
            for row in rows:
                target = grouped.setdefault(
                    row["customer_id"],
                    {"customer_name": row["customer_name"], "count": 0, "amount": 0},
                )
                target["count"] += 1
                target["amount"] = money(target["amount"] + row["amount"])
            rows = list(grouped.values())
            columns = ["customer_name", "count", "amount"]
    elif report in {"costs", "profit_vehicle", "profit_customer"}:
        ledger = [r for r in financial_ledger(data) if match(r)]
        rows = [r for r in ledger if r["direction"] == "gider"] if report == "costs" else []
        if report.startswith("profit_"):
            grouped = {}
            key = "vehicle_id" if report == "profit_vehicle" else "customer_id"
            for row in ledger:
                group = row.get(key)
                target = grouped.setdefault(
                    group,
                    {
                        "plate": row.get("plate") or "Genel Gider / Gelir",
                        "customer_name": row.get("customer_name") or "Genel",
                        "revenue": 0,
                        "cost": 0,
                        "gross_margin": 0,
                        "net_profit": 0,
                        "note": "",
                    },
                )
                income = row["direction"] == "gelir"
                target["revenue" if income else "cost"] = money(
                    target["revenue" if income else "cost"] + row["amount"]
                )
                target["gross_margin"] = money(target["revenue"] - target["cost"])
                if row["net_amount"] is None:
                    target["net_profit"] = None
                    target["note"] = "Vergi ayrımı eksik; brüt fark net kâr değildir."
                elif target["net_profit"] is not None:
                    target["net_profit"] = money(
                        target["net_profit"] + row["net_amount"] * (1 if income else -1)
                    )
            rows = list(grouped.values())
            columns = [
                "plate" if report == "profit_vehicle" else "customer_name",
                "revenue",
                "cost",
                "gross_margin",
                "net_profit",
                "note",
            ]
    elif report in {"service", "tire", "hgs", "fuel"}:
        rows = [r for r in data[report] if match(r)]
    else:
        kind = {
            "damage": "damage",
            "fine": "fine",
            "invoices": "invoice",
            "contract_expiry": "contract",
            "sales": "sale",
        }[report]
        rows = [
            r
            for r in data["records"]
            if r["kind"] == kind and match(r, report != "contract_expiry")
        ]
        if report == "contract_expiry":
            rows = [
                r
                for r in rows
                if (not filters.get("start") or (r["end_date"] or "") >= filters["start"])
                and (not filters.get("end") or (r["end_date"] or "") <= filters["end"])
            ]
            columns = ["number", "plate", "customer_name", "date", "end_date", "status", "amount"]
        if report == "invoices":
            for r in rows:
                r["net_amount"] = r["details"].get("net_amount") or None
                r["tax_amount"] = (
                    money(r["amount"] - float(r["net_amount"]))
                    if r["net_amount"] is not None
                    else None
                )
    return {
        "report": report,
        "title": REPORTS[report],
        "generated_at": stamp(),
        "filters": filters,
        "columns": columns,
        "labels": {key: LABELS.get(key, key) for key in columns},
        "rows": [{key: r.get(key) for key in columns} for r in rows],
        "note": "Genel giderler ayrı satırdır; eksik vergi bilgisi tahmin edilmez. Tarih filtresi envanterde anlık durumu, kiralamalarda çakışan dönemi, sözleşme bitişinde bitiş tarihini, diğer raporlarda kayıt tarihini seçer.",
    }


def xlsx_bytes(report):
    """Inline strings cannot become Excel formulas, even when starting with '='."""
    from xml.sax.saxutils import escape

    def column_name(index):
        result = ""
        while index:
            index, rem = divmod(index - 1, 26)
            result = chr(65 + rem) + result
        return result

    grid = [[report["labels"][key] for key in report["columns"]]] + [
        [r[key] for key in report["columns"]] for r in report["rows"]
    ]
    body = []
    for ri, row in enumerate(grid, 1):
        cells = []
        for ci, value in enumerate(row, 1):
            reference = f"{column_name(ci)}{ri}"
            if isinstance(value, (int, float)):
                cells.append(f'<c r="{reference}"><v>{value}</v></c>')
            else:
                text = str(value if value is not None else "")
                text = "".join(
                    c
                    for c in text
                    if c in "\t\n\r"
                    or 32 <= ord(c) <= 0xD7FF
                    or 0xE000 <= ord(c) <= 0xFFFD
                    or 0x10000 <= ord(c) <= 0x10FFFF
                )
                cells.append(
                    f'<c r="{reference}" t="inlineStr"><is><t xml:space="preserve">{escape(text)}</t></is></c>'
                )
        body.append(f'<row r="{ri}">' + "".join(cells) + "</row>")
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        )
        archive.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="FleetRent" sheetId="1" r:id="rId1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" state="frozen"/></sheetView></sheetViews><sheetData>'
            + "".join(body)
            + "</sheetData></worksheet>",
        )
    return stream.getvalue()


def pdf_bytes(report):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle
    except ImportError:
        raise HTTPException(
            503, "PDF bağımlılığı eksik. Backend requirements paketlerini yükleyin."
        )
    font_candidates = [
        os.environ.get("FLEETCAR_REPORT_FONT", ""),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    font = next((p for p in font_candidates if p and Path(p).is_file()), None)
    if not font:
        raise HTTPException(
            503, "Türkçe PDF yazı tipi bulunamadı. FLEETCAR_REPORT_FONT ile Unicode TTF tanımlayın."
        )
    if "FleetRentReport" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("FleetRentReport", font))
    stream = BytesIO()
    width, height = landscape(A4)
    document = SimpleDocTemplate(
        stream,
        pagesize=(width, height),
        leftMargin=30,
        rightMargin=30,
        topMargin=32,
        bottomMargin=38,
        title=report["title"],
        author="FleetRent",
    )
    cell = ParagraphStyle(
        "cell",
        fontName="FleetRentReport",
        fontSize=7,
        leading=10,
        textColor=colors.HexColor("#19365d"),
    )
    title = ParagraphStyle("title", parent=cell, fontSize=17, leading=22, spaceAfter=10)

    def text(value):
        value = str(value if value is not None else "-")
        value = "".join(
            c
            for c in value
            if c in "\t\n\r"
            or 32 <= ord(c) <= 0xD7FF
            or 0xE000 <= ord(c) <= 0xFFFD
            or 0x10000 <= ord(c) <= 0x10FFFF
        )
        return escape(value).replace("\n", "<br/>")

    grid = [[Paragraph(text(report["labels"][key]), cell) for key in report["columns"]]]
    grid.extend(
        [[Paragraph(text(row[key]), cell) for key in report["columns"]] for row in report["rows"]]
    )
    if len(grid) == 1:
        grid.append(
            [
                Paragraph("Kayıt yok" if index == 0 else "", cell)
                for index in range(len(report["columns"]))
            ]
        )
    table = LongTable(
        grid,
        colWidths=[(width - 60) / len(report["columns"])] * len(report["columns"]),
        repeatRows=1,
        hAlign="LEFT",
        splitInRow=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf1ff")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7faff")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#a9c6fb")),
            ]
        )
    )

    def footer(canvas, doc):
        canvas.setFont("FleetRentReport", 8)
        canvas.setFillColor(colors.HexColor("#667b99"))
        canvas.drawString(30, 20, "FleetRent | " + report["generated_at"][:10])
        canvas.drawRightString(width - 30, 20, f"Sayfa {doc.page}")

    document.build(
        [
            Paragraph("FLEETRENT / " + text(report["title"]), title),
            Paragraph(text(report["note"]), cell),
            Spacer(1, 12),
            table,
        ],
        onFirstPage=footer,
        onLaterPages=footer,
    )
    return stream.getvalue()


@router.get("/catalog")
def catalog(ctx=Depends(context)):
    return [{"key": key, "label": value} for key, value in REPORTS.items()]


@router.get("/{report}")
def report_endpoint(
    report: str,
    format: str = Query("json", pattern="^(json|xlsx|pdf)$"),
    start: date = None,
    end: date = None,
    customer: int = None,
    vehicle: str = None,
    brand: str = None,
    model: str = None,
    group: str = None,
    contract: int = None,
    status: str = None,
    ctx=Depends(context),
    db: Session = Depends(get_db),
):
    if start and end and start > end:
        raise HTTPException(400, "Başlangıç bitişten sonra olamaz.")
    from app.supplier_permissions import EXPORT_ROLES

    if format != "json" and ctx["role"] not in EXPORT_ROLES:
        raise HTTPException(403, "Rapor dışa aktarma yetkiniz yok.")
    result = build_report(
        db,
        ctx,
        report,
        {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
            "customer": customer,
            "vehicle": vehicle,
            "brand": brand,
            "model": model,
            "group": group,
            "contract": contract,
            "status": status,
        },
    )
    db.add(
        m.AccessAudit(
            principal_kind="supplier",
            subject_id=ctx["id"],
            method="EXPORT" if format != "json" else "REPORT",
            resource=f"{report}:{format}",
            created_at=stamp(),
        )
    )
    db.commit()
    if format == "json":
        return result
    content = xlsx_bytes(result) if format == "xlsx" else pdf_bytes(result)
    return Response(
        content,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if format == "xlsx"
            else "application/pdf"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="fleetrent-{report}.{format}"',
            "Cache-Control": "private, no-store",
        },
    )
