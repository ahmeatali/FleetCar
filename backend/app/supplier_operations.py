"""Supplier business workflows. Shared fleet data is read once; business events preserve history."""

import calendar
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as m
from app.auth import hash_password
from app.common.time import business_today as business_today
from app.common.time import stamp as stamp
from app.common.validation import number_detail as number_detail
from app.common.validation import parsed as parsed
from app.database import get_db
from app.schemas import (
    SupplierVehicleAssignment,
    VehicleCreate,
    VehicleExpenseCreate,
    VehicleUpdate,
)
from app.supplier_context import (
    SERVICE_TYPES,
)
from app.supplier_context import (
    context as context,
)
from app.supplier_context import (
    customer_ids as customer_ids,
)
from app.supplier_context import (
    operation as operation,
)
from app.supplier_context import (
    session_token as session_token,
)
from app.supplier_context import (
    vehicle as vehicle,
)
from app.supplier_permissions import capabilities, permit
from app.supplier_schemas import (
    ConvertInput,
    CustomerInput,
    MemberInput,
    OperationInput,
    SettingsInput,
    SharedInput,
    TransitionInput,
)
from app.supplier_service import (
    append_record as append_record,
)
from app.supplier_service import (
    approval_needed as approval_needed,
)
from app.supplier_service import (
    audit as audit,
)
from app.supplier_service import (
    display_status as display_status,
)
from app.supplier_service import (
    link_customer as link_customer,
)
from app.supplier_service import (
    serialize as serialize,
)
from app.supplier_service import (
    settings as settings,
)
from app.supplier_service import (
    sync_policy as sync_policy,
)
from app.supplier_service import (
    validate_record as validate_record,
)
from app.supplier_workflow import INITIAL, PREFIXES, TRANSITIONS

router = APIRouter(prefix="/api/supplier-workspace", tags=["Supplier workspace"])


@router.get("/session")
def read_session(ctx=Depends(context)):
    return {
        "supplier_id": ctx["id"],
        "name": ctx["actor"],
        "company_name": ctx["supplier"].name,
        "role": ctx["role"],
        "capabilities": capabilities(ctx["role"]),
    }


@router.post("/logout")
def logout(ctx=Depends(context), db: Session = Depends(get_db)):
    db.delete(ctx["session"])
    db.commit()
    return {"ok": True}


@router.get("/directory")
def directory(ctx=Depends(context), db: Session = Depends(get_db)):
    return [
        {"id": c.id, "company_name": c.company_name}
        for c in db.query(m.Customer)
        .filter(m.Customer.id.in_(customer_ids(db, ctx["id"])))
        .order_by(m.Customer.company_name)
        .all()
    ]


@router.get("/customers")
def get_customers(ctx=Depends(context), db: Session = Depends(get_db)):
    result = []
    for cid in customer_ids(db, ctx["id"]):
        c = db.get(m.Customer, cid)
        if not c:
            continue
        link = (
            db.query(m.SupplierCustomerLink)
            .filter_by(supplier_id=ctx["id"], customer_id=cid)
            .first()
        )
        cars = db.query(m.Vehicle).filter_by(supplier_id=ctx["id"], customer_id=cid).all()
        records = (
            db.query(m.SupplierOperation).filter_by(supplier_id=ctx["id"], customer_id=cid).all()
        )
        invoices = [
            r
            for r in records
            if r.kind == "invoice"
            and r.status not in {"Taslak", "İptal"}
            and r.details.get("direction") == "gelir"
        ]
        result.append(
            {
                "id": cid,
                "source": "customer",
                "number": f"MUS-{cid:04d}",
                "title": c.company_name,
                "company_name": c.company_name,
                "email": c.email,
                "phone": c.phone,
                "address": c.address,
                "customer_id": cid,
                "customer_name": c.company_name,
                "status": (link.details or {}).get("status", "Aktif") if link else "Aktif",
                "details": {
                    **(link.details if link else {}),
                    "email": c.email,
                    "phone": c.phone,
                    "address": c.address,
                },
                "vehicle_count": len(cars),
                "active_vehicles": sum(v.is_active for v in cars),
                "amount": sum(r.amount for r in invoices),
                "date": link.created_at[:10] if link else None,
                "actions": [],
            }
        )
    return sorted(result, key=lambda c: c["title"].casefold())


@router.post("/customers")
def save_customer(data: CustomerInput, ctx=Depends(context), db: Session = Depends(get_db)):
    permit(ctx, "customer")
    if data.customer_id:
        if data.customer_id not in customer_ids(db, ctx["id"]):
            raise HTTPException(
                404,
                "Müşteri erişimi onaylanmamış. Müşteri firma sahibi panelinden tedarikçi bağlantısını onaylamalı.",
            )
        link_customer(db, ctx["id"], data.customer_id, data.details)
        cid = data.customer_id
    else:
        name = data.company_name.strip()
        if not name:
            raise HTTPException(400, "Firma adını girin.")
        email = data.email.strip().lower() if data.email else None
        if email and db.query(m.Customer).filter_by(email=email).first():
            raise HTTPException(
                409, "Bu e-posta ile kayıtlı müşteri var. Mevcut müşteri bağlantısını kullanın."
            )
        c = m.Customer(
            company_name=name, email=email, phone=data.phone, address=data.address, status="Aktif"
        )
        db.add(c)
        db.flush()
        cid = c.id
        link_customer(db, ctx["id"], cid, data.details)
    db.commit()
    return next(c for c in get_customers(ctx, db) if c["id"] == cid)


@router.put("/customers/{cid}")
def update_customer(
    cid: int, data: CustomerInput, ctx=Depends(context), db: Session = Depends(get_db)
):
    permit(ctx, "customer")
    if cid not in customer_ids(db, ctx["id"]):
        raise HTTPException(404, "Müşteri bulunamadı.")
    # Relationship metadata is supplier-owned; the shared customer's identity is not overwritten.
    link_customer(db, ctx["id"], cid, data.details)
    db.commit()
    return next(c for c in get_customers(ctx, db) if c["id"] == cid)


