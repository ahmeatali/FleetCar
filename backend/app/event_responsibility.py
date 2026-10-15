"""Resolve costs against assignment history, never whichever customer owns the plate today."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app import models as m
from app.common.time import business_today, interval_contains, stamp
from app.database import get_db
from app.supplier_context import context, customer_ids, operation, vehicle
from app.supplier_schemas import OperationInput
from app.supplier_service import append_record, audit, serialize

router = APIRouter(prefix="/api/supplier-workspace/responsibility")


def resolve(db, sid, vid, when, kind=None, source_id=None):
    override = (
        db.query(m.EventResponsibility)
        .filter_by(supplier_id=sid, source_kind=kind, source_id=source_id)
        .first()
        if kind and source_id
        else None
    )
    if override:
        return {
            "customer_id": override.customer_id,
            "rental_id": None,
            "driver_name": None,
            "responsibility_status": "Manuel Onaylandı",
            "reason": override.reason,
        }
    if kind == "fine" and source_id:
        fine = (
            db.query(m.SupplierOperation)
            .filter_by(id=source_id, supplier_id=sid, kind="fine")
            .first()
        )
        if (
            fine
            and fine.customer_id
            and fine.details.get("responsibility_status") not in {"Belirsiz", "Eşleştirme Bekliyor"}
        ):
            return {
                "customer_id": fine.customer_id,
                "rental_id": fine.details.get("rental_id"),
                "driver_name": fine.details.get("driver"),
                "responsibility_status": fine.details.get("responsibility_status")
                or "Manuel Seçildi",
                "reason": "Ceza kaydı sorumluluğu.",
            }
    assignments = db.query(m.VehicleAssignment).filter_by(supplier_id=sid, vehicle_id=vid).all()
    moment = str(when or "")
    matches = []
    for assignment in assignments:
        rental = db.get(m.Rental, assignment.rental_id) if assignment.rental_id else None
        if rental and not rental.delivered_at:
            continue
        start = (
            max(assignment.starts_at, rental.delivered_at)
            if rental and rental.delivered_at
            else assignment.starts_at
        )
        hit = interval_contains(start, assignment.ends_at, moment)
        if hit:
            matches.append(assignment)
    if len(matches) == 1:
        row = matches[0]
        return {
            "customer_id": row.customer_id,
            "rental_id": row.rental_id,
            "driver_name": row.driver_name,
            "responsibility_status": "Eşleşti",
            "reason": "Olay tarihindeki tahsis kaydı.",
        }
    if len(matches) > 1:
        return {
            "customer_id": None,
            "rental_id": None,
            "driver_name": None,
            "responsibility_status": "Belirsiz",
            "reason": "Olay anında birden fazla tahsis var veya yalnız tarih verilmiş. İnceleme gerekli.",
        }
    # Unmigrated manual stock carries no reliable historical assignment interval.
    return {
        "customer_id": None,
        "rental_id": None,
        "driver_name": None,
        "responsibility_status": "Eşleştirme Bekliyor",
        "reason": "Olay tarihini kapsayan tahsis yok.",
    }


def source(db, ctx, kind, rid):
    if kind not in {"fuel", "hgs", "fine"}:
        raise HTTPException(400, "Eşleme kaynağı geçersiz.")
    row = (
        operation(db, ctx, rid)
        if kind == "fine"
        else db.get({"fuel": m.VehicleExpense, "hgs": m.HgsTransaction}[kind], rid)
    )
    if not row or kind == "fine" and row.kind != "fine":
        raise HTTPException(404, "Kaynak bulunamadı.")
    car = vehicle(db, ctx, row.vehicle_id)
    return row, car


class ResponsibilityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: Optional[int] = Field(None, gt=0)
    reason: str = Field(min_length=10, max_length=2000)


@router.put("/{kind}/{rid}")
def assign(
    kind: str,
    rid: int,
    data: ResponsibilityInput,
    ctx=Depends(context),
    db: Session = Depends(get_db),
):
    if ctx["role"] not in {"owner", "finance", "fleet_manager"}:
        raise HTTPException(403, "Mali eşleştirme yetkisi gerekli.")
    row, car = source(db, ctx, kind, rid)
    if data.customer_id and data.customer_id not in customer_ids(db, ctx["id"]):
        raise HTTPException(404, "Müşteri bulunamadı.")
    reference = f"{kind}:{rid}"
    if any(
        r.details.get("source_reference") == reference
        or r.details.get("reflection_reference") == reference
        for r in db.query(m.SupplierOperation)
        .filter_by(supplier_id=ctx["id"], kind="invoice")
        .filter(m.SupplierOperation.status.notin_(["Taslak", "İptal"]))
        .all()
    ):
        raise HTTPException(
            409,
            "Faturalanmış mali olay yeni düzeltme kaydıyla düzeltilir; eşleşmesi değiştirilemez.",
        )
    match = (
        db.query(m.EventResponsibility)
        .filter_by(supplier_id=ctx["id"], source_kind=kind, source_id=rid)
        .first()
    )
    if not match:
        match = m.EventResponsibility(
            supplier_id=ctx["id"], source_kind=kind, source_id=rid, vehicle_id=car.id
        )
        db.add(match)
    match.customer_id = data.customer_id
    match.reason = data.reason.strip()
    match.actor = ctx["actor"]
    match.updated_at = stamp()
    if kind == "fine":
        row.customer_id = data.customer_id
        row.version += 1
        row.updated_at = stamp()
        row.details = {
            **row.details,
            "responsibility_status": "Manuel Onaylandı",
            "responsibility_reason": data.reason.strip(),
        }
        audit(
            db,
            ctx,
            row,
            "Ceza sorumluluğu mali incelemeyle belirlendi",
            {"customer_id": data.customer_id, "reason": data.reason.strip()},
        )
    db.commit()
    return {"ok": True}


@router.post("/{kind}/{rid}/reflect")
def reflect(kind: str, rid: int, ctx=Depends(context), db: Session = Depends(get_db)):
    if ctx["role"] not in {"owner", "finance"}:
        raise HTTPException(403, "Müşteriye yansıtma finans yetkisi gerektirir.")
    row, car = source(db, ctx, kind, rid)
    if kind == "hgs" and row.type != "Geçiş":
        raise HTTPException(400, "HGS yüklemesi müşteriye geçiş gideri olarak yansıtılamaz.")
    if kind == "fine" and row.status in {"İptal", "İtiraz Edildi"}:
        raise HTTPException(400, "İptal veya itiraz sürecindeki ceza yansıtılamaz.")
    match = resolve(
        db,
        ctx["id"],
        car.id,
        (
            (row.details or {}).get("occurred_at")
            if kind == "fine" and row.details.get("occurred_at")
            else row.date
        ),
        kind,
        rid,
    )
    cid = match["customer_id"]
    if not cid:
        raise HTTPException(400, "Müşteri sorumluluğunu mali eşleştirme kuyruğundan doğrulayın.")
    reference = f"{kind}:{rid}"
    previous = [
        r
        for r in db.query(m.SupplierOperation)
        .filter_by(supplier_id=ctx["id"], kind="invoice")
        .all()
        if r.details.get("reflection_reference") == reference
    ]
    if any(r.status != "İptal" for r in previous):
        raise HTTPException(409, "Bu olay için yansıtma faturası zaten var.")
    payload = OperationInput(
        title=f"{car.plate} / {kind.upper()} Gider Yansıtması",
        customer_id=cid,
        vehicle_id=car.id,
        date=business_today(),
        amount=row.amount,
        details={
            "direction": "gelir",
            "invoice_no": f"YNS-{kind.upper()}-{rid:08d}-{len(previous)+1}",
            "reflection_reference": reference,
            "responsibility_status": match["responsibility_status"],
            "rental_id": match["rental_id"],
            "source_date": row.date,
        },
    )
    invoice = append_record(db, ctx, "invoice", payload)
    db.commit()
    return serialize(db, invoice)
