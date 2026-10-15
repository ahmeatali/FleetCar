"""Fail-closed authorization for legacy portal routes and private files."""

import os
from urllib.parse import urlencode

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.datastructures import QueryParams

from app import models as m
from app.common.security import issue_session, session_expired, token_digest
from app.common.time import stamp
from app.database import get_db
from app.supplier_context import SERVICE_TYPES

PUBLIC = {
    "/api/admin/login",
    "/admin/login",
    "/api/customer/login",
    "/api/service/login",
    "/api/supplier/login",
    "/api/customer/register",
    "/api/supplier/register",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/auth/resend-verification",
    "/api/customer/set-password",
    "/api/supplier/set-password",
}


def mint(db, kind, subject_id, user_id=None, response=None):
    token = issue_session(db, m.PortalSession, kind=kind, subject_id=subject_id, user_id=user_id)
    if response is not None:
        cookie(response, token)
    return token


def cookie(response, token):
    response.set_cookie(
        "fleetcar_session",
        token,
        httponly=True,
        samesite="lax",
        max_age=604800,
        path="/uploads",
        secure=os.environ.get("FLEETCAR_COOKIE_SECURE", "false").lower() == "true",
    )


def identify(request, value):
    request.state.audit_principal = value
    return value


def principal(request: Request, db):
    header = request.headers.get("authorization", "")
    token = (
        header[7:]
        if header.startswith("Bearer ")
        else (
            request.cookies.get("fleetcar_session", "")
            if request.url.path.startswith("/uploads/")
            else ""
        )
    )
    if not token:
        raise HTTPException(401, "Oturum gerekli. Tekrar giriş yapın.")
    digest = token_digest(token)
    session = db.query(m.PortalSession).filter_by(token_hash=digest).first()
    if session:
        if session_expired(session.expires_at):
            raise HTTPException(401, "Oturum süresi doldu.")
        if session.kind == "admin":
            if not db.get(m.AdminUser, session.subject_id):
                raise HTTPException(401, "Oturum geçersiz.")
            return identify(request, {"kind": "admin", "id": session.subject_id, "role": "owner"})
        c = db.get(m.Customer, session.subject_id)
        user = db.get(m.CustomerPortalUser, session.user_id) if session.user_id else None
        if (
            not c
            or session.user_id
            and (not user or not user.is_active or user.customer_id != c.id)
        ):
            raise HTTPException(401, "Oturum geçersiz.")
        return identify(
            request,
            {
                "kind": "customer",
                "id": c.id,
                "role": user.role if user else "owner",
                "plate": user.assigned_plate if user else None,
                "user_id": session.user_id,
            },
        )
    session = db.query(m.SupplierSession).filter_by(token_hash=digest).first()
    if not session or session_expired(session.expires_at):
        raise HTTPException(401, "Oturum geçersiz veya süresi doldu.")
    supplier = db.get(m.Supplier, session.supplier_id)
    user = db.get(m.SupplierPortalUser, session.user_id) if session.user_id else None
    if (
        not supplier
        or session.user_id
        and (not user or not user.is_active or user.supplier_id != supplier.id)
    ):
        raise HTTPException(401, "Oturum geçersiz.")
    from app.supplier_permissions import ROLES

    if user and user.role not in ROLES:
        raise HTTPException(403, "Kullanıcı rolü geçersiz.")
    return identify(
        request,
        {
            "kind": "service" if supplier.type in SERVICE_TYPES else "supplier",
            "id": supplier.id,
            "role": user.role if user else "owner",
            "type": supplier.type,
            "user_id": session.user_id,
        },
    )


def check_vehicle(db, p, vid):
    car = db.get(m.Vehicle, vid)
    if not car:
        raise HTTPException(404, "Araç bulunamadı.")
    if p["kind"] == "admin":
        return car
    if (
        p["kind"] == "customer"
        and car.customer_id == p["id"]
        and (not p.get("plate") or car.plate == p["plate"])
    ):
        return car
    if p["kind"] == "supplier" and car.supplier_id == p["id"]:
        return car
    if (
        p["kind"] == "service"
        and db.query(m.Request).filter_by(vehicle_id=vid, supplier_id=p["id"]).first()
    ):
        return car
    raise HTTPException(404, "Araç bulunamadı.")


def bind_query(request, key, value):
    pairs = [(k, v) for k, v in request.query_params.multi_items() if k != key] + [
        (key, str(value))
    ]
    request.scope["query_string"] = urlencode(pairs).encode()
    request._query_params = QueryParams(request.scope["query_string"].decode())


def access_audit(db, p, request):
    db.add(
        m.AccessAudit(
            principal_kind=p["kind"],
            subject_id=p["id"],
            method=request.method,
            resource=(
                request.scope.get("route").path if request.scope.get("route") else request.url.path
            ),
            created_at=stamp(),
        )
    )
    db.commit()


