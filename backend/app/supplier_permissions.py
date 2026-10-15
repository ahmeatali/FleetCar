"""Seven supplier roles. Read, write, approval, document and export are separate actions."""

from fastapi import HTTPException

ROLES = {"owner", "fleet_manager", "operations", "finance", "sales", "delivery", "viewer"}
WRITES = {
    "owner": None,
    "fleet_manager": {
        "vehicle",
        "customer",
        "offer",
        "contract",
        "delivery",
        "return",
        "policy",
        "damage",
        "fine",
        "scenario",
        "maintenance",
        "service",
        "tire",
        "fuel",
        "hgs",
        "sale",
    },
    "operations": {
        "vehicle",
        "customer",
        "offer",
        "contract",
        "delivery",
        "return",
        "policy",
        "damage",
        "scenario",
        "maintenance",
        "service",
        "tire",
        "fuel",
        "hgs",
    },
    "finance": {"invoice", "payment", "fine", "return", "fuel", "hgs"},
    "sales": {"customer", "offer", "contract", "sale"},
    "delivery": {"delivery", "return"},
    "viewer": set(),
}
EXPORT_ROLES = {"owner", "fleet_manager", "finance"}
DOCUMENT_ROLES = ROLES.copy()


def capabilities(role):
    return {
        "view": role in ROLES,
        "write": sorted(WRITES.get(role) or []) if role != "owner" else ["*"],
        "approve": role == "owner",
        "download_document": role in DOCUMENT_ROLES,
        "export_report": role in EXPORT_ROLES,
    }


def permit(ctx, kind):
    role = ctx["role"]
    if role not in ROLES or role != "owner" and kind not in WRITES[role]:
        raise HTTPException(403, "Bu işlem için rolünüz yetkili değil.")