@router.get("/records/{kind}")
def list_records(kind: str, ctx=Depends(context), db: Session = Depends(get_db)):
    if kind not in INITIAL:
        raise HTTPException(404, "Modül bulunamadı.")
    return [
        serialize(db, r)
        for r in db.query(m.SupplierOperation)
        .filter_by(supplier_id=ctx["id"], kind=kind)
        .order_by(m.SupplierOperation.id.desc())
        .all()
    ]


@router.post("/records/{kind}")
def create_record(
    kind: str, data: OperationInput, ctx=Depends(context), db: Session = Depends(get_db)
):
    permit(ctx, kind)
    row = append_record(db, ctx, kind, data)
    db.commit()
    db.refresh(row)
    return serialize(db, row)


@router.put("/records/{rid}")
def edit_record(
    rid: int, data: OperationInput, ctx=Depends(context), db: Session = Depends(get_db)
):
    row = operation(db, ctx, rid)
    permit(ctx, row.kind)
    if not data.version or data.version != row.version:
        raise HTTPException(409, "Kayıt değişti. Yenileyin.")
    if row.status not in {
        "Önerildi",
        "Hazırlık",
        "Ekspertizde",
        "İlanda",
        "Teklif Alındı",
        "Revizyon Bekliyor",
        "Taslak",
        "Planlandı",
        "İnceleniyor",
        "Mutabakat Bekliyor",
        "Bildirildi",
        "Kaydedildi",
        "Aktif",
    } or row.kind not in {
        "offer",
        "contract",
        "delivery",
        "return",
        "sale",
        "maintenance",
        "damage",
        "scenario",
        "policy",
        "invoice",
    }:
        raise HTTPException(400, "Bu durumdaki kayıt düzenlenemez.")
    if row.kind == "contract" and row.status == "Aktif":
        raise HTTPException(400, "Aktif sözleşmeyi yeni sözleşmeyle yenileyin.")
    if row.kind in {"contract", "delivery"}:
        from app.signature_documents import locked

        locked(db, row)
    validate_record(db, ctx, row.kind, data)
    if row.kind == "sale":
        from app.vehicle_sales import validate

        if data.vehicle_id != row.vehicle_id:
            raise HTTPException(400, "Satış dosyasının aracı değiştirilemez.")
        validate(db, ctx, data, current=row.id)
    if row.kind == "invoice":
        identity = (
            db.query(m.InvoiceIdentity)
            .filter_by(operation_id=row.id, supplier_id=ctx["id"])
            .first()
        )
        if not identity:
            identity = m.InvoiceIdentity(
                supplier_id=ctx["id"], operation_id=row.id, invoice_no=data.details["invoice_no"]
            )
            db.add(identity)
        identity.invoice_no = data.details["invoice_no"]
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Fatura numarası daha önce kullanılmış.")
    before = {
        "amount": row.amount,
        "status": row.status,
        "customer_id": row.customer_id,
        "vehicle_id": row.vehicle_id,
        "details": row.details,
    }
    if row.parent_id != data.parent_id:
        raise HTTPException(400, "Üst kayıt değiştirilemez.")
    if row.kind == "policy" and row.status == "Aktif" and data.amount != row.amount:
        raise HTTPException(400, "Aktif poliçe primi değiştirilemez. Yeni poliçe oluşturun.")
    if row.kind == "invoice" and any(
        r.id != row.id
        and r.status != "İptal"
        and r.details.get("invoice_no") == data.details.get("invoice_no")
        for r in db.query(m.SupplierOperation)
        .filter_by(supplier_id=ctx["id"], kind="invoice")
        .all()
    ):
        raise HTTPException(409, "Fatura numarası zaten kayıtlı.")
    if row.kind == "offer":
        from app.offer_history import capture

        if not db.query(m.OfferVersion).filter_by(offer_id=row.id, version=row.version).first():
            capture(db, row)
            db.flush()
    values = data.model_dump(exclude={"version"})
    values["amount"] = round(data.amount, 2)
    values["date"] = data.date.isoformat()
    values["end_date"] = data.end_date.isoformat() if data.end_date else None
    if row.kind == "offer" and row.status == "Revizyon Bekliyor":
        values["status"] = "Taslak"
    changed = (
        db.query(m.SupplierOperation)
        .filter_by(id=rid, version=data.version)
        .update(
            {**values, "version": data.version + 1, "updated_at": stamp()},
            synchronize_session=False,
        )
    )
    if changed != 1:
        db.rollback()
        raise HTTPException(409, "Kayıt değişti. Yenileyin.")
    db.refresh(row)
    if row.kind == "contract":
        from app.rental_lifecycle import attach

        db.query(m.ContractVehicle).filter_by(contract_id=row.id, supplier_id=ctx["id"]).delete()
        attach(db, ctx, row)
    if row.kind == "return" and row.status == "Mutabakat Bekliyor":
        from app.rental_lifecycle import return_status

        return_status(db, ctx, row, "Mutabakat Bekliyor")
    if row.kind == "offer":
        capture(db, row)
    audit(
        db,
        ctx,
        row,
        "Kayıt düzenlendi",
        {
            "before": before,
            "after": {"amount": row.amount, "details": row.details, "customer_id": row.customer_id},
        },
    )
    if row.kind == "policy":
        sync_policy(db, ctx, row)
    db.commit()
    return serialize(db, row)


