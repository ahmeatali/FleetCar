"""Per-vehicle rental and assignment history underneath a shared commercial contract."""

from fastapi import HTTPException

from app import models as m
from app.common.time import stamp
from app.common.validation import number_detail
from app.supplier_context import vehicle


def contract_cars(db, ctx, row):
    links = db.query(m.ContractVehicle).filter_by(supplier_id=ctx["id"], contract_id=row.id).all()
    # Legacy single-vehicle records remain readable and acquire normalized links on activation.
    return (
        [vehicle(db, ctx, link.vehicle_id) for link in links]
        if links
        else [vehicle(db, ctx, row.vehicle_id)]
    )


def attach(db, ctx, row, vehicle_ids=None):
    ids = vehicle_ids or row.details.get("vehicle_ids") or [row.vehicle_id]
    if not isinstance(ids, list) or not ids or len(set(ids)) != len(ids):
        raise HTTPException(400, "Sözleşme araçları benzersiz olmalı.")
    cars = [vehicle(db, ctx, vid) for vid in ids]
    if row.vehicle_id not in ids:
        raise HTTPException(400, "Birincil araç sözleşme listesinde olmalı.")
    unit = number_detail(
        row.details, "unit_monthly_rent", default=row.amount / len(ids), minimum=0.01
    )
    if round(unit * len(ids), 2) != round(row.amount, 2):
        raise HTTPException(400, "Araç bedelleri sözleşme aylık toplamıyla eşleşmeli.")
    for car in sorted(cars, key=lambda car: car.id):
        from app.fleet_schedule import check_contract_reservations

        check_contract_reservations(db, ctx, car, row)
        if (
            db.query(m.SupplierOperation)
            .filter_by(supplier_id=ctx["id"], vehicle_id=car.id, kind="sale")
            .filter(m.SupplierOperation.status != "İptal")
            .first()
        ):
            raise HTTPException(400, "Satış dosyası bulunan araç kiralanamaz.")
        if not car.is_active or car.vehicle_group == "Satışta":
            raise HTTPException(400, "Sözleşme aracı kiralamaya uygun değil.")
        db.add(
            m.ContractVehicle(
                supplier_id=ctx["id"], contract_id=row.id, vehicle_id=car.id, monthly_rent=unit
            )
        )
    row.details = {
        **row.details,
        "vehicle_ids": ids,
        "quantity": len(ids),
        "unit_monthly_rent": unit,
    }


def activate(db, ctx, row):
    cars = contract_cars(db, ctx, row)
    for car in sorted(cars, key=lambda car: car.id):
        from app.fleet_schedule import check_contract_reservations

        check_contract_reservations(db, ctx, car, row)
        # Lock before checking current assignment; a second activation must see the committed state.
        db.query(m.Vehicle).filter_by(
            id=car.id, supplier_id=ctx["id"]
        ).populate_existing().with_for_update().first()
        collision = (
            db.query(m.Rental)
            .filter(
                m.Rental.supplier_id == ctx["id"],
                m.Rental.vehicle_id == car.id,
                m.Rental.status.notin_(["Tamamlandı", "İptal"]),
                m.Rental.contract_id != row.id,
            )
            .first()
        )
        legacy = (
            db.query(m.SupplierOperation)
            .filter_by(supplier_id=ctx["id"], kind="contract", vehicle_id=car.id, status="Aktif")
            .filter(m.SupplierOperation.id != row.id)
            .first()
        )
        if collision or legacy or car.customer_id and car.customer_id != row.customer_id:
            raise HTTPException(409, "Sözleşme araçlarından biri başka kiralama/müşteriye bağlı.")
        if (
            not car.is_active
            or car.status in {"Servis", "Serviste", "Hasar", "Kaza"}
            or car.vehicle_group == "Satışta"
        ):
            raise HTTPException(400, "Sözleşme araçlarından biri kiralamaya uygun değil.")
    from app.signature_documents import ensure_signed

    proof = ensure_signed(db, row)
    source_offer = db.get(m.SupplierOperation, row.parent_id) if row.parent_id else None
    quote = (
        db.get(m.Quote, (source_offer.details or {}).get("quote_id"))
        if source_offer and source_offer.details.get("quote_id")
        else None
    )
    if quote and quote.customer_id == row.customer_id:
        quote.status = "Sözleşme İmzalandı"
        quote.contract_amount = round(row.amount * int(row.details.get("months", 12)), 2)
        db.get(m.Customer, row.customer_id).signed_at = proof.signed_date
    if not db.query(m.ContractVehicle).filter_by(contract_id=row.id).first():
        attach(db, ctx, row)
    for car in cars:
        from app.tenant_visibility import clear_customer_projection

        for prior in db.query(m.VehicleAssignment).filter_by(vehicle_id=car.id, ends_at=None).all():
            prior.ends_at = stamp()
        clear_customer_projection(car)
        link = db.query(m.ContractVehicle).filter_by(contract_id=row.id, vehicle_id=car.id).first()
        rental = m.Rental(
            supplier_id=ctx["id"],
            customer_id=row.customer_id,
            contract_id=row.id,
            vehicle_id=car.id,
            status="Teslim Bekliyor",
            starts_at=row.date,
            ends_at=row.end_date,
        )
        db.add(rental)
        db.flush()
        db.add(
            m.VehicleAssignment(
                supplier_id=ctx["id"],
                customer_id=row.customer_id,
                vehicle_id=car.id,
                rental_id=rental.id,
                starts_at=stamp(),
                driver_name=row.details.get("driver"),
            )
        )
        car.customer_id = row.customer_id
        car.contract_no = row.number
        car.contract_start_date = row.date
        car.contract_end_date = row.end_date
        car.monthly_rent = link.monthly_rent
        car.contract_duration_months = int(row.details.get("months", 12))
        car.contract_committed_km = int(row.details.get("annual_km", 0))
        car.monthly_km_limit = int(car.contract_committed_km / 12)
        car.contract_signed_at = proof.signed_date


