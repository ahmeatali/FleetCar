"""Notifications for the customer, supplier and service portals.

What each portal hears about is listed once in CATALOG, grouped the way the settings page
shows it. Notices are not written by hand in each endpoint: data changes to the tracked
tables are captured from the ORM session (object changes and the bulk UPDATEs the
optimistic-concurrency paths use), turned into notices by `derive` after the transaction
commits, and delivered in-app and by e-mail according to the account's preferences.
Date-based reminders (inspection, insurance, contract end, due tasks) come from a daily job.

A notice is never sent to the account that made the change; who acted is taken from the
session principal (`remember_actor`, called by portal_access.principal).
"""

from __future__ import annotations

import html
import logging
import os
import sys
import threading
import time
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, attributes

from app import models as m
from app.common.plates import compact_plate
from app.common.time import BUSINESS_TIMEZONE, stamp
from app.database import get_db

log = logging.getLogger(__name__)

SERVICE_TYPES = {"servis", "oto_servis", "lastik", "yol_yardim"}

# ─────────────────── Catalog ────────────────────────────────────────────────
# portal -> groups -> topics. The group is the unit of preference (in-app / e-mail).

CATALOG = {
    "customer": [
        {
            "key": "offers",
            "label": "Teklif ve Sözleşmeler",
            "description": "Gelen kiralama teklifleri, başlayan ve biten sözleşmeler, imza teyitleri.",
            "topics": {
                "offer_received": "Yeni kiralama teklifi",
                "contract_started": "Sözleşme başladı",
                "contract_ending": "Sözleşme bitişi yaklaşıyor",
                "signature_required": "Belge teyidiniz bekleniyor",
                "signature_completed": "Belge teyidi tamamlandı",
            },
        },
        {
            "key": "deliveries",
            "label": "Teslimat, İade ve Rezervasyon",
            "description": "Planlanan ve tamamlanan teslimatlar, iadeler, rezervasyonlar ve atanan araçlar.",
            "topics": {
                "delivery_planned": "Teslimat planlandı",
                "delivery_completed": "Araç teslim edildi",
                "return_planned": "İade planlandı",
                "return_completed": "Araç iadesi tamamlandı",
                "reservation_update": "Rezervasyon güncellendi",
                "vehicle_assigned": "Filonuza araç atandı",
            },
        },
        {
            "key": "service",
            "label": "Servis, Lastik ve Yol Yardım",
            "description": "Taleplerinizin durum değişiklikleri, yol yardım ekibi ve planlanan bakımlar.",
            "topics": {
                "request_update": "Talep durumu değişti",
                "roadside_update": "Yol yardım güncellemesi",
                "maintenance_planned": "Bakım planlandı",
            },
        },
        {
            "key": "damage",
            "label": "Hasar ve Cezalar",
            "description": "Hasar dosyalarındaki gelişmeler ve araçlarınıza yansıyan cezalar.",
            "topics": {"damage_update": "Hasar dosyası güncellendi", "fine_new": "Yeni ceza kaydı"},
        },
        {
            "key": "finance",
            "label": "Fatura ve Ödemeler",
            "description": "Kesilen faturalar ve kaydedilen ödemeler.",
            "topics": {"invoice_issued": "Fatura kesildi", "payment_recorded": "Ödeme kaydedildi"},
        },
        {
            "key": "reminders",
            "label": "Araç Hatırlatmaları",
            "description": "Yaklaşan muayene, sigorta ve servis tarihleri (30, 7 gün kala ve günü gelince).",
            "topics": {
                "inspection_due": "Muayene tarihi yaklaşıyor",
                "insurance_due": "Sigorta bitişi yaklaşıyor",
                "service_due": "Bakım zamanı yaklaşıyor",
            },
        },
        {
            "key": "team",
            "label": "Ekip",
            "description": "Davet ettiğiniz kullanıcıların hesaba katılması.",
            "topics": {"member_joined": "Ekibe yeni kullanıcı katıldı"},
        },
        {
            "key": "ai",
            "label": "AI Önerileri",
            "description": "Her sabah hazırlanan filo analizi.",
            "topics": {"ai_daily": "Günlük AI filo analizi hazır"},
        },
    ],
    "supplier": [
        {
            "key": "sales",
            "label": "Talepler ve Teklifler",
            "description": "Pazaryerine düşen yeni kiralama talepleri ve tekliflerinize verilen kararlar.",
            "topics": {
                "quote_new": "Yeni kiralama talebi",
                "offer_decision": "Teklifinize karar verildi",
                "bid_decision": "Pazaryeri teklifinize karar verildi",
            },
        },
        {
            "key": "approvals",
            "label": "Onaylar",
            "description": "Onayınızı bekleyen kayıtlar ve sonuçlanan onay talepleri.",
            "topics": {
                "approval_requested": "Onay bekleyen kayıt",
                "approval_decided": "Onay talebi sonuçlandı",
            },
        },
        {
            "key": "operations",
            "label": "Operasyon",
            "description": "Yeni rezervasyonlar, yaklaşan teslimat ve iadeler, atanan ve günü gelen görevler.",
            "topics": {
                "reservation_new": "Yeni rezervasyon",
                "delivery_due": "Teslimat günü yaklaştı",
                "return_due": "İade günü yaklaştı",
                "task_assigned": "Görev atandı",
                "task_due": "Görevin günü geldi",
            },
        },
        {
            "key": "contracts",
            "label": "Sözleşme ve İmza",
            "description": "İmza teyitlerindeki ilerleme ve bitişi yaklaşan sözleşmeler.",
            "topics": {
                "signature_progress": "Belge teyidinde ilerleme",
                "contract_ending": "Sözleşme bitişi yaklaşıyor",
            },
        },
        {
            "key": "service",
            "label": "Servis ve Bakım",
            "description": "Filonuzdaki araçların servis talepleri ve sistemin önerdiği bakımlar.",
            "topics": {
                "service_update": "Servis talebinde gelişme",
                "maintenance_proposed": "Bakım önerisi",
            },
        },
        {
            "key": "damage",
            "label": "Hasar ve Cezalar",
            "description": "Bildirilen hasarlar ve yeni ceza kayıtları.",
            "topics": {"damage_reported": "Hasar bildirildi", "fine_new": "Yeni ceza kaydı"},
        },
        {
            "key": "reminders",
            "label": "Araç ve Poliçe Hatırlatmaları",
            "description": "Filonuzdaki araçların muayene ve sigorta tarihleri, bitişi yaklaşan poliçeler.",
            "topics": {
                "inspection_due": "Muayene tarihi yaklaşıyor",
                "insurance_due": "Sigorta bitişi yaklaşıyor",
                "policy_ending": "Poliçe bitişi yaklaşıyor",
            },
        },
        {
            "key": "team",
            "label": "Ekip",
            "description": "Davet ettiğiniz kullanıcıların hesaba katılması.",
            "topics": {"member_joined": "Ekibe yeni kullanıcı katıldı"},
        },
        {
            "key": "ai",
            "label": "AI Önerileri",
            "description": "Her sabah hazırlanan filo analizi.",
            "topics": {"ai_daily": "Günlük AI filo analizi hazır"},
        },
    ],
    "service": [
        {
            "key": "jobs",
            "label": "İş Talepleri",
            "description": "Size atanan yeni işler, yol yardım çağrıları ve mevcut işlerdeki değişiklikler.",
            "topics": {
                "job_new": "Yeni iş talebi",
                "roadside_new": "Yeni yol yardım çağrısı",
                "job_update": "İş talebi güncellendi",
            },
        },
        {
            "key": "team",
            "label": "Ekip",
            "description": "Davet ettiğiniz kullanıcıların hesaba katılması.",
            "topics": {"member_joined": "Ekibe yeni kullanıcı katıldı"},
        },
    ],
}
GROUP_OF = {
    (portal, topic): group["key"]
    for portal, groups in CATALOG.items()
    for group in groups
    for topic in group["topics"]
}

