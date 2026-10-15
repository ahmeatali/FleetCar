"""Supplier domain services; routes orchestrate these validated business operations."""

import secrets
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app import models as m
from app.common.time import business_today, stamp
from app.common.validation import number_detail
from app.supplier_context import customer_ids, operation, vehicle
from app.supplier_workflow import DEFAULT_SETTINGS, INITIAL, PREFIXES, TRANSITIONS


def settings(db, sid):
    row = db.query(m.SupplierSetting).filter_by(supplier_id=sid).first()
    return (
        {
            **DEFAULT_SETTINGS,
            **{k: v for k, v in (row.value or {}).items() if k in DEFAULT_SETTINGS},
        }
        if row
        else dict(DEFAULT_SETTINGS)
    )


def link_customer(db, sid, cid, details=None):
    if not db.get(m.Customer, cid):
        raise HTTPException(404, "Müşteri bulunamadı.")
    link = db.query(m.SupplierCustomerLink).filter_by(supplier_id=sid, customer_id=cid).first()
    if not link:
        link = m.SupplierCustomerLink(
            supplier_id=sid, customer_id=cid, details=details or {}, created_at=stamp()
        )
        db.add(link)
    elif details is not None:
        link.details = {**(link.details or {}), **details}
    return link


def validate_record(db, ctx, kind, data):
    if kind not in INITIAL:
        raise HTTPException(404, "Geçersiz modül.")
    if data.details.get("occurred_at"):
        try:
            moment = datetime.fromisoformat(data.details["occurred_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(400, "Olay zamanı ISO tarih/saat olmalı.")
        if moment.date() != data.date:
            raise HTTPException(400, "Olay zamanı ve kayıt tarihi eşleşmeli.")
    if data.end_date and data.end_date < data.date:
        raise HTTPException(400, "Bitiş tarihi başlangıçtan önce olamaz.")
    if data.customer_id and data.customer_id not in customer_ids(db, ctx["id"]):
        raise HTTPException(404, "Müşteriyi önce müşteri listenize ekleyin.")
    v = vehicle(db, ctx, data.vehicle_id) if data.vehicle_id else None
    if v and not v.is_active and kind not in {"fine", "invoice", "payment", "approval"}:
        raise HTTPException(400, "Pasif araç için yeni operasyon oluşturulamaz.")
    parent = operation(db, ctx, data.parent_id) if data.parent_id else None
    if parent and (
        parent.status in {"İptal", "Reddedildi"}
        or parent.kind == "contract"
        and parent.status == "Sona Erdi"
        and kind != "invoice"
    ):
        raise HTTPException(400, "Kapanmış kayda yeni işlem bağlanamaz.")
    parent_vehicle_matches = (
        not parent
        or parent.kind == "offer"
        or parent.vehicle_id == data.vehicle_id
        or parent.kind == "contract"
        and (
            data.vehicle_id is None
            and kind == "invoice"
            or db.query(m.ContractVehicle)
            .filter_by(supplier_id=ctx["id"], contract_id=parent.id, vehicle_id=data.vehicle_id)
            .first()
        )
    )
    if parent and (parent.customer_id != data.customer_id or not parent_vehicle_matches):
        raise HTTPException(400, "Üst kayıt ile müşteri ve araç eşleşmeli.")
    if (
        kind in {"offer", "contract", "delivery", "return", "invoice", "payment"}
        and not data.customer_id
    ):
        raise HTTPException(400, "Müşteri seçin.")
    if kind in {"contract", "delivery", "return", "policy", "damage", "fine"} and not v:
        raise HTTPException(400, "Araç seçin.")
    if kind in {"offer", "contract"}:
        months = number_detail(data.details, "months", minimum=1)
        quantity = number_detail(data.details, "quantity", default=1, minimum=1)
        if not months.is_integer() or months > 120 or not quantity.is_integer() or quantity > 10000:
            raise HTTPException(400, "Süre ve adet tam sayı olmalı; en fazla 120 ay / 10000 araç.")
        number_detail(data.details, "annual_km", minimum=0)
        if data.amount <= 0:
            raise HTTPException(400, "Aylık kira sıfırdan büyük olmalı.")
        if kind == "contract" and not data.end_date:
            raise HTTPException(400, "Sözleşme bitiş tarihini girin.")
        if (
            kind == "contract"
            and parent
            and (parent.kind != "offer" or parent.status != "Onaylandı")
        ):
            raise HTTPException(400, "Sözleşme yalnızca onaylı teklife bağlanabilir.")
    if kind == "contract" and parent:
        commercial_keys = [
            "months",
            "annual_km",
            "excess_km_fee",
            "terms",
            "service_coverage",
            "tire_coverage",
            "replacement_coverage",
        ]
        if (
            data.details.get("accepted_offer_version") != parent.version
            or any(data.details.get(k) != parent.details.get(k) for k in commercial_keys)
            or int(data.details.get("quantity", 1)) != int(parent.details.get("quantity", 1))
            or round(data.amount, 2)
            != round(parent.amount * int(parent.details.get("quantity", 1)), 2)
        ):
            raise HTTPException(
                400, "Sözleşme kabul edilen teklif sürümü ve ticari şartlarla aynı olmalı."
            )
    if kind == "delivery" and (not parent or parent.kind != "contract" or parent.status != "Aktif"):
        raise HTTPException(400, "Teslimat aktif sözleşmeye bağlı olmalı.")
    if kind == "maintenance" and not v:
        raise HTTPException(400, "Bakım aracı gerekli.")
    if kind == "sale":
        if not v:
            raise HTTPException(400, "Satış aracı gerekli.")
    if kind == "return":
        if not parent or parent.kind != "contract" or parent.status != "Aktif":
            raise HTTPException(400, "İade aktif sözleşmeye bağlı olmalı.")
    if kind == "contract":
        ids = data.details.get("vehicle_ids") or [data.vehicle_id]
        if (
            not isinstance(ids, list)
            or not ids
            or len(ids) != int(data.details.get("quantity", 1))
            or len(set(ids)) != len(ids)
        ):
            raise HTTPException(400, "Sözleşme araç listesi adetle eşleşmeli ve benzersiz olmalı.")
        for vid in ids:
            vehicle(db, ctx, vid)
    if data.details.get("document_file_id"):
        try:
            fid = int(data.details["document_file_id"])
        except (ValueError, TypeError):
            raise HTTPException(400, "Belge kimliği geçersiz.")
        doc = db.get(m.VehicleFile, fid)
        if not doc or doc.vehicle_id != data.vehicle_id or doc.category != "document":
            raise HTTPException(404, "Araç belgesi bulunamadı.")
    if kind == "policy":
        if data.details.get("policy_type") not in {
            "Kasko",
            "Trafik",
            "Ferdi Kaza",
            "İMM",
            "Cam",
            "Diğer",
        }:
            raise HTTPException(400, "Poliçe türü seçin.")
        if not str(data.details.get("policy_no", "")).strip() or not data.end_date:
            raise HTTPException(400, "Poliçe numarası ve bitiş tarihi gerekli.")
    if kind == "invoice":
        if data.details.get("direction") not in {"gelir", "gider"}:
            raise HTTPException(400, "Fatura yönünü seçin.")
        if not str(data.details.get("invoice_no", "")).strip():
            raise HTTPException(400, "Fatura numarası gerekli.")
        if data.amount <= 0:
            raise HTTPException(400, "Fatura tutarı sıfırdan büyük olmalı.")
        if parent and parent.kind not in {"contract", "sale", "return"}:
            raise HTTPException(400, "Fatura sözleşmeye bağlanabilir.")
        net = data.details.get("net_amount")
        tax = data.details.get("tax_rate")
        if net not in (None, "") or tax not in (None, ""):
            if net in (None, "") or tax in (None, ""):
                raise HTTPException(400, "Net tutar ve vergi oranını birlikte girin.")
            net = number_detail(data.details, "net_amount", minimum=0.01)
            rate = number_detail(data.details, "tax_rate")
            if rate > 100 or round(net * (1 + rate / 100), 2) != round(data.amount, 2):
                raise HTTPException(
                    400,
                    "Net tutar + vergi fatura toplamına eşit olmalı; vergi oranı en fazla %100.",
                )
        allocations = data.details.get("vehicle_allocations")
        if allocations:
            if not isinstance(allocations, list) or len(allocations) > 10000:
                raise HTTPException(400, "Araç dağılımı listesi geçersiz.")
            seen = set()
            total = 0
            for part in allocations:
                if not isinstance(part, dict):
                    raise HTTPException(400, "Araç dağılımı geçersiz.")
                vid = part.get("vehicle_id")
                vehicle(db, ctx, vid)
                if vid in seen:
                    raise HTTPException(400, "Araç dağılımında tekrar var.")
                seen.add(vid)
                total += number_detail(part, "amount", minimum=0.01)
            if round(total, 2) != round(data.amount, 2):
                raise HTTPException(400, "Araç dağılımı fatura toplamına eşit olmalı.")
        reference = data.details.get("source_reference")
        if reference:
            try:
                source_kind, source_id = reference.split(":", 1)
                source_id = int(source_id)
            except (ValueError, AttributeError):
                raise HTTPException(400, "Gider bağlantısı geçersiz.")
            if source_kind in {"fuel", "hgs", "service"}:
                model = {"fuel": m.VehicleExpense, "hgs": m.HgsTransaction, "service": m.Request}[
                    source_kind
                ]
                source = db.get(model, source_id)
                if not source:
                    raise HTTPException(404, "Gider kaydı bulunamadı.")
                vehicle(db, ctx, source.vehicle_id)
            elif source_kind in {"policy", "damage", "fine"}:
                source = operation(db, ctx, source_id)
                if source.kind != source_kind:
                    raise HTTPException(400, "Gider türü eşleşmiyor.")
            else:
                raise HTTPException(400, "Gider kaynağı geçersiz.")
            if data.details.get("direction") != "gider":
                raise HTTPException(
                    400, "Gider bağlantısı yalnız gider faturasında kullanılabilir."
                )
            if source.vehicle_id != data.vehicle_id:
                raise HTTPException(400, "Gider kaynağı ve fatura aracı eşleşmeli.")
    if kind == "payment":
        if (
            not parent
            or parent.kind != "invoice"
            or parent.status not in {"Kesildi", "Kısmen Ödendi"}
        ):
            raise HTTPException(400, "Ödeme için açık bir fatura seçin.")
        paid = sum(
            r.amount
            for r in db.query(m.SupplierOperation)
            .filter_by(parent_id=parent.id, kind="payment")
            .all()
        )
        if data.amount <= 0 or round(paid + data.amount, 2) > round(parent.amount, 2):
            raise HTTPException(400, "Ödeme tutarı açık bakiyeyi aşamaz.")
    if kind == "approval" and not parent:
        raise HTTPException(400, "Onay için üst işlem gerekli.")
    if kind == "approval" and (
        data.details.get("target_version") != parent.version
        or data.details.get("target_amount") != parent.amount
    ):
        raise HTTPException(400, "Onay tutarı ve sürümü üst kayıtla eşleşmeli.")
    if kind == "scenario":
        count = number_detail(data.details, "vehicle_count", minimum=1)
        electric = number_detail(data.details, "electric_count")
        if not count.is_integer() or not electric.is_integer() or electric > count:
            raise HTTPException(
                400, "Araç adetleri tam sayı olmalı; elektrikli adet toplamı aşamaz."
            )
        number_detail(data.details, "monthly_unit_cost", minimum=0)
    return v, parent


def audit(db, ctx, record, title, details=None):
    db.add(
        m.SupplierOperationEvent(
            operation_id=record.id,
            supplier_id=ctx["id"],
            title=title,
            actor=ctx["actor"],
            details=details or {},
            created_at=stamp(),
        )
    )


def append_record(db, ctx, kind, data):
    v, parent = validate_record(db, ctx, kind, data)
    if kind == "sale":
        from app.vehicle_sales import validate

        validate(db, ctx, data)
    if kind == "delivery":
        from app.rental_lifecycle import rental_for

        rental = rental_for(db, ctx, data.parent_id, data.vehicle_id)
        if rental.status != "Teslim Bekliyor" or rental.delivery_id:
            raise HTTPException(
                409, "Bu araç kiralaması için teslimat zaten planlanmış veya tamamlanmış."
            )
    if kind == "return":
        from app.rental_lifecycle import rental_for, validate_return

        validate_return(db, ctx, data)
        return_rental = rental_for(db, ctx, data.parent_id, data.vehicle_id)
    if data.customer_id is None and v and kind == "fine":
        from app.event_responsibility import resolve

        match = resolve(
            db, ctx["id"], v.id, data.details.get("occurred_at") or data.date.isoformat()
        )
        data.customer_id = match["customer_id"]
        data.details = {
            **data.details,
            "responsibility_status": match["responsibility_status"],
            "rental_id": match["rental_id"],
        }
    if data.customer_id is None and v and v.customer_id and kind in {"policy", "damage"}:
        data.customer_id = v.customer_id
    if kind == "invoice":
        duplicate = [
            r
            for r in db.query(m.SupplierOperation)
            .filter_by(supplier_id=ctx["id"], kind="invoice")
            .all()
            if r.status != "İptal" and r.details.get("invoice_no") == data.details["invoice_no"]
        ]
        if duplicate:
            raise HTTPException(409, "Bu fatura numarası zaten kayıtlı.")
    row = m.SupplierOperation(
        supplier_id=ctx["id"],
        kind=kind,
        number=f"pending-{secrets.token_hex(12)}",
        title=data.title,
        customer_id=data.customer_id,
        vehicle_id=data.vehicle_id,
        parent_id=data.parent_id,
        date=data.date.isoformat(),
        end_date=data.end_date.isoformat() if data.end_date else None,
        amount=round(data.amount, 2),
        details=data.details,
        status=INITIAL[kind],
        created_at=stamp(),
        updated_at=stamp(),
    )
    if kind == "policy" and row.amount > settings(db, ctx["id"])["approval_threshold"]:
        row.status = "Taslak"
    db.add(row)
    db.flush()
    if kind == "invoice":
        db.add(
            m.InvoiceIdentity(
                supplier_id=ctx["id"], invoice_no=data.details["invoice_no"], operation_id=row.id
            )
        )
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Fatura numarası daha önce kullanılmış.")
    if kind == "sale":
        from app.vehicle_sales import created

        created(db, ctx, row)
    if kind == "contract":
        from app.rental_lifecycle import attach

        attach(db, ctx, row)
        if parent:
            db.add(m.ContractOfferLink(offer_id=parent.id, contract_id=row.id))
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                raise HTTPException(409, "Teklif için sözleşme zaten oluşturulmuş.")
    row.number = f"{PREFIXES[kind]}-{business_today().year}-{row.id:06d}"
    if kind == "offer":
        from app.offer_history import capture

        capture(db, row)
    audit(db, ctx, row, "Kayıt oluşturuldu")
    if kind == "payment":
        # Database compare-and-swap prevents two concurrent payments from exceeding the same balance.
        locked = (
            db.query(m.SupplierOperation)
            .filter_by(id=parent.id, version=parent.version)
            .update({m.SupplierOperation.version: parent.version + 1}, synchronize_session=False)
        )
        if locked != 1:
            db.rollback()
            raise HTTPException(409, "Fatura değişti. Bakiyeyi yenileyin.")
        paid = sum(
            r.amount
            for r in db.query(m.SupplierOperation)
            .filter_by(parent_id=parent.id, kind="payment")
            .all()
        )
        parent.status = "Ödendi" if round(paid, 2) == round(parent.amount, 2) else "Kısmen Ödendi"
        parent.updated_at = stamp()
        audit(db, ctx, parent, "Ödeme kaydedildi", {"payment_id": row.id, "amount": row.amount})
    if kind == "delivery":
        locked = (
            db.query(m.Rental)
            .filter_by(
                id=rental.id, version=rental.version, delivery_id=None, status="Teslim Bekliyor"
            )
            .update(
                {"delivery_id": row.id, "version": rental.version + 1}, synchronize_session=False
            )
        )
        if locked != 1:
            db.rollback()
            raise HTTPException(409, "Araç teslimat planı başka işlemle değişti.")
    if kind == "return":
        locked = (
            db.query(m.Rental)
            .filter_by(
                id=return_rental.id, version=return_rental.version, return_id=None, status="Aktif"
            )
            .update(
                {"return_id": row.id, "version": return_rental.version + 1},
                synchronize_session=False,
            )
        )
        if locked != 1:
            db.rollback()
            raise HTTPException(409, "Araç için iade zaten açılmış.")
    if kind == "policy":
        sync_policy(db, ctx, row)
    if (
        kind not in {"payment", "approval", "scenario"}
        and row.amount > settings(db, ctx["id"])["approval_threshold"]
    ):
        approval = m.SupplierOperation(
            supplier_id=ctx["id"],
            kind="approval",
            number=f"pending-{secrets.token_hex(12)}",
            title=f"{row.number} onayı",
            customer_id=row.customer_id,
            vehicle_id=row.vehicle_id,
            parent_id=row.id,
            date=business_today().isoformat(),
            amount=row.amount,
            status="Beklemede",
            details={"target_version": 1, "target_amount": row.amount},
            created_at=stamp(),
            updated_at=stamp(),
        )
        db.add(approval)
        db.flush()
        approval.number = f"ONY-{business_today().year}-{approval.id:06d}"
        audit(db, ctx, approval, "Onay talebi oluşturuldu")
    return row


def sync_policy(db, ctx, row):
    if row.details.get("policy_type") not in {"Kasko", "Trafik"} or row.status != "Aktif":
        return
    v = vehicle(db, ctx, row.vehicle_id)
    if row.end_date < business_today().isoformat():
        return
    prefix = "casco" if row.details["policy_type"] == "Kasko" else "traffic_insurance"
    existing = getattr(
        v, "casco_insurance_expiry_date" if prefix == "casco" else "traffic_insurance_expiry_date"
    )
    if existing and existing > row.end_date:
        return
    setattr(
        v,
        "casco_policy_no" if prefix == "casco" else "traffic_insurance_policy_no",
        row.details["policy_no"],
    )
    setattr(
        v,
        "casco_insurance_expiry_date" if prefix == "casco" else "traffic_insurance_expiry_date",
        row.end_date,
    )


def display_status(row):
    if (
        row.kind == "policy"
        and row.status == "Aktif"
        and row.end_date < business_today().isoformat()
    ):
        return "Süresi Doldu"
    if (
        row.kind == "delivery"
        and row.status == "Planlandı"
        and row.date < business_today().isoformat()
    ):
        return "Gecikti"
    if (
        row.kind == "offer"
        and row.status in {"Taslak", "Beklemede"}
        and row.end_date
        and row.end_date < business_today().isoformat()
    ):
        return "Süresi Doldu"
    if (
        row.kind == "contract"
        and row.status == "Aktif"
        and row.end_date < business_today().isoformat()
    ):
        return "Süresi Doldu"
    return row.status


def serialize(db, row):
    c = db.get(m.Customer, row.customer_id) if row.customer_id else None
    v = db.get(m.Vehicle, row.vehicle_id) if row.vehicle_id else None
    paid = (
        sum(
            r.amount
            for r in db.query(m.SupplierOperation).filter_by(parent_id=row.id, kind="payment").all()
        )
        if row.kind == "invoice"
        else 0
    )
    actions = TRANSITIONS.get(row.kind, {}).get(row.status, [])
    status = display_status(row)
    if row.kind in {"contract", "policy"} and row.status == "Aktif" and row.end_date:
        remaining = (date.fromisoformat(row.end_date) - business_today()).days
        if 0 <= remaining <= settings(db, row.supplier_id)["renewal_days"]:
            status = "Yenilenecek" if row.kind == "contract" else "Yaklaşıyor"
    if (
        row.kind == "invoice"
        and row.status in {"Kesildi", "Kısmen Ödendi"}
        and row.end_date
        and row.end_date < business_today().isoformat()
        and round(row.amount - paid, 2) > 0
    ):
        status = "Gecikti"
    return {
        "id": row.id,
        "kind": row.kind,
        "source": "operation",
        "number": row.number,
        "title": row.title,
        "customer_id": row.customer_id,
        "customer_name": c.company_name if c else None,
        "vehicle_id": row.vehicle_id,
        "plate": v.plate if v else None,
        "vehicle_name": f'{v.brand or ""} {v.model or ""}'.strip() if v else None,
        "parent_id": row.parent_id,
        "date": row.date,
        "end_date": row.end_date,
        "amount": row.amount,
        "status": status,
        "raw_status": row.status,
        "details": row.details,
        "version": row.version,
        "created_at": row.created_at,
        "paid": round(paid, 2),
        "balance": round(row.amount - paid, 2) if row.kind == "invoice" else None,
        "actions": actions,
    }


def approval_needed(db, ctx, row, target):
    if (
        row.kind == "approval"
        or row.amount <= settings(db, ctx["id"])["approval_threshold"]
        or target not in {"Aktif", "Tamamlandı", "Kesildi", "Ödendi"}
    ):
        return
    approved = (
        db.query(m.SupplierOperation)
        .filter_by(parent_id=row.id, kind="approval", status="Onaylandı")
        .all()
    )
    if not any(
        r.details.get("target_amount") == row.amount
        and r.details.get("target_version") == row.version
        for r in approved
    ):
        raise HTTPException(
            400,
            "Güncel tutar ve sürüm için şirket sahibi onayı gerekli. Onay & Yetki ekranından talep oluşturun.",
        )
