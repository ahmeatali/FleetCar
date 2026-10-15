"""GPS can suggest maintenance, never silently book a provider or invent an interval."""

from datetime import date

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app import models as m
from app.common.time import business_today, stamp
from app.common.validation import number_detail
from app.supplier_context import vehicle
from app.supplier_schemas import OperationInput
from app.supplier_service import append_record, audit


def suggest(db, ctx, car, event):
    if (
        not car.is_active
        or car.next_service_due_km is None
        or car.mileage < car.next_service_due_km
    ):
        return
    key = str(car.next_service_due_km)
    if (
        db.query(m.AutomationRun)
        .filter_by(supplier_id=ctx["id"], vehicle_id=car.id, rule="maintenance_km", rule_key=key)
        .first()
    ):
        return
    try:
        with db.begin_nested():
            run = m.AutomationRun(
                supplier_id=ctx["id"],
                vehicle_id=car.id,
                integration_event_id=event.id,
                rule="maintenance_km",
                rule_key=key,
                reason=f"Arvento doğrulanmış kilometre {car.mileage}; bakım eşiği {car.next_service_due_km}.",
                result="Öneri Oluşturuldu",
                created_at=stamp(),
            )
            db.add(run)
            db.flush()
            actor = {**ctx, "actor": "Arvento / bakım kuralı"}
            row = append_record(
                db,
                actor,
                "maintenance",
                OperationInput(
                    title=f"{car.plate} / Km Bazlı Bakım Önerisi",
                    vehicle_id=car.id,
                    customer_id=car.customer_id,
                    date=business_today(),
                    amount=0,
                    details={
                        "reason": run.reason,
                        "source": "arvento",
                        "integration_event_id": event.id,
                        "threshold_km": car.next_service_due_km,
                    },
                ),
            )
            run.operation_id = row.id
    except IntegrityError:
        # A concurrent sync already produced the suggestion. The outer GPS transaction stays intact.
        return


def schedule(db, ctx, row, target):
    if target == "Onaylandı" and ctx["role"] != "owner":
        raise HTTPException(403, "Bakım önerisini firma sahibi onaylar.")
    if target not in {"Onaylandı", "Planlandı"}:
        return
    car = vehicle(db, ctx, row.vehicle_id)
    if not car.is_active:
        raise HTTPException(400, "Pasif araca servis planlanamaz.")
    provider_id = int(number_detail(row.details, "provider_id", minimum=1))
    provider = db.get(m.Supplier, provider_id)
    if not provider or provider.type != "servis" or not provider.is_email_verified:
        raise HTTPException(400, "Doğrulanmış servis sağlayıcısı seçin.")
    interval = number_detail(row.details, "next_interval_km", minimum=1)
    if not interval.is_integer():
        raise HTTPException(400, "Bakım aralığı tam kilometre olmalı.")
    try:
        appointment = date.fromisoformat(row.details.get("appointment_date", ""))
    except (ValueError, TypeError):
        raise HTTPException(400, "Servis randevu tarihini girin.")
    if appointment < business_today():
        raise HTTPException(400, "Geçmişe servis randevusu açılamaz.")
    if target == "Onaylandı":
        row.details = {**row.details, "approved_estimate_amount": row.amount}
        return
    if row.details.get("request_id"):
        raise HTTPException(409, "Bakım önerisi zaten servis talebine bağlandı.")
    request = m.Request(
        vehicle_id=car.id,
        supplier_id=provider_id,
        type="servis",
        status="Beklemede",
        description=row.title,
        created_at=stamp(),
        details={
            "maintenance_proposal_id": row.id,
            "next_interval_km": int(interval),
            "preferred_date_start": appointment.isoformat(),
            "preferred_date_end": appointment.isoformat(),
            "estimated_amount": row.amount,
            "source": row.details.get("source", "manual"),
        },
    )
    db.add(request)
    db.flush()
    row.details = {
        **row.details,
        "request_id": request.id,
        "appointment_date": appointment.isoformat(),
    }
    car.status = "Serviste"
    audit(
        db,
        ctx,
        row,
        "Bakım randevusu oluşturuldu",
        {"request_id": request.id, "provider_id": provider_id},
    )


