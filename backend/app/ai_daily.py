"""Daily AI fleet analysis at 06:00 Istanbul time for suppliers and customers with a live session.

Each company/day is claimed through a unique row (ai_job_claims for suppliers,
customer_ai_job_claims for customers), so several workers or a restart never analyse the same
fleet twice on one day. A failed run releases its claim and is retried on the next start.
Set FLEETCAR_AI_DAILY=0 to switch the job off.
"""

import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app import models as m
from app.common.time import BUSINESS_TIMEZONE, stamp

JOB = "fleet_insights"
RUN_HOUR = 6
log = logging.getLogger("fleetcar.ai_daily")


@dataclass(frozen=True)
class Spec:
    name: str  # "suppliers" | "customers"
    insight: type
    claim: type
    owner: str  # owner column on insight and claim rows

    def run(self, db, oid):
        from app import ai_assistant

        if self.name == "suppliers":
            return ai_assistant.fleet_insights(db, {"id": oid}, force=True, trigger="daily")
        return ai_assistant.customer_fleet_insights(db, oid, force=True, trigger="daily")


SUPPLIERS = Spec("suppliers", m.SupplierAiInsight, m.AiJobClaim, "supplier_id")
CUSTOMERS = Spec("customers", m.CustomerAiInsight, m.CustomerAiJobClaim, "customer_id")


def local_date(value):
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not moment.tzinfo:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(BUSINESS_TIMEZONE).date()


def active_ids(db, spec):
    now = datetime.now(timezone.utc).isoformat()
    if spec is SUPPLIERS:
        rows = db.query(m.SupplierSession.supplier_id).filter(m.SupplierSession.expires_at > now)
    else:
        rows = db.query(m.PortalSession.subject_id).filter(
            m.PortalSession.kind == "customer", m.PortalSession.expires_at > now
        )
    return sorted({oid for (oid,) in rows.distinct()})


def analysed_today(db, spec, oid, today):
    row = (
        db.query(spec.insight)
        .filter_by(kind="fleet", **{spec.owner: oid})
        .order_by(spec.insight.id.desc())
        .first()
    )
    return bool(row) and local_date(row.created_at) == today


def claim(db, spec, oid, day):
    db.add(spec.claim(job=JOB, run_date=day, started_at=stamp(), **{spec.owner: oid}))
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


def finish(db, spec, oid, day, status):
    row = db.query(spec.claim).filter_by(job=JOB, run_date=day, **{spec.owner: oid}).first()
    if status == "failed":
        db.delete(row)  # release so the next start retries today's run
    else:
        row.status, row.finished_at = status, stamp()
    db.commit()


def run_daily(session_factory, today=None):
    """Analyse every active supplier and customer once for `today`.

    Returns {"suppliers": {id: status}, "customers": {id: status}}.
    """
    today = today or datetime.now(BUSINESS_TIMEZONE).date()
    day = today.isoformat()
    result = {}
    db = session_factory()
    try:
        for spec in (SUPPLIERS, CUSTOMERS):
            statuses = result.setdefault(spec.name, {})
            for oid in active_ids(db, spec):
                if analysed_today(db, spec, oid, today) or not claim(db, spec, oid, day):
                    statuses[oid] = "skipped"
                    continue
                try:
                    spec.run(db, oid)
                    status = "done"
                except HTTPException as exc:  # no active vehicles, missing key, API refusal
                    db.rollback()
                    status = "empty" if exc.status_code == 400 else "failed"
                    log.warning("Daily AI analysis for %s %s: %s", spec.name, oid, exc.detail)
                except Exception:
                    db.rollback()
                    status = "failed"
                    log.exception("Daily AI analysis failed for %s %s", spec.name, oid)
                finish(db, spec, oid, day, status)
                statuses[oid] = status
    finally:
        db.close()
    return result


def seconds_until_next_run(now):
    target = now.replace(hour=RUN_HOUR, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _loop(session_factory):
    while True:
        now = datetime.now(BUSINESS_TIMEZONE)
        if now.hour >= RUN_HOUR:  # covers a server that was down at 06:00
            try:
                run_daily(session_factory, now.date())
            except Exception:
                log.exception("Daily AI analysis run failed")
        time.sleep(max(60, seconds_until_next_run(datetime.now(BUSINESS_TIMEZONE))))


def start(session_factory):
    from app import email_utils  # noqa: F401  (loads backend/.env into os.environ)

    if os.environ.get("FLEETCAR_AI_DAILY", "1").lower() in {"0", "false", "no"}:
        return None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.info("ANTHROPIC_API_KEY is not set; daily AI analysis is off.")
        return None
    thread = threading.Thread(target=_loop, args=(session_factory,), name="ai-daily", daemon=True)
    thread.start()
    return thread
