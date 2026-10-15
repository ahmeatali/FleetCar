"""Shared, tenant-scoped team administration and single-use email invitations."""

import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as m
from app.auth import hash_password
from app.common.security import session_expired, token_digest
from app.common.time import stamp
from app.database import get_db
from app.portal_access import principal
from app.supplier_permissions import ROLES
from app.team_permissions import (
    ACTIONS,
    CUSTOMER_ROLES,
    MODULES,
    base_permissions,
    validate_permissions,
)

router = APIRouter(prefix="/api/team", tags=["Team"])


def identity(request, db, portal, owner=True):
    if portal not in {"customer", "supplier"}:
        raise HTTPException(404, "Portal bulunamadı.")
    ctx = principal(request, db)
    if ctx["kind"] != portal:
        raise HTTPException(403, "Bu portal için oturum gerekli.")
    if owner and (ctx.get("user_id") or ctx["role"] != "owner"):
        raise HTTPException(403, "Kullanıcı ve rol yönetimi şirket hesabı sahibine aittir.")
    return ctx


def model(portal):
    return m.CustomerPortalUser if portal == "customer" else m.SupplierPortalUser


def scope(db, cls, portal, tenant):
    return db.query(cls).filter_by(portal=portal, tenant_id=tenant)


def members(db, portal, tenant):
    return db.query(model(portal)).filter_by(**{portal + "_id": tenant})


def find_user(db, ctx, uid):
    user = members(db, ctx["kind"], ctx["id"]).filter_by(id=uid).first()
    if not user:
        raise HTTPException(404, "Kullanıcı bulunamadı.")
    return user


def access_row(db, portal, tenant, user):
    return scope(db, m.TeamMemberAccess, portal, tenant).filter_by(user_id=user.id).first()


def role_value(db, ctx, key):
    portal = ctx["kind"]
    builtins = CUSTOMER_ROLES if portal == "customer" else ROLES - {"owner"}
    if key in builtins:
        return key, None, base_permissions(portal, key)
    try:
        rid = int(str(key).removeprefix("custom:"))
    except ValueError:
        raise HTTPException(422, "Geçerli bir rol seçin.")
    role = scope(db, m.TeamRole, portal, ctx["id"]).filter_by(id=rid).first()
    if not role:
        raise HTTPException(404, "Rol bulunamadı.")
    return role.base_role, role.id, role.permissions


def log(db, ctx, action, target):
    owner = db.get(m.Customer if ctx["kind"] == "customer" else m.Supplier, ctx["id"])
    db.add(
        m.TeamActivity(
            portal=ctx["kind"],
            tenant_id=ctx["id"],
            actor=owner.company_name if ctx["kind"] == "customer" else owner.name,
            action=action,
            target=target,
            created_at=stamp(),
        )
    )


def revoke_sessions(db, portal, tenant, uid):
    if portal == "supplier":
        db.query(m.SupplierSession).filter_by(supplier_id=tenant, user_id=uid).delete()
    else:
        db.query(m.PortalSession).filter_by(
            kind="customer", subject_id=tenant, user_id=uid
        ).delete()


def serialize(db, portal, tenant, user):
    access = access_row(db, portal, tenant, user)
    role = db.get(m.TeamRole, access.role_id) if access and access.role_id else None
    invite = (
        scope(db, m.TeamInvitation, portal, tenant)
        .filter_by(user_id=user.id)
        .order_by(m.TeamInvitation.id.desc())
        .first()
    )
    pending = bool(access and access.pending)
    status = (
        "Pasif"
        if not user.is_active
        else (
            (
                "Davet Süresi Doldu"
                if invite and session_expired(invite.expires_at)
                else "Davet Bekliyor"
            )
            if pending and invite and not invite.revoked_at
            else "Davet Edilmedi" if pending else "Aktif"
        )
    )
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": getattr(user, "phone", "") or "",
        "assigned_plate": getattr(user, "assigned_plate", "") or "",
        "role": "custom:" + str(role.id) if role else user.role,
        "base_role": user.role,
        "role_name": role.name if role else user.role,
        "is_active": user.is_active,
        "status": status,
        "department": access.department if access else "",
        "version": access.version if access else 0,
        "custom_permissions": bool(access and access.permissions is not None and access.role_id),
        "permissions": (
            access.permissions
            if access and access.permissions is not None
            else role.permissions if role else base_permissions(portal, user.role)
        ),
        "created_at": user.created_at,
    }


class MemberInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=200)
    role: str
    department: str = Field("", max_length=100)
    phone: str = Field("", max_length=40)
    assigned_plate: str = Field("", max_length=30)
    is_active: bool = True
    permissions: dict | None = None
    invite: bool = False
    version: int = 0


class RoleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    description: str = Field("", max_length=300)
    base_role: str
    permissions: dict
    version: int = 0


class AcceptInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=10, max_length=200)


@router.get("/{portal}/session")
def team_session(portal: str, request: Request, db: Session = Depends(get_db)):
    from app.team_permissions import policy

    ctx = identity(request, db, portal, owner=False)
    return {
        "can_manage": not ctx.get("user_id"),
        "permissions": policy(db, portal, ctx["id"], ctx.get("user_id")),
    }


@router.get("/{portal}/overview")
def overview(portal: str, request: Request, db: Session = Depends(get_db)):
    ctx = identity(request, db, portal)
    roles = [
        {
            "key": name,
            "name": name,
            "base_role": name,
            "permissions": base_permissions(portal, name),
            "system": True,
            "version": 0,
            "description": "Sistem rolü",
        }
        for name in sorted(CUSTOMER_ROLES if portal == "customer" else ROLES - {"owner"})
    ]
    roles += [
        {
            "key": "custom:" + str(r.id),
            "name": r.name,
            "description": r.description,
            "base_role": r.base_role,
            "permissions": r.permissions,
            "version": r.version,
            "system": False,
        }
        for r in scope(db, m.TeamRole, portal, ctx["id"]).order_by(m.TeamRole.id).all()
    ]
    users = [
        serialize(db, portal, ctx["id"], u)
        for u in members(db, portal, ctx["id"]).order_by(model(portal).id.desc()).all()
    ]
    return {
        "users": users,
        "roles": roles,
        "modules": MODULES,
        "actions": ACTIONS,
        "activities": [
            {
                "id": e.id,
                "actor": e.actor,
                "action": e.action,
                "target": e.target,
                "created_at": e.created_at,
            }
            for e in scope(db, m.TeamActivity, portal, ctx["id"])
            .order_by(m.TeamActivity.id.desc())
            .limit(100)
            .all()
        ],
    }


def save_member(db, ctx, data, user=None):
    portal, tenant = ctx["kind"], ctx["id"]
    email = data.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or not data.name.strip():
        raise HTTPException(422, "Geçerli ad ve e-posta girin.")
    if user and email != user.email.lower():
        raise HTTPException(422, "Giriş e-postası değiştirilemez; yeni bir kullanıcı davet edin.")
    if not user:
        for cls in (m.Supplier, m.Customer, m.SupplierPortalUser, m.CustomerPortalUser):
            if db.query(cls).filter(cls.email.ilike(email)).first():
                raise HTTPException(409, "Bu e-posta adresi zaten kayıtlı.")
    base, rid, permissions = role_value(db, ctx, data.role)
    if data.permissions is not None:
        permissions = validate_permissions(portal, base, data.permissions)
    if portal == "customer" and data.assigned_plate:
        if not db.query(m.Vehicle).filter_by(customer_id=tenant, plate=data.assigned_plate).first():
            raise HTTPException(422, "Araç bu müşteriye ait değil.")
    if portal == "customer" and base == "Sürücü" and not data.assigned_plate:
        raise HTTPException(422, "Sürücü için tahsis edilmiş araç seçin.")
    if not user:
        user = model(portal)(
            **{portal + "_id": tenant},
            name=data.name.strip(),
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(48)),
            role=base,
            is_active=data.is_active,
            created_at=stamp(),
        )
        db.add(user)
        db.flush()
        access = m.TeamMemberAccess(portal=portal, tenant_id=tenant, user_id=user.id, pending=True)
        db.add(access)
    else:
        access = access_row(db, portal, tenant, user)
        if (access.version if access else 0) != data.version:
            raise HTTPException(409, "Kullanıcı başka bir işlemde değişti. Listeyi yenileyin.")
        if not access:
            access = m.TeamMemberAccess(portal=portal, tenant_id=tenant, user_id=user.id, version=0)
            db.add(access)
        revoke_sessions(db, portal, tenant, user.id)
    user.name = data.name.strip()
    user.role = base
    user.is_active = data.is_active
    if portal == "customer":
        user.phone = data.phone
        user.assigned_plate = data.assigned_plate or None
    access.department = data.department.strip()
    access.role_id = rid
    access.permissions = data.permissions
    # A built-in role also gets an explicit policy, preventing legacy endpoints from broadening it.
    if rid is None and access.permissions is None:
        access.permissions = permissions
    access.version = (access.version or 0) + 1
    if not user.is_active:
        scope(db, m.TeamInvitation, portal, tenant).filter_by(
            user_id=user.id, accepted_at=None
        ).update({"revoked_at": stamp()})
    log(db, ctx, "Kullanıcı kaydedildi", user.email)
    db.commit()
    db.refresh(user)
    return user