def completed(db, request, car):
    rid = (request.details or {}).get("maintenance_proposal_id")
    if not rid:
        return
    proposal = (
        db.query(m.SupplierOperation)
        .filter_by(id=rid, kind="maintenance", supplier_id=car.supplier_id, vehicle_id=car.id)
        .first()
    )
    if not proposal or proposal.details.get("request_id") != request.id:
        raise HTTPException(409, "Bakım önerisi ve servis talebi eşleşmiyor.")
    if not request.details.get("invoice_no") or request.details.get("invoice_amount") is None:
        raise HTTPException(400, "Bakım tamamlanmadan servis faturasını kaydedin.")
    if proposal.details.get("cost_approval_required"):
        approved = (
            db.query(m.SupplierOperation)
            .filter_by(
                kind="approval",
                parent_id=proposal.id,
                status="Onaylandı",
                supplier_id=car.supplier_id,
            )
            .all()
        )
        if not any(
            a.details.get("target_version") == proposal.version
            and a.details.get("target_amount") == proposal.amount
            for a in approved
        ):
            raise HTTPException(
                400,
                "Servis faturası onaylı tahmini aşıyor. Firma sahibi güncel maliyeti onaylamalı.",
            )
    interval = number_detail(request.details, "next_interval_km", minimum=1)
    car.last_service_date = request.completed_at[:10]
    car.last_service_mileage = car.mileage
    car.next_service_due_km = car.mileage + int(interval)
    proposal.status = "Tamamlandı"
    proposal.version += 1
    proposal.updated_at = stamp()
    audit(
        db,
        {"id": car.supplier_id, "actor": "Servis tamamlanma kuralı"},
        proposal,
        "Bakım tamamlandı; sonraki eşik güncellendi",
        {"request_id": request.id, "next_due_km": car.next_service_due_km},
    )


def register_invoice(db, request):
    rid = (request.details or {}).get("maintenance_proposal_id")
    if not rid:
        return
    car = db.get(m.Vehicle, request.vehicle_id)
    proposal = (
        db.query(m.SupplierOperation)
        .filter_by(id=rid, kind="maintenance", supplier_id=car.supplier_id, vehicle_id=car.id)
        .first()
    )
    if not proposal or proposal.details.get("request_id") != request.id:
        raise HTTPException(409, "Bakım önerisi ve servis talebi eşleşmiyor.")
    actual = number_detail(request.details, "invoice_amount")
    if proposal.details.get("actual_invoice_amount") == actual:
        return
    exceeds = actual > number_detail(proposal.details, "approved_estimate_amount")
    proposal.amount = round(actual, 2)
    proposal.version += 1
    proposal.updated_at = stamp()
    proposal.details = {
        **proposal.details,
        "actual_invoice_amount": actual,
        "cost_approval_required": exceeds,
    }
    actor = {"id": car.supplier_id, "actor": "Servis faturası kontrolü", "role": "owner"}
    audit(
        db,
        actor,
        proposal,
        "Gerçek servis faturası kaydedildi",
        {"actual": actual, "approval_required": exceeds, "request_id": request.id},
    )
    if exceeds:
        append_record(
            db,
            actor,
            "approval",
            OperationInput(
                title=f"{proposal.number} / Tahmin Aşımı Onayı",
                parent_id=proposal.id,
                vehicle_id=car.id,
                customer_id=proposal.customer_id,
                date=business_today(),
                amount=proposal.amount,
                details={
                    "target_version": proposal.version,
                    "target_amount": proposal.amount,
                    "reason": "Servis faturası onaylı tahmini aşıyor.",
                },
            ),
        )
