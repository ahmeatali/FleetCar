"""Supplier-scoped scheduling and shared collision rules for reservations/contracts."""

from fastapi import HTTPException
from sqlalchemy import or_

from app import models as m
from app.common.time import business_today


def schedule_lock(db, sid):
    # A database write serializes SQLite writers too (FOR UPDATE alone does not).
    db.query(m.Supplier).filter_by(id=sid).update(
        {m.Supplier.name: m.Supplier.name}, synchronize_session=False
    )


def blocks(db, sid, vid, start, end, exclude_reservation=None, exclude_contract=None):
    result = []
    reservations = (
        db.query(m.FleetReservation)
        .filter(
            m.FleetReservation.supplier_id == sid,
            m.FleetReservation.vehicle_id == vid,
            m.FleetReservation.status == "Onaylandı",
            m.FleetReservation.start_date <= end,
            m.FleetReservation.end_date >= start,
        )
        .all()
    )
    for row in reservations:
        if row.id != exclude_reservation:
            result.append(
                {
                    "kind": "reservation",
                    "id": row.id,
                    "start": row.start_date,
                    "end": row.end_date,
                    "label": f"Rezervasyon #{row.id}",
                }
            )
    contracts = (
        db.query(m.SupplierOperation)
        .filter(
            m.SupplierOperation.supplier_id == sid,
            m.SupplierOperation.kind == "contract",
            m.SupplierOperation.status.in_(["Taslak", "Aktif"]),
            m.SupplierOperation.date <= end,
            m.SupplierOperation.end_date >= start,
            or_(
                m.SupplierOperation.vehicle_id == vid,
                m.SupplierOperation.id.in_(
                    db.query(m.ContractVehicle.contract_id).filter_by(
                        supplier_id=sid, vehicle_id=vid
                    )
                ),
            ),
        )
        .all()
    )
    for row in contracts:
        if row.id == exclude_contract:
            continue
        rental = (
            db.query(m.Rental)
            .filter_by(supplier_id=sid, contract_id=row.id, vehicle_id=vid)
            .first()
        )
        if rental and rental.status in {"Tamamlandı", "İptal"}:
            continue
        result.append(
            {
                "kind": "contract",
                "id": row.id,
                "start": row.date,
                "end": row.end_date,
                "label": row.number,
            }
        )
    # Overdue, unreturned vehicles remain occupied beyond their planned end date.
    for rental in (
        db.query(m.Rental)
        .filter(
            m.Rental.supplier_id == sid,
            m.Rental.vehicle_id == vid,
            m.Rental.status.notin_(["Tamamlandı", "İptal", "Teslim Bekliyor"]),
            m.Rental.ends_at < business_today().isoformat(),
        )
        .all()
    ):
        existing = next(
            (r for r in result if r["kind"] == "contract" and r["id"] == rental.contract_id), None
        )
        if rental.contract_id == exclude_contract:
            continue
        if existing:
            existing["end"] = max(existing["end"], end)
            existing["label"] = "İadesi geciken kiralama"
        else:
            result.append(
                {
                    "kind": "contract",
                    "id": rental.contract_id,
                    "start": rental.starts_at,
                    "end": end,
                    "label": "İadesi geciken kiralama",
                }
            )
    return result


def available(db, ctx, car, start, end, check_blocks=True, **exclude):
    if (
        not car.is_active
        or car.status in {"Servis", "Serviste", "Hasar", "Kaza", "Satıldı"}
        or car.vehicle_group == "Satışta"
    ):
        raise HTTPException(409, "Araç aktif ve kiralamaya uygun durumda olmalı.")
    if (
        db.query(m.SupplierOperation)
        .filter_by(supplier_id=ctx["id"], kind="sale", vehicle_id=car.id)
        .filter(m.SupplierOperation.status != "İptal")
        .first()
    ):
        raise HTTPException(409, "Satış dosyası bulunan araç rezerve edilemez.")
    if check_blocks and blocks(db, ctx["id"], car.id, start, end, **exclude):
        raise HTTPException(409, "Araç seçilen tarihlerde rezervasyon veya sözleşmeyle çakışıyor.")
    if (
        car.customer_id
        and not db.query(m.Rental)
        .filter_by(supplier_id=ctx["id"], vehicle_id=car.id)
        .filter(m.Rental.status.notin_(["Tamamlandı", "İptal"]))
        .first()
    ):
        raise HTTPException(
            409, "Aracın mevcut müşteri tahsisi önce kiralama kayıtlarıyla doğrulanmalı."
        )


def check_contract_reservations(db, ctx, car, row):
    schedule_lock(db, ctx["id"])
    if (
        db.query(m.FleetReservation)
        .filter(
            m.FleetReservation.supplier_id == ctx["id"],
            m.FleetReservation.vehicle_id == car.id,
            m.FleetReservation.status == "Onaylandı",
            m.FleetReservation.start_date <= row.end_date,
            m.FleetReservation.end_date >= row.date,
        )
        .first()
    ):
        raise HTTPException(
            409,
            "Sözleşme araç için onaylı rezervasyonla çakışıyor. Rezervasyondan sözleşme oluşturun.",
        )

    # A converted reservation is still protected by its draft contract.
    converted = (
        db.query(m.FleetReservation)
        .join(m.SupplierOperation, m.SupplierOperation.id == m.FleetReservation.contract_id)
        .filter(
            m.FleetReservation.supplier_id == ctx["id"],
            m.FleetReservation.vehicle_id == car.id,
            m.FleetReservation.status == "Sözleşmeye Dönüştü",
            m.SupplierOperation.status.in_(["Taslak", "Aktif"]),
            m.SupplierOperation.id != row.id,
            m.SupplierOperation.date <= row.end_date,
            m.SupplierOperation.end_date >= row.date,
        )
        .all()
    )
    for reservation in converted:
        rental = (
            db.query(m.Rental)
            .filter_by(
                supplier_id=ctx["id"], contract_id=reservation.contract_id, vehicle_id=car.id
            )
            .first()
        )
        if rental and rental.status in {"Tamamlandı", "İptal"}:
            continue
        raise HTTPException(409, "Araç rezervasyondan oluşturulan başka bir sözleşmeyle çakışıyor.")
