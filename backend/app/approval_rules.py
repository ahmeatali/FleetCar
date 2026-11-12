"""Role-based approval limits and the step chain an approval request walks through.

A role's limit is the largest amount that role may give the final approval for.
A request starts at the lowest role that takes part in the category and climbs
until it reaches a role whose limit covers the amount; the owner (Genel Müdür)
has no limit and closes any chain that no other role covers.
"""

from fastapi import HTTPException

from app.common.time import stamp

APPROVAL_ROLES = ["fleet_manager", "operations", "finance"]
ROLE_LABELS = {
    "fleet_manager": "Filo Yöneticisi",
    "operations": "Operasyon Müdürü",
    "finance": "Finans Müdürü",
    "owner": "Genel Müdür",
}
CATEGORIES = {
    "service": ("Servis / Bakım", {"service", "maintenance"}),
    "tire": ("Lastik", {"tire"}),
    "damage": ("Hasar / Kaza", {"damage"}),
    "contract": ("Sözleşme / Teklif", {"contract", "offer"}),
    "policy": ("Sigorta / Kasko", {"policy"}),
    "return": ("Teslim / İade", {"delivery", "return"}),
    "invoice": ("Fatura / Ceza", {"invoice", "fine"}),
    "sale": ("Araç Satışı", {"sale"}),
    "other": ("Diğer", set()),
}
DEFAULT_MATRIX = {
    "service": {"fleet_manager": 10000, "operations": 50000, "finance": 100000},
    "tire": {"fleet_manager": 10000, "operations": 50000, "finance": 100000},
    "damage": {"fleet_manager": 20000, "operations": 100000, "finance": 250000},
    "contract": {"fleet_manager": 100000, "operations": 500000, "finance": 1000000},
    "policy": {"fleet_manager": 20000, "operations": 100000, "finance": 250000},
    "return": {"fleet_manager": 20000, "operations": 50000, "finance": 100000},
    "invoice": {"fleet_manager": 10000, "operations": 50000, "finance": 100000},
    "sale": {"fleet_manager": None, "operations": None, "finance": 500000},
    "other": {"fleet_manager": 10000, "operations": 50000, "finance": 100000},
}


def category_of(kind):
    return next((key for key, (_, kinds) in CATEGORIES.items() if kind in kinds), "other")


def normalize_matrix(stored):
    """Fill missing categories and roles with defaults; keep explicit None (role skipped)."""
    stored = stored if isinstance(stored, dict) else {}
    result = {}
    for key, defaults in DEFAULT_MATRIX.items():
        row = stored.get(key) if isinstance(stored.get(key), dict) else {}
        result[key] = {role: row.get(role, defaults[role]) for role in APPROVAL_ROLES}
    return result


def validate_matrix(matrix):
    if set(matrix) - set(CATEGORIES):
        raise ValueError("Bilinmeyen onay konusu.")
    for key, row in matrix.items():
        if not isinstance(row, dict) or set(row) - set(APPROVAL_ROLES):
            raise ValueError("Onay matrisinde bilinmeyen rol.")
        previous = 0
        for role in APPROVAL_ROLES:
            limit = row.get(role)
            if limit is None:
                continue
            if isinstance(limit, bool) or not isinstance(limit, (int, float)) or limit < 0:
                raise ValueError("Onay limitleri sıfır veya pozitif tutar olmalı.")
            if limit < previous:
                raise ValueError(
                    f"{CATEGORIES[key][0]}: üst rolün limiti alt rolden düşük olamaz."
                )
            previous = limit
    return normalize_matrix(matrix)


def build_steps(matrix, kind, amount):
    limits = normalize_matrix(matrix)[category_of(kind)]
    steps = []
    for role in APPROVAL_ROLES:
        limit = limits[role]
        if limit is None:
            continue
        steps.append({"role": role, "limit": limit, "status": "Bekliyor"})
        if amount <= limit:
            return steps
    steps.append({"role": "owner", "limit": None, "status": "Bekliyor"})
    return steps


def approval_details(matrix, parent_kind, amount, requester, details=None):
    return {
        **(details or {}),
        "category": category_of(parent_kind),
        "parent_kind": parent_kind,
        "requested_by": requester,
        "steps": build_steps(matrix, parent_kind, amount),
    }


def current_step(details):
    return next(
        (i for i, s in enumerate(details.get("steps") or []) if s["status"] == "Bekliyor"), None
    )


def decide(ctx, details, approve, note=""):
    """Apply one decision to an approval's steps. Returns (new_details, new_status)."""
    steps = [dict(s) for s in details.get("steps") or []]
    index = current_step({"steps": steps})
    if index is None:
        raise HTTPException(400, "Bu onay talebinde bekleyen adım yok.")
    role = ctx["role"]
    if role != "owner" and steps[index]["role"] != role:
        raise HTTPException(
            403,
            f"Bu adım {ROLE_LABELS[steps[index]['role']]} onayında. Rolünüz yetkili değil.",
        )
    user_id = getattr(ctx.get("session"), "user_id", None)
    requester = details.get("requested_by") or {}
    if approve and role != "owner" and user_id and requester.get("user_id") == user_id:
        raise HTTPException(403, "Kendi oluşturduğunuz talebi onaylayamazsınız.")
    decision = {
        "status": "Onaylandı" if approve else "Reddedildi",
        "actor": ctx["actor"],
        "actor_role": role,
        "user_id": user_id,
        "at": stamp(),
        "note": note,
    }
    if not approve:
        steps[index].update(decision)
        return {**details, "steps": steps}, "Reddedildi"
    # The owner has no limit: one owner approval closes every remaining step.
    targets = range(index, len(steps)) if role == "owner" else [index]
    for i in targets:
        steps[i].update(decision)
        if i != index:
            steps[i]["note"] = "Genel Müdür onayıyla tamamlandı."
    status = "Beklemede" if current_step({"steps": steps}) is not None else "Onaylandı"
    return {**details, "steps": steps}, status