async def legacy_access(request: Request, db: Session = Depends(get_db)):
    path = request.scope["route"].path
    if path in PUBLIC or path.startswith(
        ("/api/auth/verify-email/", "/api/supplier/verify-token/", "/api/customer/verify-token/")
    ):
        return
    p = principal(request, db)
    request.state.portal = p
    if p["kind"] == "admin":
        access_audit(db, p, request)
        return
    if path.startswith("/api/admin/") or path == "/api/customers":
        raise HTTPException(403, "Yönetici yetkisi gerekli.")
    ids = request.path_params
    if request.method not in {"GET", "HEAD"} and p["role"] in {"viewer", "Sürücü", "Görüntüleyici"}:
        raise HTTPException(403, "Bu işlem için yetkiniz yok.")
    payload = {}
    if request.method not in {"GET", "HEAD"} and request.headers.get("content-type", "").startswith(
        "application/json"
    ):
        try:
            payload = await request.json()
        except ValueError:
            raise HTTPException(400, "Geçersiz JSON.")
        if not isinstance(payload, dict):
            raise HTTPException(422, "Nesne bekleniyor.")
    if (
        p["kind"] == "service"
        and payload.get("supplier_id") is not None
        and payload["supplier_id"] != p["id"]
    ):
        raise HTTPException(403, "Servis kimliği oturumla eşleşmiyor.")
    if (
        p["kind"] == "supplier"
        and request.method not in {"GET", "HEAD"}
        and not (path == "/api/quotes/{quote_id}/bids")
    ):
        raise HTTPException(403, "İşlemi yetki kontrollü tedarikçi çalışma alanından yapın.")
    if (
        p["kind"] in {"supplier", "service"}
        and ids.get("supplier_id")
        and int(ids["supplier_id"]) != p["id"]
    ):
        raise HTTPException(404, "Tedarikçi bulunamadı.")
    vid = (
        ids.get("vehicle_id") or payload.get("vehicle_id") or request.query_params.get("vehicle_id")
    )
    if vid:
        check_vehicle(db, p, vid)
    for key, cls in [
        ("expense_id", m.VehicleExpense),
        ("tire_id", m.TireRecord),
        ("case_id", m.RoadsideCase),
        ("request_id", m.Request),
        ("file_id", m.VehicleFile),
    ]:
        if key not in ids:
            continue
        row = db.get(cls, ids[key])
        if not row:
            raise HTTPException(404, "Kayıt bulunamadı.")
        if p["kind"] == "customer" and key != "file_id":
            from app.tenant_visibility import event_visible

            when = (
                getattr(row, "date", None)
                or getattr(row, "created_at", None)
                or getattr(row, "installed_at", None)
            )
            kind = "fuel" if key == "expense_id" else None
            if not event_visible(db, p["id"], row.vehicle_id, when, kind, row.id):
                raise HTTPException(404, "Kayıt bulunamadı.")
        if key == "request_id" and p["kind"] == "service":
            if row.supplier_id != p["id"] and not (
                row.supplier_id is None and row.type == p["type"] and row.status == "Beklemede"
            ):
                raise HTTPException(404, "Talep bulunamadı.")
        else:
            check_vehicle(db, p, row.vehicle_id)
    if "user_id" in ids:
        user = db.get(m.CustomerPortalUser, ids["user_id"])
        if (
            p["kind"] != "customer"
            or p["role"] != "owner"
            or not user
            or user.customer_id != p["id"]
        ):
            raise HTTPException(404, "Kullanıcı bulunamadı.")
    if "quote_id" in ids or "bid_id" in ids:
        bid = db.get(m.SupplierBid, ids["bid_id"]) if "bid_id" in ids else None
        q = db.get(m.Quote, bid.quote_id if bid else ids.get("quote_id"))
        if not q:
            raise HTTPException(404, "Talep bulunamadı.")
        if p["kind"] == "customer" and q.customer_id != p["id"]:
            raise HTTPException(404, "Talep bulunamadı.")
        if (
            p["kind"] == "supplier"
            and q.status not in {"Teklif Bekleniyor", "Değerlendirmede", "Teklif Verildi"}
            and not db.query(m.SupplierBid).filter_by(quote_id=q.id, supplier_id=p["id"]).first()
        ):
            raise HTTPException(404, "Talep bulunamadı.")
        if p["kind"] == "supplier" and (
            bid
            and bid.supplier_id != p["id"]
            or request.method not in {"GET", "HEAD"}
            and not path.endswith("/bids")
        ):
            raise HTTPException(403, "İşlem yetkisi yok.")
    if p["kind"] == "customer":
        if path == "/api/quotes/{quote_id}/bids" and request.method == "POST":
            raise HTTPException(403, "Tedarikçi teklifini müşteri oluşturamaz.")
        if path == "/api/bids/{bid_id}/status" and p["role"] not in {
            "owner",
            "Yönetici",
            "Filo Yöneticisi",
            "Genel Müdür",
        }:
            raise HTTPException(403, "Teklif kararı için yönetici yetkisi gerekli.")
        if path.startswith("/api/suppliers/") or path == "/api/vehicles/removals":
            raise HTTPException(403, "Bu kaynağa müşteri erişimi yok.")
        if path == "/api/suppliers/{supplier_id}/bids":
            raise HTTPException(403, "Teklifleri kendi talebiniz üzerinden görüntüleyin.")
        if (
            path == "/api/vehicles/{vehicle_id}"
            and request.method == "PUT"
            and any(
                key in payload and payload[key] != getattr(db.get(m.Vehicle, vid), key, None)
                for key in {
                    "supplier_id",
                    "customer_id",
                    "contract_no",
                    "contract_start_date",
                    "contract_end_date",
                    "monthly_rent",
                    "contract_signed_at",
                }
            )
        ):
            raise HTTPException(403, "Müşteri araç sahipliği ve sözleşme bilgilerini değiştiremez.")
        if (
            p.get("plate")
            and not vid
            and path
            not in {"/api/company/profile", "/api/customer/settings/{key}", "/api/suppliers"}
        ):
            raise HTTPException(403, "Sürücü sadece kendisine atanan aracı görüntüleyebilir.")
        if path == "/api/quotes" and request.method == "POST":
            customer = db.get(m.Customer, p["id"])
            payload.update(
                {
                    "company_name": customer.company_name,
                    "email": customer.email or "",
                    "phone": customer.phone or "",
                }
            )
        if (
            path in {"/api/quotes/{quote_id}", "/api/quotes/{quote_id}/status"}
            and request.method == "PUT"
            and payload.get("status") in {"Sözleşme İmzalandı", "Sözleşme Yapıldı"}
        ):
            raise HTTPException(403, "İmzalı durum belge akışından oluşur.")
        if payload.get("customer_id") is not None and payload["customer_id"] != p["id"]:
            raise HTTPException(404, "Müşteri bulunamadı.")
        requested = request.query_params.get("customer_id")
        if requested and requested != str(p["id"]):
            raise HTTPException(404, "Müşteri bulunamadı.")
        bind_query(request, "customer_id", p["id"])
        if path.startswith("/api/customer/users") and p["role"] != "owner":
            raise HTTPException(403, "Kullanıcı yönetimi yetkisi gerekli.")
        if request.method not in {"GET", "HEAD"} and (
            path.startswith("/api/suppliers")
            or path.startswith("/api/requests/")
            or path.startswith("/api/roadside-cases/")
            or path in {"/api/vehicles", "/api/tires", "/api/tire-operations"}
        ):
            raise HTTPException(403, "Tedarikçi veya yönetici yetkisi gerekli.")
    elif p["kind"] == "supplier":
        if path == "/api/quotes/{quote_id}/bids" and request.method == "POST":
            from app.supplier_permissions import permit

            permit(p, "offer")
        if path.startswith("/api/customer/") and path != "/api/customer/delivery-forms":
            request.query_params.get("customer_id")
            # Delivery forms and customer company documents can contain other suppliers' records.
            raise HTTPException(
                403, "Müşteri kaynaklarını tedarikçi çalışma alanından görüntüleyin."
            )
        scope_paths = {
            "/api/quotes/{quote_id}/bids",
            "/api/customer/delivery-forms",
            "/api/vehicles",
            "/api/vehicle-expenses",
            "/api/quotes",
            "/api/vehicles/{vehicle_id}",
            "/api/vehicles/{vehicle_id}/files",
            "/api/vehicles/{vehicle_id}/hgs",
            "/api/vehicles/{vehicle_id}/locations",
        }
        if path in scope_paths:
            bind_query(request, "supplier_id", p["id"])
        elif path == "/api/requests":
            bind_query(request, "fleet_supplier_id", p["id"])
        elif not (
            vid
            or any(
                k in ids
                for k in ["expense_id", "tire_id", "case_id", "request_id", "quote_id", "bid_id"]
            )
            or path in {"/api/suppliers", "/api/suppliers/{supplier_id}/bids"}
        ):
            raise HTTPException(403, "Bu kaynağı tedarikçi çalışma alanından görüntüleyin.")
        if (
            request.query_params.get("supplier_id") != str(p["id"])
            and path.endswith("/bids")
            and request.method == "POST"
        ):
            raise HTTPException(403, "Tedarikçi kimliği eşleşmiyor.")
    else:
        if path == "/api/requests":
            bind_query(request, "supplier_id", p["id"])
        elif not (
            any(k in ids for k in ["request_id", "vehicle_id", "case_id"])
            or path in {"/api/suppliers", "/api/suppliers/{supplier_id}/bids"}
        ):
            raise HTTPException(403, "Servis yetkisi gerekli.")
    access_audit(db, p, request)
