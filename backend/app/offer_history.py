"""Immutable commercial snapshots and decisions made by authenticated customers."""

import hashlib
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as m
from app.common.time import business_today, stamp
from app.database import get_db
from app.portal_access import access_audit, principal
from app.supplier_context import context, operation
from app.supplier_service import audit, serialize

supplier_router = APIRouter(prefix="/api/supplier-workspace")
customer_router = APIRouter(prefix="/api/customer-workspace")


def capture(db, row):
    if row.kind != "offer":
        return
    snapshot = {
        key: getattr(row, key)
        for key in [
            "title",
            "customer_id",
            "vehicle_id",
            "date",
            "end_date",
            "amount",
            "status",
            "details",
        ]
    }
    # Copy JSON structures so future ORM changes cannot mutate an already captured version.
    snapshot = json.loads(json.dumps(snapshot, ensure_ascii=False))
    digest = hashlib.sha256(
        json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    db.add(
        m.OfferVersion(
            offer_id=row.id,
            supplier_id=row.supplier_id,
            version=row.version,
            snapshot=snapshot,
            content_hash=digest,
            created_at=stamp(),
        )
    )


def versions(db, row):
    return [
        {
            "version": v.version,
            "snapshot": v.snapshot,
            "content_hash": v.content_hash,
            "created_at": v.created_at,
        }
        for v in db.query(m.OfferVersion)
        .filter_by(offer_id=row.id)
        .order_by(m.OfferVersion.version)
        .all()
    ]


@supplier_router.get("/records/{rid}/versions")
def supplier_versions(rid: int, ctx=Depends(context), db: Session = Depends(get_db)):
    row = operation(db, ctx, rid)
    if row.kind != "offer":
        raise HTTPException(400, "Teklif kaydı gerekli.")
    return versions(db, row)


def customer_context(request: Request, db: Session = Depends(get_db)):
    p = principal(request, db)
    if p["kind"] != "customer" or p["role"] == "Sürücü":
        raise HTTPException(403, "Müşteri ticari hesabı gerekli.")
    access_audit(db, p, request)
    return p


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(gt=0)
    decision: Literal["accept", "revise", "reject"]
    note: str = Field("", max_length=3000)


@customer_router.get("/offers")
def customer_offers(p=Depends(customer_context), db: Session = Depends(get_db)):
    rows = (
        db.query(m.SupplierOperation)
        .filter_by(kind="offer", customer_id=p["id"])
        .filter(m.SupplierOperation.status != "Taslak")
        .order_by(m.SupplierOperation.id.desc())
        .all()
    )
    return [
        {**serialize(db, r), "supplier_name": db.get(m.Supplier, r.supplier_id).name} for r in rows
    ]


@customer_router.get("/offers/{rid}/versions")
def customer_versions(rid: int, p=Depends(customer_context), db: Session = Depends(get_db)):
    row = db.query(m.SupplierOperation).filter_by(id=rid, kind="offer", customer_id=p["id"]).first()
    if not row or row.status == "Taslak":
        raise HTTPException(404, "Teklif bulunamadı.")
    # Customer history includes only versions that were actually submitted.
    return [v for v in versions(db, row) if v["snapshot"]["status"] != "Taslak"]


@customer_router.post("/offers/{rid}/decision")
def decide(
    rid: int, data: DecisionInput, p=Depends(customer_context), db: Session = Depends(get_db)
):
    if p["role"] not in {"owner", "Yönetici", "Filo Yöneticisi", "Genel Müdür"}:
        raise HTTPException(403, "Teklif kararı için yönetici yetkisi gerekli.")
    row = db.query(m.SupplierOperation).filter_by(id=rid, kind="offer", customer_id=p["id"]).first()
    if not row:
        raise HTTPException(404, "Teklif bulunamadı.")
    if row.version != data.version or row.status != "Beklemede":
        raise HTTPException(409, "Teklif güncellendi veya karar verildi. Yenileyin.")
    if row.end_date and row.end_date < business_today().isoformat():
        raise HTTPException(400, "Süresi dolmuş teklif için karar verilemez.")
    if data.decision == "revise" and not data.note.strip():
        raise HTTPException(400, "Revizyon talebini açıklayın.")
    customer = db.get(m.Customer, p["id"])
    target = {"accept": "Onaylandı", "revise": "Revizyon Bekliyor", "reject": "Reddedildi"}[
        data.decision
    ]
    try:
        # Preserve existing pre-versioning records before the first new decision.
        if not db.query(m.OfferVersion).filter_by(offer_id=row.id, version=row.version).first():
            capture(db, row)
            db.flush()
        changed = (
            db.query(m.SupplierOperation)
            .filter_by(id=row.id, version=data.version, status="Beklemede")
            .update(
                {"status": target, "version": data.version + 1, "updated_at": stamp()},
                synchronize_session=False,
            )
        )
        if changed != 1:
            raise HTTPException(409, "Teklif değişti. Yenileyin.")
        db.add(
            m.CustomerOfferDecision(
                offer_id=row.id,
                offer_version=data.version,
                customer_id=p["id"],
                decision=data.decision,
                note=data.note.strip(),
                actor=customer.company_name,
                created_at=stamp(),
            )
        )
        db.refresh(row)
        row.details = {
            **row.details,
            "customer_decision": data.decision,
            "customer_decision_note": data.note.strip(),
            "customer_decision_version": data.version,
            "customer_decision_at": stamp(),
            "acceptance_source": "customer_portal",
        }
        capture(db, row)
        from app.marketplace_bridge import sync_decision

        sync_decision(db, row, data.decision)
        audit(
            db,
            {"id": row.supplier_id, "actor": customer.company_name},
            row,
            "Müşteri kararı: " + target,
            {"version": data.version, "note": data.note.strip()},
        )
        db.commit()
        return serialize(db, row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu teklif sürümü için karar zaten kaydedildi.")
    except Exception:
        db.rollback()
        raise


@customer_router.get("/rental-suppliers")
def rental_supplier_directory(p=Depends(customer_context), db: Session = Depends(get_db)):
    from app.portal_access import SERVICE_TYPES

    return [
        {"id": s.id, "name": s.name}
        for s in db.query(m.Supplier)
        .filter(m.Supplier.type.notin_(SERVICE_TYPES))
        .order_by(m.Supplier.name)
        .all()
    ]


@customer_router.post("/suppliers/{sid}/authorize")
def authorize_supplier(sid: int, p=Depends(customer_context), db: Session = Depends(get_db)):
    from app.portal_access import SERVICE_TYPES
    from app.supplier_service import link_customer

    if p["role"] != "owner":
        raise HTTPException(403, "Firma sahibi yetkisi gerekli.")
    supplier = db.get(m.Supplier, sid)
    if not supplier or supplier.type in SERVICE_TYPES:
        raise HTTPException(404, "Kiralama tedarikçisi bulunamadı.")
    link_customer(db, sid, p["id"], {"authorized_by_customer": True, "authorized_at": stamp()})
    db.commit()
    return {"ok": True}
