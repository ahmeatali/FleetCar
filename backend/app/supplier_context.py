"""Supplier authentication and tenant-scoped lookups, independent of workflow routes."""

from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app import models as m
from app.common.security import issue_session, session_expired, token_digest
from app.database import get_db
from app.supplier_permissions import ROLES

SERVICE_TYPES = {"servis", "oto_servis", "lastik", "yol_yardim"}


def session_token(db, supplier_id, user_id=None):
    return issue_session(db, m.SupplierSession, supplier_id=supplier_id, user_id=user_id)


def context(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    request: Request = None,
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Oturum bulunamadı. Tedarikçi hesabınızla tekrar giriş yapın.")
    session = (
        db.query(m.SupplierSession).filter_by(token_hash=token_digest(authorization[7:])).first()
    )
    if not session or session_expired(session.expires_at):
        raise HTTPException(401, "Oturum süresi doldu. Tekrar giriş yapın.")
    supplier = db.get(m.Supplier, session.supplier_id)
    if not supplier or supplier.type in SERVICE_TYPES:
        raise HTTPException(403, "Kiralama tedarikçisi hesabı gerekli.")
    user = db.get(m.SupplierPortalUser, session.user_id) if session.user_id else None
    if session.user_id and (not user or not user.is_active or user.supplier_id != supplier.id):
        raise HTTPException(403, "Kullanıcı hesabı pasif.")
    role = user.role if user else "owner"
    if request is not None:
        request.state.audit_principal = {
            "kind": "supplier",
            "id": supplier.id,
            "role": role,
            "user_id": session.user_id,
        }
    if role not in ROLES:
        raise HTTPException(403, "Kullanıcı rolü geçersiz.")
    return {
        "supplier": supplier,
        "id": supplier.id,
        "role": role,
        "actor": user.name if user else supplier.name,
        "session": session,
    }


def vehicle(db, ctx, vid):
    row = db.query(m.Vehicle).filter_by(id=vid, supplier_id=ctx["id"]).first()
    if not row:
        raise HTTPException(404, "Tedarikçiye ait araç bulunamadı.")
    return row


def operation(db, ctx, rid):
    row = db.query(m.SupplierOperation).filter_by(id=rid, supplier_id=ctx["id"]).first()
    if not row:
        raise HTTPException(404, "İşlem bulunamadı.")
    return row


def customer_ids(db, sid):
    return (
        {
            r[0]
            for r in db.query(m.SupplierCustomerLink.customer_id).filter_by(supplier_id=sid).all()
        }
        | {
            r[0]
            for r in db.query(m.Vehicle.customer_id)
            .filter(m.Vehicle.supplier_id == sid, m.Vehicle.customer_id.isnot(None))
            .all()
        }
        | {
            r[0]
            for r in db.query(m.SupplierOperation.customer_id)
            .filter(
                m.SupplierOperation.supplier_id == sid, m.SupplierOperation.customer_id.isnot(None)
            )
            .all()
        }
    )
