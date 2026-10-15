"""Customer visibility follows the event's assignment period, not the car's current renter."""

from app import models as m
from app.common.time import business_today, interval_contains


def customer_vehicle_ids(db, cid):
    return {row[0] for row in db.query(m.Vehicle.id).filter_by(customer_id=cid).all()} | {
        row[0] for row in db.query(m.VehicleAssignment.vehicle_id).filter_by(customer_id=cid).all()
    }


def event_visible(db, cid, vid, when, kind=None, source_id=None):
    if cid is None:
        return True
    override = (
        db.query(m.EventResponsibility).filter_by(source_kind=kind, source_id=source_id).first()
        if kind in {"fuel", "hgs"} and source_id
        else None
    )
    if override:
        return override.customer_id == cid
    car = db.get(m.Vehicle, vid)
    if not car:
        return False
    assignments = db.query(m.VehicleAssignment).filter_by(vehicle_id=vid).all()
    if not assignments:
        return (
            car.customer_id == cid
        )  # Historical single-owner records retain their original visibility.
    moment = str(when or "")
    candidates = []
    for row in assignments:
        rental = db.get(m.Rental, row.rental_id) if row.rental_id else None
        if rental and not rental.delivered_at:
            continue
        start = (
            max(row.starts_at, rental.delivered_at)
            if rental and rental.delivered_at
            else row.starts_at
        )
        hit = interval_contains(start, row.ends_at, moment)
        if hit:
            candidates.append(row)
    return bool(candidates) and {a.customer_id for a in candidates} == {cid}


NEUTRAL_DOCUMENTS = {"Ruhsat", "Trafik Sigortası", "Kasko", "Muayene"}


def file_visible(db, cid, record):
    car = db.get(m.Vehicle, record.vehicle_id)
    if not car:
        return False
    scope = db.get(m.VehicleFileScope, record.id)
    if scope and scope.visibility == "customer":
        return scope.customer_id == cid
    if scope and scope.visibility == "asset":
        return car.customer_id == cid
    if scope and scope.visibility == "supplier":
        return any(
            row.details.get("document_file_id") == record.id
            for row in db.query(m.SupplierOperation)
            .filter(
                m.SupplierOperation.customer_id == cid,
                m.SupplierOperation.status.notin_(["Taslak", "İptal"]),
            )
            .all()
        )
    if event_visible(db, cid, car.id, record.uploaded_at):
        return True
    # Technical registration/coverage documents belong to the currently assigned asset.
    if car.customer_id == cid and record.document_type in NEUTRAL_DOCUMENTS:
        return True
    # Explicit case/invoice attachment remains accessible after the vehicle returns.
    return any(
        row.details.get("document_file_id") == record.id
        for row in db.query(m.SupplierOperation)
        .filter(
            m.SupplierOperation.customer_id == cid,
            m.SupplierOperation.kind.in_(["fine", "invoice"]),
            m.SupplierOperation.status.notin_(["Taslak", "İptal"]),
        )
        .all()
    )


def record_manual_assignment(db, car, new_customer):
    from app.common.time import stamp

    if car.customer_id == new_customer:
        return
    now = stamp()
    active = db.query(m.VehicleAssignment).filter_by(vehicle_id=car.id, ends_at=None).all()
    if not active:
        # Preserve the pre-existing relationship on first migration; do not silently reassign its events.
        db.add(
            m.VehicleAssignment(
                supplier_id=car.supplier_id,
                customer_id=car.customer_id,
                vehicle_id=car.id,
                rental_id=None,
                driver_name=car.assignment_user,
                starts_at=car.contract_start_date or "1970-01-01",
                ends_at=now,
            )
        )
    for row in active:
        row.ends_at = now
    db.add(
        m.VehicleAssignment(
            supplier_id=car.supplier_id,
            customer_id=new_customer,
            vehicle_id=car.id,
            rental_id=None,
            driver_name=None,
            starts_at=now,
        )
    )


def clear_customer_projection(car):
    for key in [
        "contract_no",
        "contract_start_date",
        "contract_end_date",
        "contract_duration_months",
        "contract_committed_km",
        "contract_signed_at",
        "monthly_rent",
        "monthly_km_limit",
        "assignment_user",
        "operating_company",
        "received_by",
        "delivered_by",
        "delivery_date",
        "delivery_location",
        "delivery_notes",
    ]:
        if hasattr(car, key):
            setattr(car, key, None)


def customer_vehicle_projection(db, car, data, cid):
    if cid is None:
        return data
    if not event_visible(db, cid, car.id, car.gps_last_seen_at):
        for key in ["gps_latitude", "gps_longitude", "gps_location_label", "gps_last_seen_at"]:
            data[key] = None
    history = db.query(m.VehicleAssignment).filter_by(vehicle_id=car.id).first()
    if history:
        points = [
            p
            for p in db.query(m.VehicleMileageRecord)
            .filter_by(vehicle_id=car.id)
            .order_by(m.VehicleMileageRecord.recorded_at)
            .all()
            if event_visible(db, cid, car.id, p.recorded_at)
        ]
        month = business_today().strftime("%Y-%m")
        current = [p for p in points if p.recorded_at[:7] == month]
        before = [p for p in points if p.recorded_at[:7] < month]
        data["current_month_km"] = (
            max(0, current[-1].mileage - (before[-1].mileage if before else current[0].mileage))
            if current and (before or len(current) > 1)
            else None
        )
    return data