@router.post("/records/{rid}/status")
def change_status(
    rid: int, data: TransitionInput, ctx=Depends(context), db: Session = Depends(get_db)
):
    row = operation(db, ctx, rid)
    permit(ctx, row.kind)
    if row.version != data.version:
        raise HTTPException(409, "Kayıt değişti. Yenileyin.")
    if data.status not in TRANSITIONS.get(row.kind, {}).get(row.status, []):
        raise HTTPException(400, "Bu durum geçişi geçerli değil.")
    if (
        row.kind == "offer"
        and data.status == "İptal"
        and db.query(m.SupplierOperation)
        .filter_by(parent_id=row.id, kind="contract")
        .filter(m.SupplierOperation.status != "İptal")
        .first()
    ):
        raise HTTPException(400, "Sözleşmeye dönüşmüş teklif iptal edilemez.")
    if (
        row.kind == "offer"
        and data.status == "Onaylandı"
        and row.end_date
        and row.end_date < business_today().isoformat()
    ):
        raise HTTPException(400, "Süresi dolmuş teklif onaylanamaz.")
    if row.kind == "offer" and data.status == "Onaylandı":
        row.details = {**row.details, "acceptance_source": "supplier_manual"}
    approval_needed(db, ctx, row, data.status)
    v = vehicle(db, ctx, row.vehicle_id) if row.vehicle_id else None
    if row.kind == "contract" and data.status == "Aktif":
        if row.end_date < business_today().isoformat():
            raise HTTPException(400, "Bitiş tarihi geçmiş sözleşme aktifleştirilemez.")
        from app.rental_lifecycle import activate

        activate(db, ctx, row)
        link_customer(db, ctx["id"], row.customer_id)
    if row.kind == "contract" and data.status in {"Sona Erdi", "İptal"}:
        from app.rental_lifecycle import close

        close(db, ctx, row, data.status)
        row.details = {**row.details, "closed_at": business_today().isoformat()}
        for child in (
            db.query(m.SupplierOperation)
            .filter_by(parent_id=row.id, kind="delivery", status="Planlandı")
            .all()
        ):
            child.status = "İptal"
            child.version += 1
            audit(db, ctx, child, "Sözleşme kapandığı için iptal edildi")
        if v.contract_no == row.number:
            v.customer_id = None
            v.contract_no = None
            v.contract_start_date = None
            v.contract_end_date = None
            v.monthly_rent = None
            v.monthly_km_limit = None
    if row.kind == "delivery" and data.status == "Tamamlandı":
        parent = operation(db, ctx, row.parent_id)
        if (
            parent.status != "Aktif"
            or v.contract_no != parent.number
            or v.customer_id != row.customer_id
        ):
            raise HTTPException(400, "Araç aktif sözleşme ve müşteriyle eşleşmiyor.")
        checks = row.details.get("checks", {})
        if not all(
            checks.get(key) is True for key in ["exterior", "interior", "documents", "equipment"]
        ):
            raise HTTPException(400, "Teslimat kontrol listesini tamamlayın.")
        if not row.details.get("receiver"):
            raise HTTPException(400, "Teslim alan bilgisi gerekli.")
        km = int(number_detail(row.details, "mileage"))
        if km < int(v.mileage or 0):
            raise HTTPException(400, "Teslim kilometresi mevcut kilometreden küçük olamaz.")
        from app.signature_documents import ensure_signed

        proof = ensure_signed(db, row)
        row.details = {
            **row.details,
            "signature_envelope_id": proof.id,
            "signed_document_id": proof.document_id,
            "signature_source": proof.source,
        }
        form = m.DeliveryForm(
            customer_id=row.customer_id,
            vehicle_id=row.vehicle_id,
            receiver=row.details["receiver"],
            issuer=row.details.get("issuer"),
            date=row.date,
            mileage=km,
            notes=row.details.get("notes"),
        )
        db.add(form)
        db.flush()
        row.details = {**row.details, "delivery_form_id": form.id}
        v.delivery_date = row.date
        v.received_by = row.details["receiver"]
        v.delivered_by = row.details.get("issuer")
        v.delivery_location = row.details.get("location")
        v.delivery_notes = row.details.get("notes")
        v.mileage = km
        db.add(
            m.VehicleMileageRecord(
                vehicle_id=v.id, mileage=km, recorded_at=stamp(), source="supplier_delivery"
            )
        )
        from app.rental_lifecycle import delivered

        delivered(db, ctx, row)
    if row.kind == "maintenance":
        from app.maintenance_automation import schedule

        schedule(db, ctx, row, data.status)
    if row.kind == "sale":
        from app.vehicle_sales import transition

        transition(db, ctx, row, data.status)
    if row.kind == "delivery" and data.status == "İptal":
        from app.rental_lifecycle import rental_for

        rental = rental_for(db, ctx, row.parent_id, row.vehicle_id)
        if rental.status == "Teslim Bekliyor":
            rental.delivery_id = None
            rental.version += 1
    if row.kind == "return":
        from app.rental_lifecycle import return_status

        return_status(db, ctx, row, data.status)
    if row.kind == "policy" and data.status == "Aktif":
        row.status = "Aktif"
        sync_policy(db, ctx, row)
    if (
        row.kind == "policy"
        and data.status == "İptal"
        and row.details.get("policy_type") in {"Kasko", "Trafik"}
    ):
        field = (
            "casco_policy_no"
            if row.details["policy_type"] == "Kasko"
            else "traffic_insurance_policy_no"
        )
        expiry = (
            "casco_insurance_expiry_date"
            if row.details["policy_type"] == "Kasko"
            else "traffic_insurance_expiry_date"
        )
        if getattr(v, field) == row.details.get("policy_no"):
            candidates = [
                p
                for p in db.query(m.SupplierOperation)
                .filter_by(supplier_id=ctx["id"], kind="policy", vehicle_id=v.id, status="Aktif")
                .all()
                if p.id != row.id
                and p.details.get("policy_type") == row.details["policy_type"]
                and p.end_date >= business_today().isoformat()
            ]
            latest = max(candidates, key=lambda p: p.end_date) if candidates else None
            setattr(v, field, latest.details["policy_no"] if latest else None)
            setattr(v, expiry, latest.end_date if latest else None)
    if row.kind == "invoice" and data.status == "İptal":
        if db.query(m.SupplierOperation).filter_by(parent_id=row.id, kind="payment").first():
            raise HTTPException(400, "Ödemesi bulunan fatura iptal edilemez.")
    if row.kind == "approval" and data.status == "Onaylandı":
        parent = operation(db, ctx, row.parent_id)
        if (
            row.details.get("target_version") != parent.version
            or row.details.get("target_amount") != parent.amount
        ):
            raise HTTPException(409, "Onay konusu değişti. Yeni onay isteyin.")
    changed = (
        db.query(m.SupplierOperation)
        .filter_by(id=row.id, version=data.version)
        .update(
            {
                "status": data.status,
                "version": data.version + 1,
                "updated_at": stamp(),
                "details": row.details,
                "amount": row.amount,
            },
            synchronize_session=False,
        )
    )
    if changed != 1:
        db.rollback()
        raise HTTPException(409, "Kayıt değişti. Yenileyin.")
    db.refresh(row)
    if row.kind == "offer":
        from app.offer_history import capture

        capture(db, row)
    audit(db, ctx, row, f"Durum: {data.status}")
    db.commit()
    return serialize(db, row)


