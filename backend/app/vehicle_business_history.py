"""Commercial vehicle history reads the same records used by supplier operations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models as m
from app.database import get_db
from app.offer_history import customer_context
from app.supplier_service import serialize

router = APIRouter(prefix="/api/customer-workspace")


def history(db, vid, supplier_id=None, customer_id=None):
    contracts = {r.contract_id for r in db.query(m.ContractVehicle).filter_by(vehicle_id=vid).all()}
    query = db.query(m.SupplierOperation)
    if supplier_id is not None:
        query = query.filter_by(supplier_id=supplier_id)
    if customer_id is not None:
        query = query.filter_by(customer_id=customer_id).filter(
            m.SupplierOperation.status.notin_(["Taslak", "İptal"])
        )
    rows = []
    for row in query.order_by(m.SupplierOperation.id.desc()).all():
        allocations = (row.details or {}).get("vehicle_allocations", [])
        allocated = (
            any(str(a.get("vehicle_id")) == vid for a in allocations if isinstance(a, dict))
            if isinstance(allocations, list)
            else False
        )
        if row.vehicle_id != vid and row.id not in contracts and not allocated:
            continue
        item = serialize(db, row)
        # Internal notes, approval metadata and other fleet vehicles remain supplier-only.
        rows.append(
            {
                k: item[k]
                for k in [
                    "id",
                    "kind",
                    "number",
                    "title",
                    "date",
                    "end_date",
                    "amount",
                    "status",
                    "paid",
                    "balance",
                    "customer_name",
                ]
            }
        )
    return rows


@router.get("/vehicles/{vid}/business-history")
def customer_history(vid: str, p=Depends(customer_context), db: Session = Depends(get_db)):
    from app.tenant_visibility import customer_vehicle_ids

    if vid not in customer_vehicle_ids(db, p["id"]):
        raise HTTPException(404, "Araç bulunamadı.")
    from app.team_permissions import KINDS, policy

    permissions = policy(db, "customer", p["id"], p.get("user_id"))
    rows = history(db, vid, customer_id=p["id"])
    return (
        rows
        if permissions is None
        else [row for row in rows if permissions.get(KINDS.get(row["kind"]), {}).get("view", False)]
    )