def send_invitation(db, ctx, user):
    if not user.is_active:
        raise HTTPException(409, "Pasif kullanıcıya davet gönderilemez.")
    portal, tenant = ctx["kind"], ctx["id"]
    scope(db, m.TeamInvitation, portal, tenant).filter_by(
        user_id=user.id, accepted_at=None, revoked_at=None
    ).update({"revoked_at": stamp()})
    token = secrets.token_urlsafe(48)
    db.add(
        m.TeamInvitation(
            portal=portal,
            tenant_id=tenant,
            user_id=user.id,
            token_hash=token_digest(token),
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
            created_at=stamp(),
        )
    )
    log(db, ctx, "Kullanıcı daveti oluşturuldu", user.email)
    db.commit()
    url = (
        os.environ.get("APP_BASE_URL", "https://fleetrent.com.tr").rstrip("/")
        + "/accept-invitation#token="
        + token
    )
    from app import email_utils as email

    try:
        email._send_message(
            user.email,
            "FleetRent ekip daveti",
            "<h2>FleetRent ekip daveti</h2><p>Merhaba "
            + escape(user.name)
            + '</p><p>48 saat içinde şifrenizi belirleyerek ekibe katılabilirsiniz. Yeni davet, önceki bağlantıyı geçersiz kılar.</p><a href="'
            + escape(url, quote=True)
            + '">Daveti kabul et</a>',
            os.environ.get("SMTP_FROM", "info@fleetrent.com.tr"),
            os.environ.get("SMTP_HOST", ""),
            os.environ.get("SMTP_USER", ""),
            os.environ.get("SMTP_PASS", ""),
            int(os.environ.get("SMTP_PORT", "587")),
        )
        sent = True
    except Exception:
        sent = False
    return {
        "email_sent": sent,
        "invitation_url": url,
        "message": (
            "Davet e-posta ile gönderildi."
            if sent
            else "E-posta gönderilemedi. Davet bağlantısını kopyalayabilir veya tekrar gönderebilirsiniz."
        ),
    }