@router.post("/records/{rid}/convert")
def convert(rid: int, data: ConvertInput, ctx=Depends(context), db: Session = Depends(get_db)):
    parent = operation(db, ctx, rid)
    permit(ctx, data.kind)
    if parent.version != data.version:
        raise HTTPException(409, "Kayıt değişti. Yenileyin.")
    allowed = (
        (parent.kind == "offer" and parent.status == "Onaylandı" and data.kind == "contract")
        or (
            parent.kind == "contract"
            and parent.status == "Aktif"
            and data.kind in {"delivery", "invoice"}
        )
        or (parent.kind == "sale" and parent.status == "Satıldı" and data.kind == "invoice")
        or (parent.kind == "return" and parent.status == "Tamamlandı" and data.kind == "invoice")
    )
    if not allowed:
        raise HTTPException(400, "Bu kayıt dönüştürülemez.")
    linked = (
        db.query(m.SupplierOperation)
        .filter_by(parent_id=parent.id, kind=data.kind)
        .filter(m.SupplierOperation.status != "İptal")
        .all()
    )
    target_vehicle = data.vehicle_id or parent.vehicle_id
    if data.kind == "delivery" and any(r.vehicle_id == target_vehicle for r in linked):
        raise HTTPException(409, "Bu sözleşme için teslimat zaten oluşturulmuş.")
    if data.kind == "contract" and linked:
        raise HTTPException(409, "Teklif zaten bir sözleşmeye dönüştürüldü.")
    details = dict(parent.details)
    if parent.kind == "offer":
        details["accepted_offer_version"] = parent.version
    end = parent.end_date
    if data.kind == "contract":
        ids = data.vehicle_ids or ([target_vehicle] if target_vehicle else [])
        if len(ids) != int(parent.details.get("quantity", 1)) or len(set(ids)) != len(ids):
            raise HTTPException(400, "Teklifteki adet kadar benzersiz araç seçin.")
        for vid in ids:
            vehicle(db, ctx, vid)
        target_vehicle = ids[0]
        details["vehicle_ids"] = ids
        details["unit_monthly_rent"] = parent.amount
        # Offer validity is not the rental end date.
        months = int(number_detail(details, "months", default=12, minimum=1))
        start = business_today()
        month_index = start.year * 12 + start.month - 1 + months
        year, month0 = divmod(month_index, 12)
        end = (
            date(year, month0 + 1, min(start.day, calendar.monthrange(year, month0 + 1)[1]))
            - timedelta(days=1)
        ).isoformat()
    if data.kind == "delivery":
        details = {
            "receiver": "",
            "issuer": ctx["actor"],
            "mileage": int(vehicle(db, ctx, target_vehicle).mileage or 0),
            "checks": {},
        }
    if data.kind == "invoice":
        period = business_today().isoformat()[:7]
        all_invoices = (
            db.query(m.SupplierOperation)
            .filter_by(parent_id=parent.id, kind="invoice", supplier_id=ctx["id"])
            .all()
        )
        if parent.kind == "contract" and any(
            i.status != "İptal" and i.details.get("billing_period") == period for i in all_invoices
        ):
            raise HTTPException(409, "Bu dönem için sözleşme faturası zaten oluşturuldu.")
        details = {
            "direction": "gelir",
            "invoice_no": f"{parent.number}-{business_today().isoformat()}-{len(all_invoices)+1}",
            "billing_period": period,
        }
        end = (business_today() + timedelta(days=30)).isoformat()
    amount = parent.amount if data.kind != "delivery" else 0
    if data.kind == "contract":
        amount = round(parent.amount * len(details["vehicle_ids"]), 2)
    if data.kind == "invoice" and parent.kind == "contract":
        links = (
            db.query(m.ContractVehicle)
            .filter_by(contract_id=parent.id, supplier_id=ctx["id"])
            .all()
        )
        if data.vehicle_id:
            link = next((link for link in links if link.vehicle_id == data.vehicle_id), None)
            if not link:
                raise HTTPException(404, "Sözleşme aracı bulunamadı.")
            amount = link.monthly_rent
        elif len(links) > 1:
            target_vehicle = None
            details["vehicle_allocations"] = [
                {"vehicle_id": link.vehicle_id, "amount": link.monthly_rent} for link in links
            ]
    payload = OperationInput(
        title=f"{parent.number} / "
        + {"contract": "Sözleşme", "delivery": "Teslimat", "invoice": "Fatura"}[data.kind],
        customer_id=parent.customer_id,
        vehicle_id=target_vehicle,
        parent_id=parent.id,
        date=business_today(),
        end_date=end,
        amount=amount,
        details=details,
    )
    row = append_record(db, ctx, data.kind, payload)
    audit(db, ctx, parent, f"{PREFIXES[data.kind]} oluşturuldu", {"record_id": row.id})
    db.commit()
    return serialize(db, row)


@router.get("/records/{rid}/events")
def events(rid: int, ctx=Depends(context), db: Session = Depends(get_db)):
    operation(db, ctx, rid)
    return [
        {"id": r.id, "title": r.title, "actor": r.actor, "date": r.created_at, "details": r.details}
        for r in db.query(m.SupplierOperationEvent)
        .filter_by(operation_id=rid, supplier_id=ctx["id"])
        .order_by(m.SupplierOperationEvent.id.desc())
        .all()
    ]