HOME = {"customer": "/dashboard", "supplier": "/supplier-portal", "service": "/service-portal"}
SETTINGS = {
    "customer": "/dashboard/notifications?tab=settings",
    "supplier": "/supplier-portal/notifications?tab=settings",
    "service": "/service-portal/notifications?tab=settings",
}
MANAGERS = {"owner", "Filo Yöneticisi", "fleet_manager"}


def _under_test():
    """Test runs and tests/ fixtures load the real backend/.env; they must never send mail."""
    argv0 = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""
    return "unittest" in argv0 or "pytest" in argv0 or f"{os.sep}tests{os.sep}" in argv0


def email_allowed():
    off = os.environ.get("FLEETCAR_NOTIFY_EMAIL", "1").lower() in {"0", "false", "no"}
    return not off and not _under_test()


def enabled():
    return os.environ.get("FLEETCAR_NOTIFICATIONS", "1").lower() not in {"0", "false", "no"}


# ─────────────────── Change capture ─────────────────────────────────────────

TRACKED = {
    "supplier_operations": (m.SupplierOperation, "status"),
    "requests": (m.Request, "status"),
    "supplier_bids": (m.SupplierBid, "status"),
    "quotes": (m.Quote, "status"),
    "signature_envelopes": (m.SignatureEnvelope, "status"),
    "roadside_cases": (m.RoadsideCase, "status"),
    "fleet_tasks": (m.FleetTask, "assignee_id"),
    "fleet_reservations": (m.FleetReservation, "status"),
    "team_invitations": (m.TeamInvitation, "accepted_at"),
    "vehicles": (m.Vehicle, "customer_id"),
    "customer_ai_insights": (m.CustomerAiInsight, None),
    "supplier_ai_insights": (m.SupplierAiInsight, None),
}
MODEL_TABLE = {model: table for table, (model, _) in TRACKED.items()}
# Envelope attestations change without a status change; watch them as well.
EXTRA_FIELDS = {"signature_envelopes": "attestations"}


def remember_actor(db, who):
    """Record who is acting on this session, so the actor's own account is not notified."""
    try:
        db.info["fr_actor"] = (
            {"kind": who.get("kind"), "id": who.get("id")} if isinstance(who, dict) else None
        )
    except AttributeError:
        pass
    return who


def _row(obj):
    return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}


def _queue(session, table, row, new, field=None, old=None):
    session.info.setdefault("fr_events", []).append(
        {
            "table": table,
            "row": row,
            "new": new,
            "field": field,
            "old": old,
            "actor": session.info.get("fr_actor"),
        }
    )


@event.listens_for(Session, "before_flush")
def _before_flush(session, flush_context, instances):
    if session.info.get("fr_off") or not enabled():
        return
    pending = session.info.setdefault("fr_pending", [])
    for obj in session.new:
        table = MODEL_TABLE.get(type(obj))
        if table:
            pending.append((table, obj, True, None, None))
    for obj in session.dirty:
        table = MODEL_TABLE.get(type(obj))
        if not table:
            continue
        for field in (TRACKED[table][1], EXTRA_FIELDS.get(table)):
            if not field:
                continue
            history = attributes.get_history(obj, field)
            if history.has_changes():
                old = history.deleted[0] if history.deleted else None
                pending.append((table, obj, False, field, old))


@event.listens_for(Session, "after_flush")
def _after_flush(session, flush_context):
    for table, obj, new, field, old in session.info.pop("fr_pending", []):
        _queue(session, table, _row(obj), new, field, old)


@event.listens_for(Session, "do_orm_execute")
def _bulk_update(state):
    """Status changes made with query(...).update(...): compare the rows before and after."""
    session = state.session
    if not state.is_update or session.info.get("fr_off") or not enabled():
        return None
    statement = state.statement
    table_obj = getattr(statement, "table", None)
    table = getattr(table_obj, "name", None)
    if table not in TRACKED:
        return None
    fields = [f for f in (TRACKED[table][1], EXTRA_FIELDS.get(table)) if f]
    if not fields:
        return None
    columns = TRACKED[table][0].__table__.c
    where = statement.whereclause
    query = select(TRACKED[table][0].__table__)
    before = {
        r["id"]: dict(r)
        for r in session.execute(query.where(where) if where is not None else query).mappings()
    }
    result = state.invoke_statement()
    if before:
        after = session.execute(query.where(columns.id.in_(list(before)))).mappings()
        for row in after:
            row = dict(row)
            for field in fields:
                if row.get(field) != before[row["id"]].get(field):
                    _queue(session, table, row, False, field, before[row["id"]].get(field))
    return result