@router.post("/{portal}/users", status_code=201)
def create_user(portal: str, data: MemberInput, request: Request, db: Session = Depends(get_db)):
    ctx = identity(request, db, portal)
    try:
        user = save_member(db, ctx, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu e-posta zaten kayıtlı.")
    result = {"user": serialize(db, portal, ctx["id"], user)}
    if data.invite:
        result.update(send_invitation(db, ctx, user))
    return result


@router.put("/{portal}/users/{uid}")
def edit_user(
    portal: str, uid: int, data: MemberInput, request: Request, db: Session = Depends(get_db)
):
    ctx = identity(request, db, portal)
    user = find_user(db, ctx, uid)
    user = save_member(db, ctx, data, user)
    return {"user": serialize(db, portal, ctx["id"], user)}


@router.post("/{portal}/users/{uid}/invite")
def invite_user(portal: str, uid: int, request: Request, db: Session = Depends(get_db)):
    ctx = identity(request, db, portal)
    return send_invitation(db, ctx, find_user(db, ctx, uid))


@router.post("/{portal}/users/{uid}/revoke-invitation")
def revoke_invitation(portal: str, uid: int, request: Request, db: Session = Depends(get_db)):
    ctx = identity(request, db, portal)
    user = find_user(db, ctx, uid)
    scope(db, m.TeamInvitation, portal, ctx["id"]).filter_by(
        user_id=uid, accepted_at=None, revoked_at=None
    ).update({"revoked_at": stamp()})
    log(db, ctx, "Davet iptal edildi", user.email)
    db.commit()
    return {"ok": True}


@router.post("/{portal}/roles", status_code=201)
def create_role(portal: str, data: RoleInput, request: Request, db: Session = Depends(get_db)):
    ctx = identity(request, db, portal)
    base, rid, _ = role_value(db, ctx, data.base_role)
    if rid:
        raise HTTPException(422, "Temel rol bir sistem rolü olmalıdır.")
    values = validate_permissions(portal, base, data.permissions)
    if not data.name.strip():
        raise HTTPException(422, "Rol adı gerekli.")
    row = m.TeamRole(
        portal=portal,
        tenant_id=ctx["id"],
        name=data.name.strip(),
        description=data.description,
        base_role=base,
        permissions=values,
    )
    db.add(row)
    log(db, ctx, "Rol oluşturuldu", row.name)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu isimde bir rol var.")
    return {"key": "custom:" + str(row.id)}


@router.put("/{portal}/roles/{rid}")
def edit_role(
    portal: str, rid: int, data: RoleInput, request: Request, db: Session = Depends(get_db)
):
    ctx = identity(request, db, portal)
    row = scope(db, m.TeamRole, portal, ctx["id"]).filter_by(id=rid).first()
    if not row:
        raise HTTPException(404, "Rol bulunamadı.")
    if row.version != data.version:
        raise HTTPException(409, "Rol değişti. Listeyi yenileyin.")
    if data.base_role != row.base_role:
        raise HTTPException(422, "Temel rol değiştirilemez; yeni bir rol oluşturun.")
    row.permissions = validate_permissions(portal, row.base_role, data.permissions)
    row.name = data.name.strip()
    row.description = data.description
    row.version += 1
    if not row.name:
        raise HTTPException(422, "Rol adı gerekli.")
    for access in scope(db, m.TeamMemberAccess, portal, ctx["id"]).filter_by(role_id=rid).all():
        access.version += 1
        revoke_sessions(db, portal, ctx["id"], access.user_id)
    log(db, ctx, "Rol izinleri güncellendi", row.name)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu isimde bir rol var.")
    return {"ok": True}


@router.delete("/{portal}/roles/{rid}")
def delete_role(portal: str, rid: int, request: Request, db: Session = Depends(get_db)):
    ctx = identity(request, db, portal)
    row = scope(db, m.TeamRole, portal, ctx["id"]).filter_by(id=rid).first()
    if not row:
        raise HTTPException(404, "Rol bulunamadı.")
    if scope(db, m.TeamMemberAccess, portal, ctx["id"]).filter_by(role_id=rid).first():
        raise HTTPException(409, "Bu rol kullanıcıya atanmış. Önce kullanıcının rolünü değiştirin.")
    log(db, ctx, "Rol silindi", row.name)
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/invitation/inspect")
def inspect_invitation(data: dict, db: Session = Depends(get_db)):
    invite = valid_invitation(db, data.get("token", ""))
    user = db.get(model(invite.portal), invite.user_id)
    return {"name": user.name, "portal": invite.portal, "expires_at": invite.expires_at}


def valid_invitation(db, token):
    row = db.query(m.TeamInvitation).filter_by(token_hash=token_digest(str(token))).first()
    if not row or row.accepted_at or row.revoked_at or session_expired(row.expires_at):
        raise HTTPException(410, "Davet geçersiz, kullanılmış veya süresi dolmuş.")
    user = db.get(model(row.portal), row.user_id)
    if not user or not user.is_active or getattr(user, row.portal + "_id") != row.tenant_id:
        raise HTTPException(410, "Kullanıcı daveti artık etkin değil.")
    return row


@router.post("/invitation/accept")
def accept_invitation(data: AcceptInput, db: Session = Depends(get_db)):
    invite = valid_invitation(db, data.token)
    password = hash_password(data.password)
    result = db.execute(
        update(m.TeamInvitation)
        .where(
            m.TeamInvitation.id == invite.id,
            m.TeamInvitation.accepted_at.is_(None),
            m.TeamInvitation.revoked_at.is_(None),
        )
        .values(accepted_at=stamp())
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(410, "Davet daha önce kullanılmış.")
    user = db.get(model(invite.portal), invite.user_id)
    user.password_hash = password
    if invite.portal == "customer":
        user.is_email_verified = True
        user.verification_token = None
    access = access_row(db, invite.portal, invite.tenant_id, user)
    if access:
        access.pending = False
        access.version += 1
    revoke_sessions(db, invite.portal, invite.tenant_id, user.id)
    scope(db, m.TeamInvitation, invite.portal, invite.tenant_id).filter(
        m.TeamInvitation.user_id == user.id,
        m.TeamInvitation.id != invite.id,
        m.TeamInvitation.accepted_at.is_(None),
    ).update({"revoked_at": stamp()})
    db.commit()
    return {
        "portal": invite.portal,
        "message": "Şifreniz oluşturuldu. Hesabınızla giriş yapabilirsiniz.",
    }