@router.post("/records/{rid}/request-approval")
def request_approval(rid: int, ctx=Depends(context), db: Session = Depends(get_db)):
    parent = operation(db, ctx, rid)
    permit(ctx, parent.kind)
    if parent.kind in {"approval", "payment"} or parent.status in {
        "İptal",
        "Sona Erdi",
        "Ödendi",
        "Tamamlandı",
    }:
        raise HTTPException(400, "Bu kayıt için onay istenemez.")
    existing = (
        db.query(m.SupplierOperation)
        .filter_by(parent_id=rid, kind="approval", status="Beklemede")
        .all()
    )
    if any(a.details.get("target_version") == parent.version for a in existing):
        raise HTTPException(409, "Bu sürüm için onay talebi var.")
    data = OperationInput(
        title=f"{parent.number} onayı",
        customer_id=parent.customer_id,
        vehicle_id=parent.vehicle_id,
        parent_id=parent.id,
        date=business_today(),
        amount=parent.amount,
        details={"target_version": parent.version, "target_amount": parent.amount},
    )
    row = append_record(db, ctx, "approval", data)
    db.commit()
    return serialize(db, row)


@router.get("/users")
def users(ctx=Depends(context), db: Session = Depends(get_db)):
    if ctx["role"] != "owner":
        raise HTTPException(403, "Kullanıcı yönetimi şirket sahibine aittir.")
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in db.query(m.SupplierPortalUser).filter_by(supplier_id=ctx["id"]).all()
    ]


@router.post("/users")
def create_user(data: MemberInput, ctx=Depends(context), db: Session = Depends(get_db)):
    if ctx["role"] != "owner":
        raise HTTPException(403, "Kullanıcı oluşturma yetkiniz yok.")
    if not data.password:
        raise HTTPException(400, "En az 10 karakterli şifre gerekli.")
    email = data.email.strip().lower()
    if "@" not in email:
        raise HTTPException(400, "Geçerli e-posta girin.")
    if (
        db.query(m.SupplierPortalUser).filter_by(email=email).first()
        or db.query(m.Supplier).filter_by(email=email).first()
    ):
        raise HTTPException(409, "E-posta zaten kayıtlı.")
    u = m.SupplierPortalUser(
        supplier_id=ctx["id"],
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=data.is_active,
        created_at=stamp(),
    )
    db.add(u)
    db.commit()
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "is_active": u.is_active}


@router.put("/users/{uid}")
def edit_user(uid: int, data: MemberInput, ctx=Depends(context), db: Session = Depends(get_db)):
    if ctx["role"] != "owner":
        raise HTTPException(403, "Kullanıcı yönetimi yetkiniz yok.")
    u = db.query(m.SupplierPortalUser).filter_by(id=uid, supplier_id=ctx["id"]).first()
    if not u:
        raise HTTPException(404, "Kullanıcı bulunamadı.")
    # Login identity cannot be changed to impersonate a different member.
    if data.email.strip().lower() != u.email:
        raise HTTPException(400, "Giriş e-postası değiştirilemez.")
    u.name = data.name
    u.role = data.role
    u.is_active = data.is_active
    if data.password:
        u.password_hash = hash_password(data.password)
    db.commit()
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "is_active": u.is_active}


@router.get("/settings")
def get_settings(ctx=Depends(context), db: Session = Depends(get_db)):
    return settings(db, ctx["id"])


@router.put("/settings")
def save_settings(data: SettingsInput, ctx=Depends(context), db: Session = Depends(get_db)):
    if ctx["role"] != "owner":
        raise HTTPException(403, "Ayar değiştirme yetkiniz yok.")
    r = db.query(m.SupplierSetting).filter_by(supplier_id=ctx["id"]).first()
    if not r:
        r = m.SupplierSetting(supplier_id=ctx["id"])
        db.add(r)
    r.value = {**(r.value or {}), **data.model_dump()}
    db.commit()
    return settings(db, ctx["id"])


