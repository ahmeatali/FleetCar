"""Vehicle disposal reserves stock and preserves the completed commercial record."""

from fastapi import HTTPException

from app import models as m
from app.common.time import stamp
from app.common.validation import number_detail
from app.supplier_context import vehicle


def validate(db, ctx, data, current=None):
    car = vehicle(db, ctx, data.vehicle_id)
    if (
        car.customer_id
        or db.query(m.Rental)
        .filter(
            m.Rental.vehicle_id == car.id,
            m.Rental.supplier_id == ctx["id"],
            m.Rental.status.notin_(["Tamamlandı", "İptal"]),
        )
        .first()
    ):
        raise HTTPException(409, "Kiralaması veya müşteri ataması süren araç satışa ayrılamaz.")
    active = (
        db.query(m.SupplierOperation)
        .filter_by(supplier_id=ctx["id"], vehicle_id=car.id, kind="sale")
        .filter(m.SupplierOperation.status != "İptal")
    )
    if current:
        active = active.filter(m.SupplierOperation.id != current)
    if active.first():
        raise HTTPException(409, "Araç için satış dosyası zaten var.")
    if data.amount <= 0:
        raise HTTPException(400, "Satış hedef fiyatı sıfırdan büyük olmalı.")
    number_detail(data.details, "sale_price")
    number_detail(data.details, "offer_price")


def created(db, ctx, row):
    car = vehicle(db, ctx, row.vehicle_id)
    db.add(
        m.VehicleSale(
            supplier_id=ctx["id"],
            vehicle_id=car.id,
            operation_id=row.id,
            previous_group=car.vehicle_group,
        )
    )
    car.vehicle_group = "Satışta"


def transition(db, ctx, row, target):
    car = vehicle(db, ctx, row.vehicle_id)
    sale = db.query(m.VehicleSale).filter_by(operation_id=row.id, supplier_id=ctx["id"]).first()
    if not sale:
        raise HTTPException(404, "Satış dosyası bulunamadı.")
    if target in {"İlanda", "Teklif Alındı", "Satıldı"} and not row.details.get(
        "expertise_reference"
    ):
        raise HTTPException(400, "Ekspertiz raporu referansı gerekli.")
    if target == "Teklif Alındı":
        if number_detail(row.details, "offer_price", minimum=0.01) <= 0 or not row.details.get(
            "buyer_name"
        ):
            raise HTTPException(400, "Alıcı ve teklif bedeli gerekli.")
    if target == "Satıldı":
        if ctx["role"] != "owner":
            raise HTTPException(403, "Satışı şirket sahibi kesinleştirir.")
        amount = number_detail(row.details, "sale_price", minimum=0.01)
        if (
            not row.customer_id
            or not row.details.get("buyer_name")
            or not row.details.get("sale_document")
        ):
            raise HTTPException(400, "Alıcı müşteri, alıcı adı ve satış belge referansı gerekli.")
        if car.customer_id:
            raise HTTPException(409, "Müşteriye atanmış araç satılamaz.")
        sale.buyer_id = row.customer_id
        sale.sold_at = stamp()
        car.is_active = False
        car.status = "Satıldı"
        row.amount = round(amount, 2)
        row.details = {**row.details, "sold_at": sale.sold_at, "approved_by": ctx["actor"]}
    if target == "İptal":
        car.vehicle_group = sale.previous_group
