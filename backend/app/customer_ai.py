"""AI fleet recommendations for customers (the vehicles they rent).

Paths sit under /api/customer/reports so team permissions apply the existing "reports" module:
viewing needs reports.view, starting an analysis needs reports.create. Drivers never see it.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models as m
from app.database import get_db
from app.offer_history import customer_context

router = APIRouter(prefix="/api/customer/reports", tags=["customer-ai"])


@router.get("/ai-insights")
def customer_ai_insights_latest(p=Depends(customer_context), db: Session = Depends(get_db)):
    """Last stored analysis; null when none was generated yet (no API call here)."""
    from app import ai_assistant

    row = (
        db.query(m.CustomerAiInsight)
        .filter_by(customer_id=p["id"], kind="fleet")
        .order_by(m.CustomerAiInsight.id.desc())
        .first()
    )
    if not row:
        return None
    return ai_assistant.insight_view(row, ai_assistant.fleet_metrics(db, customer_id=p["id"]))


@router.post("/ai-insights")
def customer_ai_insights(
    force: bool = False, p=Depends(customer_context), db: Session = Depends(get_db)
):
    from app import ai_assistant

    if p["role"] == "Görüntüleyici":
        raise HTTPException(403, "AI analizi için rolünüz yetkili değil.")
    return ai_assistant.customer_fleet_insights(db, p["id"], force=force)