@router.get("/snapshot")
def snapshot(ctx=Depends(context), db: Session = Depends(get_db)):
    from app.main import (
        hgs_transaction_dict,
        tire_record_dict,
        vehicle_dict,
        vehicle_expense_dict,
        vehicle_file_dict,
    )

    cars = db.query(m.Vehicle).filter_by(supplier_id=ctx["id"]).all()
    ids = [v.id for v in cars]
    records = [
        serialize(db, r)
        for r in db.query(m.SupplierOperation)
        .filter_by(supplier_id=ctx["id"])
        .order_by(m.SupplierOperation.id.desc())
        .all()
    ]
    requests = (
        db.query(m.Request)
        .filter(m.Request.vehicle_id.in_(ids))
        .order_by(m.Request.id.desc())
        .all()
        if ids
        else []
    )
    expenses = (
        db.query(m.VehicleExpense).filter(m.VehicleExpense.vehicle_id.in_(ids)).all() if ids else []
    )
    tolls = (
        db.query(m.HgsTransaction).filter(m.HgsTransaction.vehicle_id.in_(ids)).all() if ids else []
    )
    tires = db.query(m.TireRecord).filter(m.TireRecord.vehicle_id.in_(ids)).all() if ids else []
    files = (
        db.query(m.VehicleFile)
        .filter(m.VehicleFile.vehicle_id.in_(ids))
        .order_by(m.VehicleFile.id.desc())
        .all()
        if ids
        else []
    )

    def shared_row(kind, r, title, amount=0):
        v = next((v for v in cars if v.id == r.vehicle_id), None)
        from app.event_responsibility import resolve

        responsibility = resolve(
            db,
            ctx["id"],
            r.vehicle_id,
            getattr(r, "date", None) or getattr(r, "created_at", None),
            kind,
            r.id,
        )
        cid = responsibility["customer_id"]
        c = db.get(m.Customer, cid) if cid else None
        return {
            **responsibility,
            "id": f"{kind}:{r.id}",
            "kind": kind,
            "source": kind,
            "source_id": r.id,
            "number": f"{kind.upper()}-{r.id:05d}",
            "title": title,
            "vehicle_id": r.vehicle_id,
            "plate": v.plate if v else "",
            "vehicle_name": f"{v.brand} {v.model}" if v else "",
            "customer_id": cid,
            "customer_name": c.company_name if c else None,
            "date": getattr(r, "date", None) or getattr(r, "created_at", None),
            "end_date": None,
            "amount": amount,
            "status": getattr(r, "status", "Tamamlandı"),
            "actions": [],
        }

    services = []
    for r in requests:
        if r.type not in {"servis", "lastik", "yol_yardim"}:
            continue
        row = shared_row(
            "service",
            r,
            r.description or r.type,
            float((r.details or {}).get("invoice_amount") or 0),
        )
        row["details"] = {**(r.details or {}), "type": r.type}
        row["number"] = (r.details or {}).get("work_order_no") or f"IS-{r.id:05d}"
        services.append(row)
    fuel = [
        {**shared_row("fuel", r, r.kind, r.amount), "details": vehicle_expense_dict(r)}
        for r in expenses
    ]
    hgs = [
        {**shared_row("hgs", r, r.type, r.amount), "details": hgs_transaction_dict(r)}
        for r in tolls
    ]
    tire_rows = [
        {
            **shared_row("tire", r, f"{r.brand} {r.size}"),
            "details": tire_record_dict(r, next(v for v in cars if v.id == r.vehicle_id)),
        }
        for r in tires
    ]
    # Existing vehicle fields remain visible until a corresponding normalized business record exists.
    legacy_contracts = []
    legacy_policies = []
    for v in cars:
        if v.contract_no and not any(
            r["kind"] == "contract" and r["number"] == v.contract_no for r in records
        ):
            c = db.get(m.Customer, v.customer_id) if v.customer_id else None
            legacy_contracts.append(
                {
                    "id": f"legacy-contract:{v.id}",
                    "kind": "contract",
                    "source": "vehicle",
                    "number": v.contract_no,
                    "title": f"{v.plate} araç sözleşmesi",
                    "vehicle_id": v.id,
                    "plate": v.plate,
                    "customer_id": v.customer_id,
                    "customer_name": c.company_name if c else None,
                    "date": v.contract_start_date,
                    "end_date": v.contract_end_date,
                    "amount": v.monthly_rent or 0,
                    "status": (
                        "Süresi Doldu"
                        if v.contract_end_date
                        and v.contract_end_date < business_today().isoformat()
                        else "Aktif"
                    ),
                    "details": {
                        "months": v.contract_duration_months,
                        "annual_km": v.contract_committed_km,
                        "source_note": "Araç kaydı",
                    },
                    "actions": [],
                }
            )
        for ptype, no, end in [
            ("Kasko", v.casco_policy_no, v.casco_insurance_expiry_date),
            ("Trafik", v.traffic_insurance_policy_no, v.traffic_insurance_expiry_date),
        ]:
            if no and not any(
                r["kind"] == "policy"
                and r["vehicle_id"] == v.id
                and r["details"].get("policy_no") == no
                for r in records
            ):
                legacy_policies.append(
                    {
                        "id": f"legacy-policy:{ptype}:{v.id}",
                        "kind": "policy",
                        "source": "vehicle",
                        "number": no,
                        "title": f"{v.plate} {ptype}",
                        "vehicle_id": v.id,
                        "plate": v.plate,
                        "customer_id": v.customer_id,
                        "date": None,
                        "end_date": end,
                        "amount": 0,
                        "status": (
                            "Süresi Doldu"
                            if end and end < business_today().isoformat()
                            else "Aktif"
                        ),
                        "details": {
                            "policy_type": ptype,
                            "source_note": "Araç kaydı — prim bilgisi yok",
                        },
                        "actions": [],
                    }
                )
    records += legacy_contracts + legacy_policies
    rentals = []
    for r in db.query(m.Rental).filter_by(supplier_id=ctx["id"]).all():
        c = db.get(m.Customer, r.customer_id)
        v = next(v for v in cars if v.id == r.vehicle_id)
        contract = db.get(m.SupplierOperation, r.contract_id)
        rentals.append(
            {
                "id": f"rental:{r.id}",
                "source": "rental",
                "kind": "rental",
                "number": f"KRL-{r.id:06d}",
                "title": contract.number,
                "customer_id": r.customer_id,
                "customer_name": c.company_name,
                "vehicle_id": v.id,
                "plate": v.plate,
                "vehicle_name": f"{v.brand} {v.model}",
                "date": r.starts_at,
                "end_date": r.ends_at,
                "status": r.status,
                "amount": next(
                    (
                        link.monthly_rent
                        for link in db.query(m.ContractVehicle)
                        .filter_by(contract_id=r.contract_id, vehicle_id=v.id)
                        .all()
                    ),
                    0,
                ),
                "actions": [],
                "parent_id": r.contract_id,
                "details": {
                    "contract_id": r.contract_id,
                    "delivery_id": r.delivery_id,
                    "return_id": r.return_id,
                    "delivered_at": r.delivered_at,
                    "returned_at": r.returned_at,
                    "version": r.version,
                },
            }
        )

    def car_snapshot(v):
        rental = next(
            (
                r
                for r in rentals
                if r["vehicle_id"] == v.id and r["status"] not in {"Tamamlandı", "İptal"}
            ),
            None,
        )
        return {**vehicle_dict(v, db), "rental_status": rental["status"] if rental else None}

    matching_queue = [
        r
        for r in fuel + hgs + records
        if r.get("kind") in {"fuel", "hgs", "fine"}
        and r.get("responsibility_status", r.get("details", {}).get("responsibility_status"))
        in {"Belirsiz", "Eşleştirme Bekliyor"}
        and not (r.get("kind") == "hgs" and r.get("details", {}).get("type") != "Geçiş")
    ]
    return {
        "matching_queue": matching_queue,
        "rentals": rentals,
        "session": read_session(ctx),
        "settings": settings(db, ctx["id"]),
        "vehicles": [car_snapshot(v) for v in cars],
        "customers": get_customers(ctx, db),
        "records": records,
        "service": services,
        "fuel": fuel,
        "hgs": hgs,
        "tire": tire_rows,
        "files": [vehicle_file_dict(f) for f in files],
        "providers": [
            {"id": s.id, "name": s.name, "type": s.type}
            for s in db.query(m.Supplier)
            .filter(m.Supplier.type.in_(SERVICE_TYPES), m.Supplier.is_email_verified.is_(True))
            .all()
        ],
        "usage": (
            [
                {
                    "id": u.id,
                    "vehicle_id": u.vehicle_id,
                    "started_at": u.started_at,
                    "ended_at": u.ended_at,
                }
                for u in db.query(m.VehicleUsageRecord)
                .filter(m.VehicleUsageRecord.vehicle_id.in_(ids))
                .all()
            ]
            if ids
            else []
        ),
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "actor": e.actor,
                "date": e.created_at,
                "record_id": e.operation_id,
            }
            for e in db.query(m.SupplierOperationEvent)
            .filter_by(supplier_id=ctx["id"])
            .order_by(m.SupplierOperationEvent.id.desc())
            .limit(100)
            .all()
        ],
    }


