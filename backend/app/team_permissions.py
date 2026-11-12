"""Tenant-owned restrictions on existing portal capabilities; never widens base-role authority."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import models as m
from app.database import get_db
from app.supplier_permissions import EXPORT_ROLES, WRITES

MODULES = {
    "vehicles": "Araçlar",
    "customers": "Müşteriler",
    "offers": "Talep & Teklifler",
    "contracts": "Sözleşmeler",
    "operations": "Operasyonlar & Kiralamalar",
    "service": "Servis & Bakım",
    "tires": "Lastik",
    "damage": "Hasar & Kaza",
    "policies": "Sigorta & Kasko",
    "tolls": "HGS & Cezalar",
    "fuel": "Yakıt & Giderler",
    "invoices": "Faturalar & Muhasebe",
    "reports": "Raporlar & Tasarruf",
    "planning": "Filo Planlama",
    "settings": "Ayarlar & Entegrasyonlar",
}
ACTIONS = {
    "view": "Görüntüle",
    "create": "Ekle",
    "edit": "Düzenle",
    "delete": "Sil / İptal",
    "approve": "Onayla",
    "export": "İndir",
}
KINDS = {
    "vehicle": "vehicles",
    "customer": "customers",
    "offer": "offers",
    "contract": "contracts",
    "delivery": "operations",
    "return": "operations",
    "rental": "operations",
    "reservation": "operations",
    "task": "operations",
    "branch": "operations",
    "maintenance": "service",
    "service": "service",
    "tire": "tires",
    "damage": "damage",
    "policy": "policies",
    "hgs": "tolls",
    "fine": "tolls",
    "fuel": "fuel",
    "invoice": "invoices",
    "payment": "invoices",
    "scenario": "planning",
    "sale": "vehicles",
    "approval": "invoices",
}
CUSTOMER_ROLES = {
    "Filo Yöneticisi",
    "Finans Sorumlusu",
    "Operasyon Personeli",
    "Sürücü",
    "Görüntüleyici",
}


def base_permissions(portal, role):
    matrix = {key: {action: False for action in ACTIONS} for key in MODULES}
    if portal == "supplier":
        for values in matrix.values():
            values["view"] = True
        for kind in WRITES.get(role) or []:
            module = KINDS.get(kind)
            if module:
                for action in ("create", "edit"):
                    matrix[module][action] = True
        if role in {"fleet_manager", "operations", "delivery"}:
            matrix["operations"]["create"] = matrix["operations"]["edit"] = True
        matrix["operations"]["delete"] = "contract" in (WRITES.get(role) or set())
        if role in EXPORT_ROLES:
            matrix["reports"]["export"] = True
        for module in ("offers", "contracts", "policies", "damage", "invoices", "planning"):
            matrix[module]["delete"] = matrix[module]["edit"]
    else:
        for key in (
            "vehicles",
            "offers",
            "contracts",
            "operations",
            "service",
            "tires",
            "damage",
            "tolls",
            "fuel",
            "invoices",
            "reports",
            "settings",
        ):
            matrix[key]["view"] = True
        if role not in {"Görüntüleyici", "Sürücü"}:
            for key in ("offers", "operations", "service", "damage", "fuel", "settings"):
                matrix[key]["create"] = matrix[key]["edit"] = True
            matrix["contracts"]["edit"] = True
            matrix["operations"]["edit"] = True
            matrix["vehicles"]["edit"] = True
            matrix["offers"]["delete"] = True
            for key in ("service", "damage", "fuel"):
                matrix[key]["edit"] = False
            matrix["reports"]["create"] = True
        if role == "Filo Yöneticisi":
            matrix["offers"]["approve"] = True
        if role != "Sürücü":
            matrix["reports"]["export"] = True
    return matrix


def policy(db, portal, tenant_id, user_id):
    if not user_id:
        return None
    access = (
        db.query(m.TeamMemberAccess)
        .filter_by(portal=portal, tenant_id=tenant_id, user_id=user_id)
        .first()
    )
    if not access:
        return None
    role = db.get(m.TeamRole, access.role_id) if access.role_id else None
    return (
        access.permissions if access.permissions is not None else role.permissions if role else None
    )


def validate_permissions(portal, role, values):
    ceiling = base_permissions(portal, role)
    if not isinstance(values, dict) or set(values) - set(MODULES):
        raise HTTPException(422, "Geçersiz modül izinleri.")
    result = {key: {action: False for action in ACTIONS} for key in MODULES}
    for key, actions in values.items():
        if not isinstance(actions, dict) or set(actions) - set(ACTIONS):
            raise HTTPException(422, "Geçersiz işlem izni.")
        for action, value in actions.items():
            if type(value) is not bool or value and not ceiling[key][action]:
                raise HTTPException(422, "İzin, temel rolün desteklediği işlemleri aşamaz.")
            result[key][action] = value
        if not result[key]["view"] and any(
            result[key][action] for action in ACTIONS if action != "view"
        ):
            raise HTTPException(422, "İşlem izni için görüntüleme izni gerekli.")
    return result


def module_for_path(path, request, db):
    for key, cls in (("eid", m.SignatureEnvelope), ("docid", m.SignedDocument)):
        value = request.path_params.get(key)
        if value:
            document = db.get(cls, value)
            record = db.get(m.SupplierOperation, document.operation_id) if document else None
            if record:
                return KINDS.get(record.kind)
    resource = request.path_params.get("resource")
    if resource in {"hgs", "expenses", "locations", "mileage-records", "usage-records", "files"}:
        return {
            "hgs": "tolls",
            "expenses": "fuel",
            "locations": "reports",
            "mileage-records": "reports",
            "usage-records": "reports",
            "files": "vehicles",
        }[resource]
    # Most specific resource first, so vehicle child endpoints cannot bypass their own module.
    for text, module in (
        ("customer-documents", "settings"),
        ("signed-document", "contracts"),
        ("locations", "reports"),
        ("mileage", "reports"),
        ("usage", "reports"),
        ("/hgs", "tolls"),
        ("expense", "fuel"),
        ("fuel", "fuel"),
        ("/integrations", "settings"),
        ("/settings", "settings"),
        ("/company", "settings"),
        ("customer/documents", "settings"),
        ("reports", "reports"),
        ("dashboard", "reports"),
        ("tires", "tires"),
        ("tire-", "tires"),
        ("roadside", "service"),
        ("/requests", "service"),
        ("/services", "service"),
        ("quotes", "offers"),
        ("bids", "offers"),
        ("offer-history", "offers"),
        ("signature", "contracts"),
        ("delivery", "operations"),
        ("/fleet/", "operations"),
        ("vehicle", "vehicles"),
        ("directory", "customers"),
        ("/customers", "customers"),
    ):
        if text in path:
            return module
    kind = request.path_params.get("kind")
    if kind in KINDS:
        return KINDS[kind]
    rid = request.path_params.get("rid") or request.path_params.get("record_id")
    if rid and str(rid).isdigit():
        record = db.get(m.SupplierOperation, int(rid))
        if record:
            return KINDS.get(record.kind)
    return None


async def enforce_access(request: Request, db: Session = Depends(get_db)):
    from app.portal_access import PUBLIC, principal

    path = request.url.path
    route = request.scope.get("route")
    pattern = route.path if route else path
    if (
        pattern in PUBLIC
        or not path.startswith(("/api/", "/uploads/"))
        or path.startswith(("/api/team", "/api/auth/", "/api/admin/"))
    ):
        return
    # Existing public email verification/setup routes retain their existing authentication contract.
    if path.startswith(
        ("/api/auth/verify-email/", "/api/supplier/verify-token/", "/api/customer/verify-token/")
    ):
        return
    if path in {
        "/api/supplier-workspace/session",
        "/api/supplier-workspace/logout",
        "/api/supplier-workspace/snapshot",
    }:
        return
    p = principal(request, db)
    if p["kind"] not in {"customer", "supplier"}:
        return
    permissions = policy(db, p["kind"], p["id"], p.get("user_id"))
    if permissions is None:
        return
    if "/users" in path:
        raise HTTPException(403, "Kullanıcı yönetimi şirket sahibine aittir.")
    module = module_for_path(pattern, request, db)
    action = (
        "view"
        if request.method in {"GET", "HEAD"}
        else (
            "create"
            if request.method == "POST"
            else "delete" if request.method == "DELETE" else "edit"
        )
    )
    if request.method == "POST" and any(
        key in request.path_params
        for key in ("rid", "uid", "eid", "vid", "vehicle_id", "request_id")
    ):
        action = "edit"
    if path.endswith(("/approve", "/reject", "/decision", "/status")) and (
        "bids" in path or "approval" in path
    ):
        action = "approve"
    if path.endswith(("/cancel", "/delete")):
        action = "delete"
    if request.method == "POST" and path.endswith("/status"):
        try:
            status = (await request.json()).get("status")
            if status in {"İptal", "Silindi"}:
                action = "delete"
        except (ValueError, AttributeError):
            pass
    if request.query_params.get("format", "json") != "json" or path.endswith(
        ("/download", "/pdf", "/csv")
    ):
        action = "export"
    if "/records" in path and request.method == "POST" and not request.path_params:
        try:
            module = KINDS.get((await request.json()).get("kind"))
        except (ValueError, AttributeError):
            pass
    if request.method == "POST" and path.endswith("/convert"):
        try:
            target = "contract" if "/fleet/" in path else (await request.json()).get("kind")
        except (ValueError, AttributeError):
            target = None
        if not permissions.get(KINDS.get(target), {}).get("create", False):
            raise HTTPException(403, "Dönüştürülecek kayıt için ekleme izniniz yok.")
    if not module or not permissions.get(module, {}).get(action, False):
        raise HTTPException(403, "Bu modül veya işlem için erişim izniniz yok.")


def filter_snapshot(result, permissions):
    if permissions is None:
        return result

    def can(module):
        return permissions.get(module, {}).get("view", False)

    for key, module in {
        "vehicles": "vehicles",
        "customers": "customers",
        "rentals": "operations",
        "service": "service",
        "fuel": "fuel",
        "hgs": "tolls",
        "tire": "tires",
        "files": "vehicles",
        "usage": "reports",
        "settings": "settings",
    }.items():
        if key in result and not can(module):
            result[key] = {} if key == "settings" else []
    result["matching_queue"] = [
        row for row in result.get("matching_queue", []) if can(KINDS.get(row["kind"], "settings"))
    ]
    result["events"] = []
    result["records"] = [
        row for row in result.get("records", []) if can(KINDS.get(row["kind"], "settings"))
    ]
    return result
