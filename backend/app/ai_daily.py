"""Daily AI fleet analysis: runs at 06:00 Istanbul time for suppliers with a live session.

Each supplier/day is claimed through a unique row in ai_job_claims, so several workers or a
restart never analyse the same fleet twice on one day. A failed run releases its claim and is
retried on the next start. Set FLEETCAR_AI_DAILY=0 to switch the job off.
"""

import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app import models as m
from app.common.time import BUSINESS_TIMEZONE, stamp

JOB = "fleet_insights"
RUN_HOUR = 6
log = logging.getLogger("fleetcar.ai_daily")


def local_date(value):
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not moment.tzinfo:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(BUSINESS_TIMEZONE).date()


def active_supplier_ids(db):
    now = datetime.now(timezone.utc).isoformat()
    rows = db.query(m.SupplierSession.supplier_id).filter(m.SupplierSession.expires_at > now)
    return sorted({sid for (sid,) in rows.distinct()})


def analysed_today(db, sid, today):
    row = (
        db.query(m.SupplierAiInsight)
        .filter_by(supplier_id=sid, kind="fleet")
        .order_by(m.SupplierAiInsight.id.desc())
        .first()
    )
    return bool(row) and local_date(row.created_at) == today


def claim(db, sid, day):
    db.add(m.AiJobClaim(job=JOB, supplier_id=sid, run_date=day, started_at=stamp()))
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


def finish(db, sid, day, status):
    row = db.query(m.AiJobClaim).filter_by(job=JOB, supplier_id=sid, run_date=day).first()
    if status == "failed":
        db.delete(row)  # release so the next start retries today's run
    else:
        row.status, row.finished_at = status, stamp()
    db.commit()


def run_daily(session_factory, today=None):
    """Analyse every active supplier once for `today`; returns a status per supplier id."""
    from app import ai_assistant

    today = today or datetime.now(BUSINESS_TIMEZONE).date()
    day = today.isoformat()
    result = {}
    db = session_factory()
    try:
        for sid in active_supplier_ids(db):
            if analysed_today(db, sid, today) or not claim(db, sid, day):
                result[sid] = "skipped"
                continue
            try:
                ai_assistant.fleet_insights(db, {"id": sid}, force=True, trigger="daily")
                status = "done"
            except HTTPException as exc:  # no active vehicles, missing key, API refusal
                db.rollback()
                status = "empty" if exc.status_code == 400 else "failed"
                log.warning("Daily AI analysis for supplier %s: %s", sid, exc.detail)
            except Exception:
                db.rollback()
                status = "failed"
                log.exception("Daily AI analysis failed for supplier %s", sid)
            finish(db, sid, day, status)
            result[sid] = status
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