@router.post("/shared/{kind}")
def create_shared(
    kind: str, data: SharedInput, ctx=Depends(context), db: Session = Depends(get_db)
):
    from app import main, schemas

    if kind not in {"fuel", "hgs", "service", "tire"}:
        raise HTTPException(404, "Modül bulunamadı.")
    permit(ctx, kind)
    v = vehicle(db, ctx, data.vehicle_id)
    if not v.is_active:
        raise HTTPException(400, "Pasif araca işlem yapılamaz.")
    d = data.details
    if kind == "fuel":
        payload = parsed(
            schemas.VehicleExpenseCreate,
            vehicle_id=v.id,
            kind="Yakıt",
            amount=data.amount,
            date=data.date.isoformat(),
            mileage=int(number_detail(d, "mileage")),
            liters=number_detail(d, "liters", minimum=0.01),
            station=d.get("station"),
            receipt_no=d.get("receipt_no"),
            fuel_type=d.get("fuel_type") or v.fuel,
            note=data.title,
            full_tank=bool(d.get("full_tank")),
        )
        return main.create_vehicle_expense(payload, db, supplier_id=ctx["id"])
    if kind == "hgs":
        if d.get("type") == "Etiket":
            if not str(d.get("hgs_no", "")).strip():
                raise HTTPException(400, "HGS numarası girin.")
            v.hgs_no = str(d["hgs_no"]).strip()
            v.hgs_active = True
            db.commit()
            return main.vehicle_dict(v, db)
        payload = parsed(
            schemas.HgsTransactionCreate,
            type=d.get("type", ""),
            amount=data.amount,
            date=data.date.isoformat(),
            description=data.title,
        )
        return main.create_vehicle_hgs_transaction(v.id, payload, db)
    if kind == "service":
        request_type = d.get("type", "servis")
        if request_type not in {"servis", "lastik", "yol_yardim"}:
            raise HTTPException(400, "Hizmet türü geçersiz.")
        if number_detail(d, "estimated_amount") > settings(db, ctx["id"])["approval_threshold"]:
            raise HTTPException(
                400,
                "Tahmini tutar onay limitini aşıyor. Önce Hasar veya ilgili ticari kaydı onaya gönderin.",
            )
        provider_id = int(d["provider_id"]) if d.get("provider_id") else None
        if provider_id:
            provider = db.get(m.Supplier, provider_id)
            if not provider or not provider.is_email_verified or provider.type != request_type:
                raise HTTPException(400, "Bu hizmet için doğrulanmış servis seçin.")
        details = {
            **d,
            "preferred_date_start": data.date.isoformat(),
            "preferred_date_end": data.date.isoformat(),
        }
        payload = parsed(
            schemas.RequestCreate,
            vehicle_id=v.id,
            supplier_id=provider_id,
            type=request_type,
            description=data.title,
            details=details,
        )
        return main.create_request(payload, db)
    payload = parsed(
        schemas.TireRecordCreate,
        vehicle_id=v.id,
        brand=d.get("brand", ""),
        size=d.get("size", ""),
        season=d.get("season", "Dört Mevsim"),
        installed_at=data.date.isoformat(),
        remaining_km=int(number_detail(d, "remaining_km")),
        tread_depth_mm=number_detail(d, "tread_depth_mm"),
        notes=data.title,
    )
    return main.create_tire_record(payload, db)


@router.post("/vehicles")
def create_inventory(data: VehicleCreate, ctx=Depends(context), db: Session = Depends(get_db)):
    from app import main, schemas

    permit(ctx, "vehicle")
    data = {**data.model_dump(), "supplier_id": ctx["id"], "customer_id": None}
    return main.create_vehicle(schemas.VehicleCreate(**data), db)


@router.put("/vehicles/{vid}")
def edit_inventory(
    vid: str, data: VehicleUpdate, ctx=Depends(context), db: Session = Depends(get_db)
):
    from app import main

    permit(ctx, "vehicle")
    v = vehicle(db, ctx, vid)
    if v.status == "Satıldı":
        raise HTTPException(400, "Satışı tamamlanan araca işlem yapılamaz.")
    values = data.model_dump(exclude_unset=True)
    active_rental = (
        db.query(m.Rental)
        .filter(
            m.Rental.supplier_id == ctx["id"],
            m.Rental.vehicle_id == vid,
            m.Rental.status.notin_(["Tamamlandı", "İptal"]),
        )
        .first()
    )
    protected = {
        "contract_no",
        "contract_start_date",
        "contract_end_date",
        "monthly_rent",
        "contract_duration_months",
        "contract_committed_km",
        "monthly_km_limit",
        "contract_signed_at",
        "is_active",
    }
    if active_rental and any(k in values and values[k] != getattr(v, k, None) for k in protected):
        raise HTTPException(
            409, "Aktif kiralama ve sözleşme alanlarını sözleşme/iade akışından yönetin."
        )
    return main.update_vehicle(vid, data, db, supplier_id=ctx["id"])