@event.listens_for(Session, "before_commit")
def _before_commit(session):
    """Turn this transaction's changes into notices, stored in the same transaction."""
    if session.info.get("fr_off") or not enabled():
        return
    if session.new or session.dirty:
        session.flush()  # capture changes the commit would otherwise flush after this hook
    events = session.info.pop("fr_events", [])
    if not events:
        return
    session.info["fr_off"] = True  # rule lookups and stored notices are not changes to watch
    try:
        notices = []
        for ev in events:
            try:
                notices.extend(derive(session, ev))
            except Exception:
                log.exception("Notification rule failed for %s", ev.get("table"))
        if notices:
            session.info.setdefault("fr_mail", []).extend(store(session, notices))
    except Exception:  # a notice must never break the user's action
        log.exception("Notification processing failed")
    finally:
        session.info.pop("fr_off", None)


@event.listens_for(Session, "after_commit")
def _after_commit(session):
    jobs = session.info.pop("fr_mail", [])
    if jobs:
        send_later(session.get_bind(), jobs)


@event.listens_for(Session, "after_rollback")
def _after_rollback(session):
    for key in ("fr_events", "fr_pending", "fr_mail"):
        session.info.pop(key, None)


# ─────────────────── Rules: change -> notices ───────────────────────────────


def _notice(
    portal, tenant_id, topic, title, body="", link=None, plate=None, key=None, self_ok=False
):
    return {
        "portal": portal,
        "tenant_id": tenant_id,
        "topic": topic,
        "title": title,
        "body": body,
        "link": link,
        "plate": plate,
        "dedupe_key": key,
        "self_ok": self_ok,
    }


def _supplier_portal(db, supplier_id):
    supplier = db.get(m.Supplier, supplier_id) if supplier_id else None
    if not supplier:
        return None
    return "service" if supplier.type in SERVICE_TYPES else "supplier"


def _plate(db, vehicle_id):
    vehicle = db.get(m.Vehicle, vehicle_id) if vehicle_id else None
    return vehicle.plate if vehicle else None