def rental_for(db, ctx, contract_id, vehicle_id):
    row = (
        db.query(m.Rental)
        .filter_by(supplier_id=ctx["id"], contract_id=contract_id, vehicle_id=vehicle_id)
        .first()
    )
    if not row:
        raise HTTPException(404, "Araç kiralaması bulunamadı.")
    return row


def delivered(db, ctx, row):
    rental = rental_for(db, ctx, row.parent_id, row.vehicle_id)
    if rental.status != "Teslim Bekliyor":
        raise HTTPException(409, "Araç için teslim kaydı zaten tamamlanmış veya kiralama kapanmış.")
    rental.status = "Aktif"
    rental.delivery_id = row.id
    rental.delivered_at = row.details.get("delivered_at") or stamp()
    rental.version += 1
    assignment = db.query(m.VehicleAssignment).filter_by(rental_id=rental.id).first()
    if assignment and row.details.get("driver_name"):
        assignment.driver_name = row.details["driver_name"]
    row.details = {
        **row.details,
        "delivered_at": rental.delivered_at,
        "condition_reference": {
            key: row.details.get(key)
            for key in [
                "mileage",
                "fuel_level",
                "tire_depth",
                "existing_damage",
                "equipment",
                "photos",
                "receiver",
                "issuer",
                "checks",
            ]
        },
    }


def close(db, ctx, row, status):
    rentals = db.query(m.Rental).filter_by(supplier_id=ctx["id"], contract_id=row.id).all()
    if any(r.status not in {"Tamamlandı", "İptal", "Teslim Bekliyor"} for r in rentals):
        raise HTTPException(400, "Teslim edilmiş araçları önce iade ve mutabakatla kapatın.")
    for rental in rentals:
        if rental.status == "Teslim Bekliyor":
            rental.status = "İptal"
            rental.version += 1
        for assignment in (
            db.query(m.VehicleAssignment).filter_by(rental_id=rental.id, ends_at=None).all()
        ):
            assignment.ends_at = stamp()
    for car in contract_cars(db, ctx, row):
        if car.contract_no == row.number:
            car.customer_id = None
            car.contract_no = None
            car.contract_start_date = None
            car.contract_end_date = None
            car.monthly_rent = None
            car.monthly_km_limit = None


def validate_return(db, ctx, data):
    rental = rental_for(db, ctx, data.parent_id, data.vehicle_id)
    if rental.status != "Aktif" or rental.return_id:
        raise HTTPException(400, "İade yalnız teslim edilmiş aktif kiralama için oluşturulabilir.")
    if rental.delivered_at and data.date.isoformat() < rental.delivered_at[:10]:
        raise HTTPException(400, "İade teslimden önce olamaz.")
    existing = (
        db.query(m.SupplierOperation)
        .filter_by(
            supplier_id=ctx["id"],
            kind="return",
            parent_id=data.parent_id,
            vehicle_id=data.vehicle_id,
        )
        .filter(m.SupplierOperation.status != "İptal")
        .first()
    )
    if existing:
        raise HTTPException(409, "Bu araç için iade kaydı zaten var.")