@router.put("/vehicles/{vid}/assignment")
def assign_inventory(
    vid: str, data: SupplierVehicleAssignment, ctx=Depends(context), db: Session = Depends(get_db)
):
    from app import main

    permit(ctx, "vehicle")
    v = vehicle(db, ctx, vid)
    if v.status == "Satıldı":
        raise HTTPException(400, "Satışı tamamlanan araca işlem yapılamaz.")
    if data.customer_id and data.customer_id not in customer_ids(db, ctx["id"]):
        raise HTTPException(404, "Müşteriyi önce listenize ekleyin.")
    active_rental = (
        db.query(m.Rental)
        .filter(
            m.Rental.supplier_id == ctx["id"],
            m.Rental.vehicle_id == vid,
            m.Rental.status.notin_(["Tamamlandı", "İptal"]),
        )
        .first()
    )
    if active_rental and data.customer_id != active_rental.customer_id:
        raise HTTPException(409, "Aktif araç kiralaması atamasını iade/sözleşme akışından yönetin.")
    active = (
        db.query(m.SupplierOperation)
        .filter_by(supplier_id=ctx["id"], kind="contract", vehicle_id=vid, status="Aktif")
        .first()
    )
    if active and data.customer_id != active.customer_id:
        raise HTTPException(409, "Aktif sözleşmesi olan aracın müşterisi sözleşmeden yönetilir.")
    return main.assign_supplier_vehicle(ctx["id"], vid, data, db)


@router.get("/vehicles/{vid}")
def read_inventory(vid: str, ctx=Depends(context), db: Session = Depends(get_db)):
    from app.main import vehicle_dict

    return vehicle_dict(vehicle(db, ctx, vid), db)


@router.get("/vehicles/{vid}/{resource}")
def read_vehicle_resource(
    vid: str, resource: str, ctx=Depends(context), db: Session = Depends(get_db)
):
    from app import main

    vehicle(db, ctx, vid)
    readers = {
        "files": main.get_vehicle_files,
        "hgs": main.get_vehicle_hgs,
        "locations": main.get_vehicle_locations,
    }
    if resource in readers:
        return readers[resource](vid, db=db, supplier_id=ctx["id"])
    if resource == "mileage-records":
        return main.get_mileage_records(vid, db)
    if resource == "usage-records":
        return main.get_usage_records(vid, db)
    if resource == "business-history":
        from app.vehicle_business_history import history

        return history(db, vid, supplier_id=ctx["id"])
    raise HTTPException(404, "Kaynak bulunamadı.")


@router.get("/requests")
def read_fleet_requests(ctx=Depends(context), db: Session = Depends(get_db)):
    from app.main import get_requests

    return get_requests(db=db, fleet_supplier_id=ctx["id"])


@router.get("/expenses")
def read_fleet_expenses(ctx=Depends(context), db: Session = Depends(get_db)):
    from app.main import get_vehicle_expenses

    return get_vehicle_expenses(db=db, supplier_id=ctx["id"])


@router.post("/vehicles/{vid}/{resource}")
async def write_vehicle_resource(
    vid: str, resource: str, request: Request, ctx=Depends(context), db: Session = Depends(get_db)
):
    from app import main, schemas

    vehicle(db, ctx, vid)
    permit(ctx, "vehicle")
    if resource == "files":
        return await main.upload_vehicle_file(
            vid,
            request,
            db=db,
            category=request.query_params.get("category", "document"),
            document_type=request.query_params.get("document_type"),
            original_name=request.query_params.get("original_name", "document"),
            expiry_date=request.query_params.get("expiry_date"),
        )
    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(422, "Geçerli JSON gövdesi gerekli.")
    if resource == "hgs":
        return main.create_vehicle_hgs_transaction(
            vid, parsed(schemas.HgsTransactionCreate, **payload), db
        )
    if resource == "locations":
        return main.create_vehicle_location(
            vid, parsed(schemas.VehicleLocationCreate, **payload), db
        )
    if resource == "remove":
        if (
            db.query(m.SupplierOperation)
            .filter_by(vehicle_id=vid, supplier_id=ctx["id"], kind="contract", status="Aktif")
            .first()
        ):
            raise HTTPException(409, "Aktif sözleşmeyi önce sonlandırın.")
        return main.remove_vehicle(vid, parsed(schemas.VehicleRemoval, **payload), db)
    if resource == "reactivate":
        return main.reactivate_vehicle(vid, db)
    raise HTTPException(404, "Kaynak bulunamadı.")


@router.delete("/vehicles/{vid}/files/{fid}")
def remove_file(vid: str, fid: int, ctx=Depends(context), db: Session = Depends(get_db)):
    from app.main import delete_vehicle_file

    vehicle(db, ctx, vid)
    permit(ctx, "vehicle")
    return delete_vehicle_file(vid, fid, db)


@router.post("/expenses")
def write_fleet_expense(
    data: VehicleExpenseCreate, ctx=Depends(context), db: Session = Depends(get_db)
):
    from app.main import create_vehicle_expense

    permit(ctx, "fuel")
    vehicle(db, ctx, data.vehicle_id)
    return create_vehicle_expense(data, db, supplier_id=ctx["id"])


@router.get("/audit")
def audit_history(ctx=Depends(context), db: Session = Depends(get_db)):
    if ctx["role"] != "owner":
        raise HTTPException(403, "Denetim geçmişini firma sahibi görüntüler.")

    rows = (
        db.query(m.AuditEvent)
        .filter(
            or_(
                m.AuditEvent.target_supplier_id == ctx["id"],
                and_(
                    m.AuditEvent.principal_kind == "supplier", m.AuditEvent.subject_id == ctx["id"]
                ),
            )
        )
        .order_by(m.AuditEvent.id.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": row.id,
            "actor_scope": f"{row.principal_kind}:{row.subject_id}",
            "user_id": row.user_id,
            "role": row.role,
            "method": row.method,
            "resource": row.resource,
            "status_code": row.status_code,
            "elapsed_ms": row.elapsed_ms,
            "date": row.created_at,
        }
        for row in rows
    ]