def _tr_date(value):
    try:
        return datetime.fromisoformat(str(value)[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return str(value or "")


def _money(value):
    try:
        return f"₺{float(value):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return ""


def _operation(db, ev):
    r = dict(ev["row"])
    # Numbers are assigned after the first insert ("pending-…"); read the row as it is now.
    current = db.get(m.SupplierOperation, r["id"])
    if current is not None:
        r.update(number=current.number, title=current.title)
    kind, status, new = r["kind"], r["status"], ev["new"]
    sid, cid = r["supplier_id"], r["customer_id"]
    plate = _plate(db, r["vehicle_id"])
    label = f"{r['number']} · {r['title']}"
    on_plate = f"{plate} · " if plate else ""
    status_changed = new or ev["field"] == "status"
    out = []
    if not status_changed:
        return out
    if kind == "offer":
        if status == "Beklemede" and cid:
            body = f"{r['title']} — aylık {_money(r['amount'])}. Teklifi inceleyip karar verebilirsiniz."
            out.append(
                _notice(
                    "customer",
                    cid,
                    "offer_received",
                    "Yeni kiralama teklifi",
                    body,
                    "/dashboard/quotes",
                )
            )
        elif status in {"Onaylandı", "Reddedildi", "Revizyon Bekliyor"} and not new:
            out.append(
                _notice(
                    "supplier",
                    sid,
                    "offer_decision",
                    f"Teklif {status.lower()}: {r['number']}",
                    r["title"],
                    "/supplier-portal/offers",
                )
            )
    elif kind == "contract" and status == "Aktif" and cid:
        body = f"{r['title']} · {_tr_date(r['date'])} – {_tr_date(r['end_date'])}"
        out.append(
            _notice(
                "customer",
                cid,
                "contract_started",
                "Sözleşmeniz başladı",
                body,
                "/dashboard/quotes",
            )
        )
    elif kind in {"delivery", "return"} and cid:
        noun = "Teslimat" if kind == "delivery" else "İade"
        if status == "Planlandı":
            topic = "delivery_planned" if kind == "delivery" else "return_planned"
            out.append(
                _notice(
                    "customer",
                    cid,
                    topic,
                    f"{noun} planlandı",
                    f"{on_plate}{_tr_date(r['date'])} · {r['title']}",
                    "/dashboard/vehicles",
                    plate,
                )
            )
        elif status == "Tamamlandı":
            topic = "delivery_completed" if kind == "delivery" else "return_completed"
            title = "Araç teslim edildi" if kind == "delivery" else "Araç iadesi tamamlandı"
            out.append(
                _notice(
                    "customer",
                    cid,
                    topic,
                    title,
                    f"{on_plate}{r['title']}",
                    "/dashboard/vehicles",
                    plate,
                )
            )
    elif kind == "damage":
        if new:
            out.append(
                _notice(
                    "supplier",
                    sid,
                    "damage_reported",
                    "Hasar bildirildi",
                    f"{on_plate}{label}",
                    "/supplier-portal/damage",
                    plate,
                )
            )
        if cid:
            out.append(
                _notice(
                    "customer",
                    cid,
                    "damage_update",
                    f"Hasar dosyası: {status}",
                    f"{on_plate}{label}",
                    "/dashboard/service-management?tab=damage",
                    plate,
                )
            )
    elif kind == "fine" and new:
        body = f"{on_plate}{r['title']} · {_money(r['amount'])}"
        out.append(
            _notice(
                "supplier",
                sid,
                "fine_new",
                "Yeni ceza kaydı",
                body,
                "/supplier-portal/fines",
                plate,
            )
        )
        if cid:
            out.append(
                _notice(
                    "customer", cid, "fine_new", "Aracınıza ceza kaydı", body, "/dashboard", plate
                )
            )
    elif kind == "invoice" and status == "Kesildi" and cid:
        out.append(
            _notice(
                "customer",
                cid,
                "invoice_issued",
                "Faturanız kesildi",
                f"{r['number']} · {_money(r['amount'])}",
                "/dashboard",
            )
        )
    elif kind == "payment" and new and cid:
        out.append(
            _notice(
                "customer",
                cid,
                "payment_recorded",
                "Ödemeniz kaydedildi",
                f"{r['number']} · {_money(r['amount'])}",
                "/dashboard",
            )
        )
    elif kind == "approval":
        # Approvals go to colleagues in the same account, so the actor's account is notified.
        if new:
            out.append(
                _notice(
                    "supplier",
                    sid,
                    "approval_requested",
                    "Onay bekleyen kayıt",
                    f"{r['title']} · {_money(r['amount'])}",
                    "/supplier-portal/approvals",
                    self_ok=True,
                )
            )
        elif status in {"Onaylandı", "Reddedildi"}:
            out.append(
                _notice(
                    "supplier",
                    sid,
                    "approval_decided",
                    f"Onay talebi {status.lower()}",
                    r["title"],
                    "/supplier-portal/approvals",
                    self_ok=True,
                )
            )
    elif kind == "maintenance":
        if new and status == "Önerildi":
            out.append(
                _notice(
                    "supplier",
                    sid,
                    "maintenance_proposed",
                    "Bakım önerisi",
                    f"{on_plate}{r['title']}",
                    "/supplier-portal/maintenance",
                    plate,
                )
            )
        elif status == "Planlandı" and cid:
            out.append(
                _notice(
                    "customer",
                    cid,
                    "maintenance_planned",
                    "Bakım planlandı",
                    f"{on_plate}{_tr_date(r['date'])} · {r['title']}",
                    "/dashboard/service-management",
                    plate,
                )
            )
    return out


REQUEST_NAMES = {
    "servis": "Servis",
    "lastik": "Lastik",
    "yol_yardim": "Yol yardım",
    "ikame_arac": "İkame araç",
}


def _request(db, ev):
    r = ev["row"]
    vehicle = db.get(m.Vehicle, r["vehicle_id"]) if r["vehicle_id"] else None
    plate = vehicle.plate if vehicle else None
    name = REQUEST_NAMES.get(r["type"], "Hizmet")
    summary = f"{plate + ' · ' if plate else ''}{name} talebi #{r['id']}"
    desc = (r.get("description") or "").strip()
    body = f"{summary}{' — ' + desc[:140] if desc else ''}"
    provider = _supplier_portal(db, r["supplier_id"])
    out = []
    if ev["new"]:
        if provider == "service":
            out.append(
                _notice(
                    "service",
                    r["supplier_id"],
                    "job_new",
                    f"Yeni {name.lower()} talebi",
                    body,
                    "/service-portal",
                    plate,
                )
            )
        if vehicle and vehicle.supplier_id and vehicle.supplier_id != r["supplier_id"]:
            out.append(
                _notice(
                    "supplier",
                    vehicle.supplier_id,
                    "service_update",
                    f"Yeni {name.lower()} talebi",
                    body,
                    "/supplier-portal/service",
                    plate,
                )
            )
        return out
    if ev["field"] != "status":
        return out
    status = r["status"]
    title = f"{name} talebi: {status}"
    if vehicle and vehicle.customer_id:
        out.append(
            _notice(
                "customer",
                vehicle.customer_id,
                "request_update",
                title,
                summary,
                f"/dashboard/requests?type=list&request_id={r['id']}",
                plate,
            )
        )
    if vehicle and vehicle.supplier_id and vehicle.supplier_id != r["supplier_id"]:
        out.append(
            _notice(
                "supplier",
                vehicle.supplier_id,
                "service_update",
                title,
                summary,
                "/supplier-portal/service",
                plate,
            )
        )
    if provider == "service":
        out.append(
            _notice(
                "service", r["supplier_id"], "job_update", title, summary, "/service-portal", plate
            )
        )
    return out


def _roadside(db, ev):
    r = ev["row"]
    plate = _plate(db, r["vehicle_id"])
    vehicle = db.get(m.Vehicle, r["vehicle_id"]) if r["vehicle_id"] else None
    request = db.get(m.Request, r["request_id"]) if r["request_id"] else None
    where = f" · {r['location']}" if r.get("location") else ""
    out = []
    if ev["new"]:
        if request and _supplier_portal(db, request.supplier_id) == "service":
            out.append(
                _notice(
                    "service",
                    request.supplier_id,
                    "roadside_new",
                    "Yeni yol yardım çağrısı",
                    f"{plate or ''} · {r['incident'] or 'Yol yardım'}{where}",
                    "/service-portal",
                    plate,
                )
            )
        return out
    if vehicle and vehicle.customer_id:
        eta = f" · tahmini varış {r['eta_minutes']} dk" if r.get("eta_minutes") else ""
        out.append(
            _notice(
                "customer",
                vehicle.customer_id,
                "roadside_update",
                f"Yol yardım: {r['status']}",
                f"{plate or ''} · {r['case_no']}{eta}",
                "/dashboard/roadside",
                plate,
            )
        )
    return out


def _bid(db, ev):
    r = ev["row"]
    if ev["new"] or r["status"] not in {"Onaylandı", "Kabul Edildi", "Reddedildi"}:
        return []
    word = "reddedildi" if r["status"] == "Reddedildi" else "kabul edildi"
    return [
        _notice(
            "supplier",
            r["supplier_id"],
            "bid_decision",
            f"Pazaryeri teklifiniz {word}",
            f"Talep #{r['quote_id']} · aylık {_money(r['monthly_price_try'])}",
            "/supplier-portal/marketplace",
        )
    ]


def _quote(db, ev):
    r = ev["row"]
    if not ev["new"]:
        return []
    body = (
        f"{r['vehicle_count'] or ''} araç · {r['vehicle_segment'] or ''} segment "
        f"{r['vehicle_type'] or ''} · {r['duration_months'] or ''} ay"
    ).strip()
    suppliers = db.query(m.Supplier.id, m.Supplier.type).all()
    return [
        _notice(
            "supplier",
            sid,
            "quote_new",
            "Yeni kiralama talebi",
            body,
            "/supplier-portal/marketplace",
        )
        for sid, kind in suppliers
        if kind not in SERVICE_TYPES
    ]


def _envelope(db, ev):
    r = ev["row"]
    op = db.get(m.SupplierOperation, r["operation_id"])
    what = f"{op.number} · {op.title}" if op else f"Belge #{r['id']}"
    parties = r.get("required_parties") or []
    signed = r.get("attestations") or {}
    out = []
    if r["status"] == "Teyit Edildi" and (ev["new"] or ev["field"] == "status"):
        out.append(
            _notice(
                "customer",
                r["customer_id"],
                "signature_completed",
                "Belge teyidi tamamlandı",
                what,
                "/dashboard/quotes",
            )
        )
        out.append(
            _notice(
                "supplier",
                r["supplier_id"],
                "signature_progress",
                "Belge teyidi tamamlandı",
                what,
                "/supplier-portal/contracts",
            )
        )
        return out
    if r["status"] != "Teyit Bekliyor":
        return out
    if (
        "customer" in parties
        and "customer" not in signed
        and (ev["new"] or ev["field"] == "attestations")
    ):
        out.append(
            _notice(
                "customer",
                r["customer_id"],
                "signature_required",
                "Belge teyidiniz bekleniyor",
                f"{what} — imzalı belgeyi ve şartları kontrol edip teyit edin.",
                "/dashboard/quotes",
                key=f"envelope:{r['id']}:customer",
            )
        )
    if not ev["new"] and ev["field"] == "attestations":
        before = ev.get("old") or {}
        names = {"customer": "Müşteri", "platform": "FleetRent", "supplier": "Kiralayan firma"}
        for party in signed:
            if party not in before and party != "supplier":
                out.append(
                    _notice(
                        "supplier",
                        r["supplier_id"],
                        "signature_progress",
                        f"{names.get(party, party)} belgeyi teyit etti",
                        what,
                        "/supplier-portal/contracts",
                    )
                )
    return out


def _task(db, ev):
    r = ev["row"]
    if not r.get("assignee_id"):
        return []
    user = db.get(m.SupplierPortalUser, r["assignee_id"])
    who = f" · {user.name}" if user else ""
    return [
        _notice(
            "supplier",
            r["supplier_id"],
            "task_assigned",
            "Görev atandı",
            f"{r['title']}{who} · son gün {_tr_date(r['due_date'])}",
            "/supplier-portal/operations",
            _plate(db, r.get("vehicle_id")),
            self_ok=True,
        )
    ]


def _reservation(db, ev):
    r = ev["row"]
    plate = _plate(db, r["vehicle_id"])
    span = (
        f"{plate + ' · ' if plate else ''}{_tr_date(r['start_date'])} – {_tr_date(r['end_date'])}"
    )
    out = []
    if ev["new"]:
        out.append(
            _notice(
                "supplier",
                r["supplier_id"],
                "reservation_new",
                "Yeni rezervasyon",
                span,
                "/supplier-portal/reservations",
                plate,
            )
        )
    if r.get("customer_id"):
        out.append(
            _notice(
                "customer",
                r["customer_id"],
                "reservation_update",
                f"Rezervasyon: {r['status']}",
                span,
                "/dashboard/vehicles",
                plate,
            )
        )
    return out


def _invitation(db, ev):
    r = ev["row"]
    if not r.get("accepted_at") or ev["old"]:
        return []
    portal = r["portal"]
    if portal == "supplier":
        portal = _supplier_portal(db, r["tenant_id"]) or "supplier"
        user = db.get(m.SupplierPortalUser, r["user_id"])
    else:
        user = db.get(m.CustomerPortalUser, r["user_id"])
    name = user.name if user else "Yeni kullanıcı"
    link = "/dashboard/users" if portal == "customer" else "/supplier-portal/users"
    return [
        _notice(
            portal,
            r["tenant_id"],
            "member_joined",
            "Ekibe yeni kullanıcı katıldı",
            f"{name} hesabını etkinleştirdi.",
            link,
            self_ok=True,
        )
    ]


def _vehicle(db, ev):
    r = ev["row"]
    if ev["new"] or not r.get("customer_id") or ev["old"] == r["customer_id"]:
        return []
    model = " ".join(x for x in (r.get("brand"), r.get("model")) if x)
    return [
        _notice(
            "customer",
            r["customer_id"],
            "vehicle_assigned",
            "Filonuza araç atandı",
            f"{r['plate']} · {model}",
            f"/dashboard/vehicles/{r['id']}",
            r["plate"],
        )
    ]


def _insight(db, ev, portal, owner):
    r = ev["row"]
    if not ev["new"] or (r.get("usage") or {}).get("trigger") != "daily":
        return []
    link = "/dashboard" if portal == "customer" else "/supplier-portal"
    return [
        _notice(
            portal,
            r[owner],
            "ai_daily",
            "Günlük AI filo analizi hazır",
            "Bu sabahki analizde öne çıkan önerileri ana sayfada görebilirsiniz.",
            link,
            key=f"ai:{(r.get('created_at') or '')[:10]}",
            self_ok=True,
        )
    ]


RULES = {
    "supplier_operations": _operation,
    "requests": _request,
    "roadside_cases": _roadside,
    "supplier_bids": _bid,
    "quotes": _quote,
    "signature_envelopes": _envelope,
    "fleet_tasks": _task,
    "fleet_reservations": _reservation,
    "team_invitations": _invitation,
    "vehicles": _vehicle,
    "customer_ai_insights": lambda db, ev: _insight(db, ev, "customer", "customer_id"),
    "supplier_ai_insights": lambda db, ev: _insight(db, ev, "supplier", "supplier_id"),
}


def derive(db, ev):
    notices = RULES[ev["table"]](db, ev)
    actor = ev.get("actor") or {}
    kind = actor.get("kind")
    out = []
    for n in notices:
        if not n["tenant_id"] or (n["portal"], n["topic"]) not in GROUP_OF:
            continue
        own = (
            kind == n["portal"] or (kind == "service" and n["portal"] == "supplier")
        ) and actor.get("id") == n["tenant_id"]
        if own and not n["self_ok"]:
            continue
        out.append(n)
    return out


# ─────────────────── Delivery ───────────────────────────────────────────────


def preferences(db, portal, tenant_id):
    rows = db.query(m.NotificationPreference).filter_by(portal=portal, tenant_id=tenant_id).all()
    saved = {r.group_key: r for r in rows}
    return {
        g["key"]: {
            "in_app": saved[g["key"]].in_app if g["key"] in saved else True,
            "email": saved[g["key"]].email if g["key"] in saved else True,
        }
        for g in CATALOG[portal]
    }


RESERVED_DOMAINS = ("example.com", "example.net", "example.org")
RESERVED_SUFFIXES = (".test", ".example", ".invalid", ".localhost")


def _deliverable(address):
    """Never mail reserved test domains (fixtures, demos)."""
    domain = address.rsplit("@", 1)[-1].lower()
    return (
        "@" in address and domain not in RESERVED_DOMAINS and not domain.endswith(RESERVED_SUFFIXES)
    )


def _address(db, portal, tenant_id):
    owner = db.get(m.Customer, tenant_id) if portal == "customer" else db.get(m.Supplier, tenant_id)
    return (getattr(owner, "email", None) or "").strip() or None


def _recipient(db, portal, tenant_id):
    owner = db.get(m.Customer, tenant_id) if portal == "customer" else db.get(m.Supplier, tenant_id)
    address = (getattr(owner, "email", None) or "").strip()
    return address if address and _deliverable(address) else None


def _email_html(portal, title, body, link):
    base = os.environ.get("APP_BASE_URL", "https://fleetrent.com.tr").rstrip("/")
    target = base + (link or HOME[portal])
    settings = base + SETTINGS[portal]
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;background:#f3f6fa;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#10254c">
<div style="max-width:560px;margin:24px auto;background:#fff;border:1px solid #dfe7f1;border-radius:12px;overflow:hidden">
<div style="padding:18px 24px;background:#0b1a33;color:#fff;font-weight:700;font-size:18px">FleetRent</div>
<div style="padding:24px">
<h1 style="margin:0 0 10px;font-size:20px;line-height:1.3">{html.escape(title)}</h1>
<p style="margin:0 0 20px;font-size:15px;line-height:1.55;color:#33476a">{html.escape(body)}</p>
<a href="{html.escape(target)}" style="display:inline-block;padding:11px 20px;background:#0064ff;color:#fff;
text-decoration:none;border-radius:8px;font-weight:600">FleetRent'te aç</a>
</div>
<div style="padding:14px 24px;background:#f6f9fc;font-size:12px;color:#5a6e90">
Bu e-postayı bildirim ayarlarınız nedeniyle aldınız.
<a href="{html.escape(settings)}" style="color:#0052d4">Bildirim ayarlarını yönet</a>
</div></div></body></html>"""


def _email_config():
    from app import email_utils

    email_utils._load_env_file()
    cfg = {
        "smtp_host": os.environ.get("SMTP_HOST", "").strip(),
        "smtp_user": os.environ.get("SMTP_USER", "").strip(),
        "smtp_pass": os.environ.get("SMTP_PASS", "").strip(),
        "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
        "smtp_from": os.environ.get("SMTP_FROM", "noreply@fleetrent.com.tr").strip(),
    }
    ok = email_utils._email_transport_configured(
        cfg["smtp_host"], cfg["smtp_user"], cfg["smtp_pass"]
    )
    return cfg, ok


def _send_emails(bind, jobs):
    from app import email_utils

    cfg, _ = _email_config()
    for nid, recipient, subject, body in jobs:
        try:
            email_utils._send_message(recipient, subject, body, **cfg)
            status = "sent"
        except Exception as error:  # delivery problems are logged on the notice, not raised
            log.warning("Notification e-mail failed: %s", email_utils._email_error_message(error))
            status = "failed"
        db = Session(bind=bind)
        db.info["fr_off"] = True
        try:
            db.query(m.Notification).filter_by(id=nid).update({"email_status": status})
            db.commit()
        finally:
            db.close()


def store(db, notices):
    """Add notices to the session (skipping duplicates); returns the e-mails to send after commit."""
    jobs = []
    email_on = email_allowed()
    cfg_ok = None
    for n in notices:
        group = GROUP_OF[(n["portal"], n["topic"])]
        prefs = preferences(db, n["portal"], n["tenant_id"])[group]
        if not prefs["in_app"] and not prefs["email"]:
            continue
        if n["dedupe_key"] and (
            db.query(m.Notification.id)
            .filter_by(portal=n["portal"], tenant_id=n["tenant_id"], dedupe_key=n["dedupe_key"])
            .first()
        ):
            continue
        row = m.Notification(
            portal=n["portal"],
            tenant_id=n["tenant_id"],
            topic=n["topic"],
            title=n["title"][:200],
            body=(n["body"] or "")[:1000],
            link=n["link"],
            plate=n["plate"],
            dedupe_key=n["dedupe_key"],
            created_at=stamp(),
            # A group shown only by e-mail is kept for history but starts as read.
            read_at=None if prefs["in_app"] else stamp(),
        )
        recipient = _recipient(db, n["portal"], n["tenant_id"]) if prefs["email"] else None
        if not prefs["email"] or not email_on:
            row.email_status = "off"
        elif not recipient:
            row.email_status = "no_address"
        else:
            if cfg_ok is None:
                cfg_ok = _email_config()[1]
            row.email_status = "queued" if cfg_ok else "not_configured"
        try:
            with (
                db.begin_nested()
            ):  # a duplicate reminder from another worker must not undo the rest
                db.add(row)
                db.flush()
        except IntegrityError:
            continue
        if row.email_status == "queued":
            jobs.append(
                (
                    row.id,
                    recipient,
                    f"FleetRent · {row.title}",
                    _email_html(row.portal, row.title, row.body, row.link),
                )
            )
    return jobs


def send_later(bind, jobs):
    threading.Thread(
        target=_send_emails, args=(bind, jobs), name="notify-mail", daemon=True
    ).start()


def deliver(db, notices):
    """Store notices in their own transaction and send the e-mails. Returns how many were stored."""
    before = db.query(m.Notification.id).count()
    jobs = store(db, notices)
    db.commit()
    if jobs:
        send_later(db.get_bind(), jobs)
    return db.query(m.Notification.id).count() - before


# ─────────────────── Daily reminders ────────────────────────────────────────

REMINDER_DAYS = (30, 7, 0)


def _days_left(value, today):
    try:
        return (date.fromisoformat(str(value)[:10]) - today).days
    except ValueError:
        return None


def _bucket(days, thresholds=REMINDER_DAYS):
    """The smallest threshold already reached, so each one fires once (30, 7, then on the day)."""
    if days is None or days < -1:
        return None
    reached = [t for t in thresholds if days <= t]
    return min(reached) if reached else None


def _when(days):
    if days < 0:
        return "süresi geçti"
    if days == 0:
        return "bugün"
    return f"{days} gün kaldı"


def reminders(db, today=None):
    today = today or datetime.now(BUSINESS_TIMEZONE).date()
    out = []
    for v in db.query(m.Vehicle).filter(m.Vehicle.is_active.isnot(False)).all():
        owners = [
            ("customer", v.customer_id, f"/dashboard/vehicles/{v.id}"),
            ("supplier", v.supplier_id, f"/supplier-portal/vehicles/{v.id}"),
        ]
        checks = [
            ("inspection_due", v.inspection_date, "Muayene"),
            ("insurance_due", v.traffic_insurance_expiry_date, "Trafik sigortası"),
            ("insurance_due", v.casco_insurance_expiry_date, "Kasko"),
        ]
        for topic, value, label in checks:
            days = _days_left(value, today)
            bucket = _bucket(days)
            if bucket is None:
                continue
            for portal, tenant, link in owners:
                if not tenant or (
                    portal == "supplier" and _supplier_portal(db, tenant) != "supplier"
                ):
                    continue
                out.append(
                    _notice(
                        portal,
                        tenant,
                        topic,
                        f"{label}: {_when(days)}",
                        f"{v.plate} · {label.lower()} tarihi {_tr_date(value)}",
                        link,
                        v.plate,
                        key=f"{topic}:{label}:{v.id}:{value}:{bucket}",
                    )
                )
        days = _days_left(v.next_service_due_date, today)
        bucket = _bucket(days, (14, 3, 0))
        if bucket is not None and v.customer_id:
            out.append(
                _notice(
                    "customer",
                    v.customer_id,
                    "service_due",
                    f"Bakım zamanı: {_when(days)}",
                    f"{v.plate} · planlı bakım {_tr_date(v.next_service_due_date)}",
                    f"/dashboard/vehicles/{v.id}",
                    v.plate,
                    key=f"service_due:{v.id}:{v.next_service_due_date}:{bucket}",
                )
            )
    ops = (
        db.query(m.SupplierOperation)
        .filter(m.SupplierOperation.status.in_(["Aktif", "Planlandı"]))
        .all()
    )
    for op in ops:
        if op.kind == "contract" and op.status == "Aktif":
            days = _days_left(op.end_date, today)
            bucket = _bucket(days)
            if bucket is None:
                continue
            body = f"{op.number} · {op.title} · bitiş {_tr_date(op.end_date)}"
            key = f"contract_ending:{op.id}:{op.end_date}:{bucket}"
            out.append(
                _notice(
                    "supplier",
                    op.supplier_id,
                    "contract_ending",
                    f"Sözleşme bitişi: {_when(days)}",
                    body,
                    "/supplier-portal/contracts",
                    key=key,
                )
            )
            if op.customer_id:
                out.append(
                    _notice(
                        "customer",
                        op.customer_id,
                        "contract_ending",
                        f"Sözleşme bitişi: {_when(days)}",
                        body,
                        "/dashboard/quotes",
                        key=key,
                    )
                )
        elif op.kind == "policy" and op.status == "Aktif":
            days = _days_left(op.end_date, today)
            bucket = _bucket(days)
            if bucket is not None:
                out.append(
                    _notice(
                        "supplier",
                        op.supplier_id,
                        "policy_ending",
                        f"Poliçe bitişi: {_when(days)}",
                        f"{op.number} · {op.title} · bitiş {_tr_date(op.end_date)}",
                        "/supplier-portal/policies",
                        _plate(db, op.vehicle_id),
                        key=f"policy_ending:{op.id}:{op.end_date}:{bucket}",
                    )
                )
        elif op.kind in {"delivery", "return"} and op.status == "Planlandı":
            days = _days_left(op.date, today)
            if days in (0, 1):
                topic = "delivery_due" if op.kind == "delivery" else "return_due"
                noun = "Teslimat" if op.kind == "delivery" else "İade"
                plate = _plate(db, op.vehicle_id)
                out.append(
                    _notice(
                        "supplier",
                        op.supplier_id,
                        topic,
                        f"{noun} {'bugün' if days == 0 else 'yarın'}",
                        f"{plate + ' · ' if plate else ''}{op.number} · {op.title}",
                        (
                            "/supplier-portal/deliveries"
                            if op.kind == "delivery"
                            else "/supplier-portal/returns"
                        ),
                        plate,
                        key=f"{topic}:{op.id}:{op.date}",
                    )
                )
    for task in db.query(m.FleetTask).filter(m.FleetTask.status != "Tamamlandı").all():
        days = _days_left(task.due_date, today)
        if days is not None and days <= 0:
            out.append(
                _notice(
                    "supplier",
                    task.supplier_id,
                    "task_due",
                    "Görevin günü geldi" if days == 0 else "Görevin günü geçti",
                    f"{task.title} · son gün {_tr_date(task.due_date)}",
                    "/supplier-portal/operations",
                    key=f"task_due:{task.id}:{task.due_date}",
                )
            )
    return out


def run_reminders(bind, today=None):
    db = Session(bind=bind)
    db.info["fr_off"] = True
    try:
        return deliver(db, reminders(db, today))
    finally:
        db.close()


REMINDER_HOUR = 7


def _reminder_loop(bind):
    while True:
        now = datetime.now(BUSINESS_TIMEZONE)
        if now.hour >= REMINDER_HOUR:
            try:
                run_reminders(bind, now.date())
            except Exception:
                log.exception("Daily notification reminders failed")
        target = now.replace(hour=REMINDER_HOUR, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        time.sleep(max(60, (target - datetime.now(BUSINESS_TIMEZONE)).total_seconds()))


def start(session_factory):
    """Daily reminders at 07:00 Istanbul time. FLEETCAR_NOTIFICATIONS=0 turns notifications off."""
    if not enabled():
        return None
    bind = session_factory.kw.get("bind") if hasattr(session_factory, "kw") else None
    if bind is None:
        return None
    thread = threading.Thread(target=_reminder_loop, args=(bind,), name="notify-daily", daemon=True)
    thread.start()
    return thread


# ─────────────────── API ────────────────────────────────────────────────────

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def _who(request, db):
    from app.portal_access import principal

    p = principal(request, db)
    if p["kind"] not in CATALOG:
        raise HTTPException(403, "Bu hesap için bildirim yok.")
    return p


def _visible(db, p):
    prefs = preferences(db, p["kind"], p["id"])
    hidden = [
        topic for g in CATALOG[p["kind"]] if not prefs[g["key"]]["in_app"] for topic in g["topics"]
    ]
    q = db.query(m.Notification).filter_by(portal=p["kind"], tenant_id=p["id"])
    if hidden:
        q = q.filter(m.Notification.topic.notin_(hidden))
    return q


def _for_driver(rows, p):
    plate = p.get("plate")
    if not plate:
        return rows
    mine = compact_plate(plate)
    return [r for r in rows if r.plate and compact_plate(r.plate) == mine]


def _view(row, portal):
    group = GROUP_OF.get((portal, row.topic))
    label = next((g["label"] for g in CATALOG[portal] if g["key"] == group), "")
    return {
        "id": row.id,
        "topic": row.topic,
        "group": group,
        "group_label": label,
        "title": row.title,
        "body": row.body,
        "link": row.link,
        "plate": row.plate,
        "created_at": row.created_at,
        "read": bool(row.read_at),
        "email_status": row.email_status,
    }


@router.get("")
def list_notifications(
    request: Request, limit: int = 50, unread: bool = False, db: Session = Depends(get_db)
):
    p = _who(request, db)
    q = _visible(db, p)
    if unread:
        q = q.filter(m.Notification.read_at.is_(None))
    rows = _for_driver(
        q.order_by(m.Notification.id.desc())
        .limit(max(1, min(limit, 200)) * (4 if p.get("plate") else 1))
        .all(),
        p,
    )
    unread_rows = _for_driver(_visible(db, p).filter(m.Notification.read_at.is_(None)).all(), p)
    return {"items": [_view(r, p["kind"]) for r in rows[:limit]], "unread": len(unread_rows)}


@router.post("/{nid}/read")
def mark_read(nid: int, request: Request, db: Session = Depends(get_db)):
    p = _who(request, db)
    row = db.query(m.Notification).filter_by(id=nid, portal=p["kind"], tenant_id=p["id"]).first()
    if not row:
        raise HTTPException(404, "Bildirim bulunamadı.")
    row.read_at = row.read_at or stamp()
    db.commit()
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(request: Request, db: Session = Depends(get_db)):
    p = _who(request, db)
    rows = _for_driver(_visible(db, p).filter(m.Notification.read_at.is_(None)).all(), p)
    now = stamp()
    for row in rows:
        row.read_at = now
    db.commit()
    return {"ok": True, "count": len(rows)}


@router.get("/preferences")
def get_preferences(request: Request, db: Session = Depends(get_db)):
    p = _who(request, db)
    prefs = preferences(db, p["kind"], p["id"])
    _, configured = _email_config()
    return {
        "can_edit": p.get("role") in MANAGERS,
        "email": _address(db, p["kind"], p["id"]),
        "email_configured": configured,
        "groups": [
            {
                "key": g["key"],
                "label": g["label"],
                "description": g["description"],
                "topics": list(g["topics"].values()),
                **prefs[g["key"]],
            }
            for g in CATALOG[p["kind"]]
        ],
    }


class PreferenceInput(BaseModel):
    key: str
    in_app: bool
    email: bool


class PreferencesInput(BaseModel):
    groups: list[PreferenceInput]


@router.put("/preferences")
def save_preferences(data: PreferencesInput, request: Request, db: Session = Depends(get_db)):
    p = _who(request, db)
    if p.get("role") not in MANAGERS:
        raise HTTPException(
            403, "Bildirim ayarlarını hesap sahibi veya filo yöneticisi değiştirebilir."
        )
    valid = {g["key"] for g in CATALOG[p["kind"]]}
    for item in data.groups:
        if item.key not in valid:
            raise HTTPException(422, "Geçersiz bildirim grubu.")
        row = (
            db.query(m.NotificationPreference)
            .filter_by(portal=p["kind"], tenant_id=p["id"], group_key=item.key)
            .first()
        )
        if not row:
            row = m.NotificationPreference(portal=p["kind"], tenant_id=p["id"], group_key=item.key)
            db.add(row)
        row.in_app, row.email = item.in_app, item.email
    db.commit()
    return get_preferences(request, db)


def catalog_rows():
    """Flat list for docs and tests: (portal, group, topic, label)."""
    return [
        (portal, g["key"], topic, label)
        for portal, groups in CATALOG.items()
        for g in groups
        for topic, label in g["topics"].items()
    ]


__all__ = [
    "router",
    "start",
    "remember_actor",
    "derive",
    "store",
    "deliver",
    "run_reminders",
    "CATALOG",
]