def return_status(db, ctx, row, target):
    rental = rental_for(db, ctx, row.parent_id, row.vehicle_id)
    car = vehicle(db, ctx, row.vehicle_id)
    delivery = db.get(m.SupplierOperation, rental.delivery_id)
    if not delivery:
        raise HTTPException(400, "Teslim referansı bulunamadı.")
    if target == "İnceleniyor":
        rental.status = "İade Bekliyor"
        rental.return_id = row.id
        rental.version += 1
    if target == "Mutabakat Bekliyor":
        km = number_detail(row.details, "mileage", minimum=car.mileage or 0)
        if not km.is_integer():
            raise HTTPException(400, "İade kilometresi tam sayı olmalı.")
        if not row.details.get("receiver") or not row.details.get("location"):
            raise HTTPException(400, "İade alan ve konum gerekli.")
        checks = row.details.get("checks", {})
        if not all(
            checks.get(k) is True for k in ["exterior", "interior", "documents", "equipment"]
        ):
            raise HTTPException(400, "İade kontrol listesini tamamlayın.")
        number_detail(row.details, "fuel_level")
        number_detail(row.details, "damage_charge")
        number_detail(row.details, "fuel_charge")
        months = number_detail(
            db.get(m.SupplierOperation, row.parent_id).details, "months", default=12, minimum=1
        )
        # Contracted kilometres apply to the agreed term, not an invented daily proration.
        contract = db.get(m.SupplierOperation, row.parent_id)
        limit = number_detail(contract.details, "annual_km") * months / 12
        driven = km - number_detail(delivery.details, "mileage")
        excess = max(0, driven - limit)
        fee = number_detail(contract.details, "excess_km_fee")
        total = round(
            excess * fee
            + number_detail(row.details, "damage_charge")
            + number_detail(row.details, "fuel_charge"),
            2,
        )
        row.amount = total
        row.details = {
            **row.details,
            "delivery_id": delivery.id,
            "delivery_reference": delivery.details.get("condition_reference") or delivery.details,
            "driven_km": driven,
            "contract_km_limit": limit,
            "excess_km": excess,
            "excess_km_charge": round(excess * fee, 2),
            "settlement_total": total,
        }
        rental.status = "İade İncelemede"
        rental.version += 1
    if target == "Tamamlandı":
        if ctx["role"] not in {"owner", "finance"}:
            raise HTTPException(403, "Son mutabakatı finans veya şirket sahibi onaylar.")
        if row.details.get("destination") not in {"Havuzda", "Serviste", "Satışta"}:
            raise HTTPException(400, "İade sonrası araç hedefi seçin.")
        if not row.details.get("settlement_note"):
            raise HTTPException(400, "Son mutabakat açıklaması gerekli.")
        rental.status = "Tamamlandı"
        rental.returned_at = row.details.get("returned_at") or stamp()
        rental.version += 1
        car.mileage = int(number_detail(row.details, "mileage", minimum=car.mileage or 0))
        db.add(
            m.VehicleMileageRecord(
                vehicle_id=car.id,
                mileage=car.mileage,
                source="supplier_return",
                recorded_at=rental.returned_at,
            )
        )
        for assignment in (
            db.query(m.VehicleAssignment).filter_by(rental_id=rental.id, ends_at=None).all()
        ):
            assignment.ends_at = rental.returned_at
        if car.contract_no == db.get(m.SupplierOperation, row.parent_id).number:
            from app.tenant_visibility import clear_customer_projection

            clear_customer_projection(car)
            car.customer_id = None
            db.add(
                m.VehicleAssignment(
                    supplier_id=ctx["id"],
                    customer_id=None,
                    vehicle_id=car.id,
                    rental_id=None,
                    starts_at=rental.returned_at,
                )
            )
        car.status = "Serviste" if row.details["destination"] == "Serviste" else "Aktif"
        if row.details["destination"] == "Satışta":
            car.vehicle_group = "Satışta"
        row.details = {**row.details, "settled_at": stamp(), "settled_by": ctx["actor"]}
    if target == "İptal":
        rental.status = "Aktif"
        rental.return_id = None
        rental.version += 1


def driver_changed(db, car, name):
    rental = (
        db.query(m.Rental)
        .filter(m.Rental.vehicle_id == car.id, m.Rental.status.notin_(["Tamamlandı", "İptal"]))
        .first()
    )
    if not rental:
        return
    now = stamp()
    for assignment in (
        db.query(m.VehicleAssignment).filter_by(rental_id=rental.id, ends_at=None).all()
    ):
        assignment.ends_at = now
    db.add(
        m.VehicleAssignment(
            supplier_id=rental.supplier_id,
            customer_id=rental.customer_id,
            vehicle_id=car.id,
            rental_id=rental.id,
            driver_name=name,
            starts_at=now,
        )
    )
