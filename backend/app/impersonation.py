"""Support impersonation: an admin opens a company's own portal to help them.

A native portal session (SupplierSession / customer PortalSession) is minted for the target
company and marked with the acting admin's id. The company's users see nothing and no new user
appears in their team; every access is written to impersonation_events as an internal trail.
Impersonation sessions are short-lived (IMPERSONATION_TTL) instead of the normal 7 days.
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models as m
from app.common.security import token_digest
from app.common.time import stamp
from app.database import get_db

router = APIRouter(prefix="/api/admin", tags=["impersonation"])

IMPERSONATION_TTL = timedelta(hours=2)
PORTALS = {"supplier", "customer"}
PORTAL_PATH = {"supplier": "/supplier-portal", "customer": "/dashboard"}
STORAGE_KEY = {"supplier": "fleetcar_supplier_token", "customer": "fleetcar_token"}


def _require_admin(request: Request, db: Session):
    from app.portal_access import principal

    p = principal(request, db)
    if p.get("kind") != "admin":
        raise HTTPException(403, "Bu işlem için yönetici oturumu gerekli.")
    admin = db.get(m.AdminUser, p["id"])
    if not admin:
        raise HTTPException(401, "Yönetici hesabı bulunamadı.")
    return admin


def _mint(db, model, **identity):
    """Like issue_session but short-lived, for a support session."""
    token = secrets.token_urlsafe(48)
    expires = (datetime.now(timezone.utc) + IMPERSONATION_TTL).isoformat()
    row = model(**identity, token_hash=token_digest(token), expires_at=expires)
    db.add(row)
    db.flush()
    return token, row


def _resolve_target(db, portal, subject_id, user_id):
    if portal == "supplier":
        supplier = db.get(m.Supplier, subject_id)
        if not supplier:
            raise HTTPException(404, "Tedarikçi bulunamadı.")
        if user_id is not None:
            user = db.get(m.SupplierPortalUser, user_id)
            if not user or user.supplier_id != supplier.id:
                raise HTTPException(404, "Tedarikçi kullanıcısı bulunamadı.")
        return supplier.name
    customer = db.get(m.Customer, subject_id)
    if not customer:
        raise HTTPException(404, "Müşteri bulunamadı.")
    if user_id is not None:
        user = db.get(m.CustomerPortalUser, user_id)
        if not user or user.customer_id != customer.id:
            raise HTTPException(404, "Müşteri kullanıcısı bulunamadı.")
    return customer.company_name


@router.post("/impersonate")
async def impersonate(request: Request, db: Session = Depends(get_db)):
    admin = _require_admin(request, db)
    body = await request.json()
    portal = str(body.get("portal", "")).strip()
    subject_id = body.get("subject_id")
    user_id = body.get("user_id")
    if portal not in PORTALS or not isinstance(subject_id, int):
        raise HTTPException(422, "Geçersiz hesap bilgisi.")
    if user_id is not None and not isinstance(user_id, int):
        raise HTTPException(422, "Geçersiz kullanıcı bilgisi.")

    subject_name = _resolve_target(db, portal, subject_id, user_id)
    if portal == "supplier":
        token, session = _mint(
            db,
            m.SupplierSession,
            supplier_id=subject_id,
            user_id=user_id,
            impersonated_by=admin.id,
        )
    else:
        token, session = _mint(
            db,
            m.PortalSession,
            kind="customer",
            subject_id=subject_id,
            user_id=user_id,
            impersonated_by=admin.id,
        )
    event = m.ImpersonationEvent(
        admin_id=admin.id,
        admin_email=admin.email,
        portal=portal,
        subject_id=subject_id,
        subject_name=subject_name,
        user_id=user_id,
        session_id=session.id,
        started_at=stamp(),
    )
    db.add(event)
    db.commit()
    return {
        "token": token,
        "portal": portal,
        "storage_key": STORAGE_KEY[portal],
        "open_path": PORTAL_PATH[portal],
        "subject_id": subject_id,
        "subject_name": subject_name,
        "event_id": event.id,
    }


@router.post("/impersonate/stop")
async def impersonate_stop(request: Request, db: Session = Depends(get_db)):
    _require_admin(request, db)
    body = await request.json()
    event_id = body.get("event_id")
    event = db.get(m.ImpersonationEvent, event_id) if isinstance(event_id, int) else None
    if not event:
        raise HTTPException(404, "Destek oturumu bulunamadı.")
    model = m.SupplierSession if event.portal == "supplier" else m.PortalSession
    session = db.get(model, event.session_id) if event.session_id else None
    if session is not None:
        db.delete(session)
    if not event.ended_at:
        event.ended_at = stamp()
    db.commit()
    return {"stopped": True}


@router.get("/impersonation-log")
def impersonation_log(request: Request, db: Session = Depends(get_db)):
    _require_admin(request, db)
    rows = (
        db.query(m.ImpersonationEvent)
        .order_by(m.ImpersonationEvent.id.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": r.id,
            "admin_email": r.admin_email,
            "portal": r.portal,
            "subject_id": r.subject_id,
            "subject_name": r.subject_name,
            "user_id": r.user_id,
            "started_at": r.started_at,
            "ended_at": r.ended_at,
            "active": r.ended_at is None,
        }
        for r in rows
    ]
