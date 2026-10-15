"""Branch locations, daily task queues and day-based reservation calendar."""

import secrets
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as m
from app.common.time import business_today, stamp
from app.database import get_db
from app.fleet_schedule import available, blocks, schedule_lock
from app.supplier_context import context, customer_ids, vehicle
from app.supplier_permissions import permit
from app.supplier_schemas import OperationInput

router = APIRouter(prefix="/api/supplier-workspace/fleet", tags=["Fleet operations"])


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class BranchInput(Input):
    name: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    address: str = Field("", max_length=500)
    is_active: bool = True
    version: int = Field(0, ge=0)


class LocationInput(Input):
    home_branch_id: int = Field(gt=0)
    current_branch_id: int = Field(gt=0)
    location_note: str = Field("", max_length=300)
    version: int = Field(0, ge=0)


class TaskInput(Input):
    title: str = Field(min_length=1, max_length=200)
    due_date: date
    vehicle_id: Optional[str] = None
    branch_id: Optional[int] = Field(None, gt=0)
    assignee_id: Optional[int] = Field(None, gt=0)
    note: str = Field("", max_length=2000)


class TaskUpdate(Input):
    due_date: Optional[date] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    assignee_id: Optional[int] = Field(None, gt=0)
    note: str = Field("", max_length=2000)
    status: Literal["Açık", "Devam Ediyor", "Tamamlandı"] = "Açık"
    version: int = Field(ge=0)


class ReservationInput(Input):
    customer_id: int = Field(gt=0)
    vehicle_id: str = Field(min_length=1, max_length=200)
    pickup_branch_id: int = Field(gt=0)
    return_branch_id: int = Field(gt=0)
    start_date: date
    end_date: date
    monthly_rent: float = Field(gt=0, le=100000000, allow_inf_nan=False, multiple_of=0.01)
    note: str = Field("", max_length=2000)

    @model_validator(mode="after")
    def valid_range(self):
        if self.start_date < business_today() or self.end_date < self.start_date:
            raise ValueError("Rezervasyon bugünden başlayabilir; bitiş başlangıçtan önce olamaz.")
        if (self.end_date - self.start_date).days > 1826:
            raise ValueError("Rezervasyon aralığı en fazla beş yıl olabilir.")
        return self


class VersionInput(Input):
    version: int = Field(gt=0)


def manage(ctx):
    if ctx["role"] not in {"owner", "fleet_manager"}:
        raise HTTPException(
            403, "Şube yönetimi için şirket sahibi veya filo yöneticisi yetkisi gerekli."
        )


def task_permit(ctx):
    if ctx["role"] not in {"owner", "fleet_manager", "operations", "delivery"}:
        raise HTTPException(403, "Operasyon görevlerini yönetme yetkiniz yok.")


def branch(db, sid, bid, active=True):
    row = db.query(m.FleetBranch).filter_by(id=bid, supplier_id=sid).first()
    if not row:
        raise HTTPException(404, "Şube bulunamadı.")
    if active and not row.is_active:
        raise HTTPException(400, "Pasif şube kullanılamaz.")
    return row


def member(db, sid, uid):
    if (
        uid
        and not db.query(m.SupplierPortalUser)
        .filter_by(id=uid, supplier_id=sid, is_active=True)
        .first()
    ):
        raise HTTPException(404, "Aktif şirket kullanıcısı bulunamadı.")


def save_version(db, model, row, expected, values):
    changed = (
        db.query(model)
        .filter_by(id=row.id, supplier_id=row.supplier_id, version=expected)
        .update({**values, "version": expected + 1}, synchronize_session=False)
    )
    if changed != 1:
        db.rollback()
        raise HTTPException(409, "Kayıt değişti. Yenileyip tekrar deneyin.")
    db.flush()
    db.refresh(row)


def branch_dict(row):
    return {k: getattr(row, k) for k in ("id", "name", "city", "address", "is_active", "version")}


@router.get("/overview")
def overview(ctx=Depends(context), db: Session = Depends(get_db)):
    branches = (
        db.query(m.FleetBranch).filter_by(supplier_id=ctx["id"]).order_by(m.FleetBranch.name).all()
    )
    locations = {
        r.vehicle_id: r
        for r in db.query(m.FleetVehicleLocation).filter_by(supplier_id=ctx["id"]).all()
    }
    cars = db.query(m.Vehicle).filter_by(supplier_id=ctx["id"]).all()
    return {
        "branches": [branch_dict(b) for b in branches],
        "vehicles": [
            {
                "id": v.id,
                "plate": v.plate,
                "brand": v.brand,
                "model": v.model,
                "group": v.vehicle_group or v.vehicle_segment or "",
                "status": v.status,
                "is_active": bool(v.is_active),
                "location": (
                    {
                        k: getattr(locations[v.id], k)
                        for k in (
                            "home_branch_id",
                            "current_branch_id",
                            "location_note",
                            "version",
                            "updated_at",
                            "updated_by",
                        )
                    }
                    if v.id in locations
                    else None
                ),
            }
            for v in cars
        ],
        "members": [
            {"id": u.id, "name": u.name}
            for u in db.query(m.SupplierPortalUser)
            .filter_by(supplier_id=ctx["id"], is_active=True)
            .all()
        ],
    }


@router.post("/branches")
def create_branch(data: BranchInput, ctx=Depends(context), db: Session = Depends(get_db)):
    manage(ctx)
    row = m.FleetBranch(supplier_id=ctx["id"], **data.model_dump(exclude={"version"}))
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu isimde şube zaten var.")
    return branch_dict(row)


@router.put("/branches/{bid}")
def update_branch(bid: int, data: BranchInput, ctx=Depends(context), db: Session = Depends(get_db)):
    manage(ctx)
    schedule_lock(db, ctx["id"])
    row = branch(db, ctx["id"], bid, False)
    if not data.is_active:
        if (
            db.query(m.FleetVehicleLocation)
            .filter(
                m.FleetVehicleLocation.supplier_id == ctx["id"],
                (m.FleetVehicleLocation.home_branch_id == bid)
                | (m.FleetVehicleLocation.current_branch_id == bid),
            )
            .first()
            or db.query(m.FleetReservation)
            .filter(
                m.FleetReservation.supplier_id == ctx["id"],
                m.FleetReservation.status == "Onaylandı",
                (m.FleetReservation.pickup_branch_id == bid)
                | (m.FleetReservation.return_branch_id == bid),
            )
            .first()
        ):
            raise HTTPException(
                409, "Bağlı araç veya açık rezervasyon bulunan şube pasife alınamaz."
            )
    save_version(db, m.FleetBranch, row, data.version, data.model_dump(exclude={"version"}))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu isimde şube zaten var.")
    return branch_dict(row)


@router.put("/locations/{vid}")
def save_location(
    vid: str, data: LocationInput, ctx=Depends(context), db: Session = Depends(get_db)
):
    permit(ctx, "vehicle")
    schedule_lock(db, ctx["id"])
    vehicle(db, ctx, vid)
    branch(db, ctx["id"], data.home_branch_id)
    branch(db, ctx["id"], data.current_branch_id)
    row = db.query(m.FleetVehicleLocation).filter_by(vehicle_id=vid).first()
    values = {
        **data.model_dump(exclude={"version"}),
        "updated_at": stamp(),
        "updated_by": ctx["actor"],
    }
    if row:
        if row.supplier_id != ctx["id"]:
            raise HTTPException(
                409, "Araç lokasyonu önceki şirket kaydına bağlı; şirket değişimi incelenmeli."
            )
        changed = (
            db.query(m.FleetVehicleLocation)
            .filter_by(vehicle_id=vid, supplier_id=ctx["id"], version=data.version)
            .update({**values, "version": data.version + 1}, synchronize_session=False)
        )
        if changed != 1:
            raise HTTPException(409, "Araç lokasyonu değişti. Yenileyin.")
    else:
        if data.version != 0:
            raise HTTPException(409, "Araç lokasyonu değişti. Yenileyin.")
        db.add(m.FleetVehicleLocation(vehicle_id=vid, supplier_id=ctx["id"], **values))
    db.commit()
    return overview(ctx, db)


def reservation_dict(row):
    return {
        k: getattr(row, k)
        for k in (
            "id",
            "customer_id",
            "vehicle_id",
            "pickup_branch_id",
            "return_branch_id",
            "start_date",
            "end_date",
            "monthly_rent",
            "note",
            "status",
            "contract_id",
            "version",
        )
    }


@router.get("/reservations")
def reservations(ctx=Depends(context), db: Session = Depends(get_db)):
    return [
        reservation_dict(r)
        for r in db.query(m.FleetReservation)
        .filter_by(supplier_id=ctx["id"])
        .order_by(m.FleetReservation.start_date.desc())
        .all()
    ]


@router.get("/availability")
def availability(
    start_date: date,
    end_date: date,
    branch_id: Optional[int] = None,
    ctx=Depends(context),
    db: Session = Depends(get_db),
):
    if end_date < start_date or (end_date - start_date).days > 92:
        raise HTTPException(422, "Takvim aralığı 1–93 gün olmalı.")
    if branch_id:
        branch(db, ctx["id"], branch_id, False)
    result = []
    for car in db.query(m.Vehicle).filter_by(supplier_id=ctx["id"]).all():
        loc = (
            db.query(m.FleetVehicleLocation)
            .filter_by(vehicle_id=car.id, supplier_id=ctx["id"])
            .first()
        )
        if branch_id and (not loc or loc.current_branch_id != branch_id):
            continue
        busy = blocks(db, ctx["id"], car.id, start_date.isoformat(), end_date.isoformat())
        reason = ""
        try:
            available(db, ctx, car, start_date.isoformat(), end_date.isoformat())
        except HTTPException as exc:
            reason = exc.detail
        operational_reason = ""
        try:
            available(
                db, ctx, car, start_date.isoformat(), end_date.isoformat(), check_blocks=False
            )
        except HTTPException as exc:
            operational_reason = exc.detail
        result.append(
            {
                "vehicle_id": car.id,
                "available": not reason,
                "reason": reason,
                "blocks": busy,
                "operational_reason": operational_reason,
            }
        )
    return result


@router.post("/reservations")
def create_reservation(data: ReservationInput, ctx=Depends(context), db: Session = Depends(get_db)):
    permit(ctx, "contract")
    schedule_lock(db, ctx["id"])
    if data.customer_id not in customer_ids(db, ctx["id"]):
        raise HTTPException(404, "Müşteri şirket listenizde bulunamadı.")
    car = vehicle(db, ctx, data.vehicle_id)
    branch(db, ctx["id"], data.pickup_branch_id)
    branch(db, ctx["id"], data.return_branch_id)
    location = (
        db.query(m.FleetVehicleLocation).filter_by(vehicle_id=car.id, supplier_id=ctx["id"]).first()
    )
    if not location or location.current_branch_id != data.pickup_branch_id:
        raise HTTPException(
            409, "Araç teslim şubesinde olmalı; önce güncel lokasyonunu doğrulayın."
        )
    available(db, ctx, car, data.start_date.isoformat(), data.end_date.isoformat())
    row = m.FleetReservation(
        supplier_id=ctx["id"],
        **{
            **data.model_dump(),
            "start_date": data.start_date.isoformat(),
            "end_date": data.end_date.isoformat(),
        },
        created_at=stamp(),
        updated_at=stamp(),
    )
    db.add(row)
    db.commit()
    return reservation_dict(row)


@router.post("/reservations/{rid}/{action}")
def reservation_action(
    rid: int,
    action: Literal["cancel", "convert"],
    data: VersionInput,
    ctx=Depends(context),
    db: Session = Depends(get_db),
):
    permit(ctx, "contract")
    schedule_lock(db, ctx["id"])
    row = db.query(m.FleetReservation).filter_by(id=rid, supplier_id=ctx["id"]).first()
    if not row:
        raise HTTPException(404, "Rezervasyon bulunamadı.")
    if row.version != data.version or row.status != "Onaylandı":
        raise HTTPException(409, "Rezervasyon değişmiş veya kapanmış. Yenileyin.")
    try:
        values = {"status": "İptal", "updated_at": stamp()}
        if action == "convert":
            from app.supplier_service import append_record

            if row.start_date < business_today().isoformat():
                raise HTTPException(
                    409,
                    "Başlangıcı geçmiş rezervasyonu iptal edip güncel tarihlerle yeniden oluşturun.",
                )
            branch(db, ctx["id"], row.pickup_branch_id)
            branch(db, ctx["id"], row.return_branch_id)
            location = (
                db.query(m.FleetVehicleLocation)
                .filter_by(supplier_id=ctx["id"], vehicle_id=row.vehicle_id)
                .first()
            )
            if not location or location.current_branch_id != row.pickup_branch_id:
                raise HTTPException(
                    409, "Araç teslim şubesinde değil. Önce güncel lokasyonunu doğrulayın."
                )
            available(
                db,
                ctx,
                vehicle(db, ctx, row.vehicle_id),
                row.start_date,
                row.end_date,
                exclude_reservation=row.id,
            )
            # Release this reservation inside the same transaction; the draft contract becomes the block.
            row.status = "Sözleşmeye Dönüştü"
            db.flush()
            start, end = date.fromisoformat(row.start_date), date.fromisoformat(row.end_date)
            months = max(1, (end.year - start.year) * 12 + end.month - start.month)
            contract = append_record(
                db,
                ctx,
                "contract",
                OperationInput(
                    title=f"Rezervasyon #{row.id}",
                    customer_id=row.customer_id,
                    vehicle_id=row.vehicle_id,
                    date=start,
                    end_date=end,
                    amount=row.monthly_rent,
                    details={
                        "months": months,
                        "quantity": 1,
                        "vehicle_ids": [row.vehicle_id],
                        "reservation_id": row.id,
                        "pickup_branch_id": row.pickup_branch_id,
                        "return_branch_id": row.return_branch_id,
                        "notes": row.note,
                    },
                ),
            )
            values.update(status="Sözleşmeye Dönüştü", contract_id=contract.id)
        save_version(db, m.FleetReservation, row, data.version, values)
        db.commit()
        return reservation_dict(row)
    except Exception:
        db.rollback()
        raise


def task_sources(db, ctx):
    """Project live business state; a task checkbox never completes a rental/service."""
    sources = {}

    def add(key, title, due, vid, url, category, bid=None):
        if due:
            sources[key] = {
                "key": key,
                "title": title,
                "due_date": due[:10],
                "vehicle_id": vid,
                "branch_id": bid,
                "url": url,
                "category": category,
                "status": "Açık",
                "version": 0,
                "assignee_id": None,
                "note": "",
                "derived": True,
            }

    operations = db.query(m.SupplierOperation).filter_by(supplier_id=ctx["id"]).all()
    for row in operations:
        if row.status in {"İptal", "Tamamlandı", "Reddedildi", "Sona Erdi", "Ödendi"}:
            continue
        module = {"delivery": "deliveries", "return": "returns", "maintenance": "maintenance"}.get(
            row.kind
        )
        if module:
            add(
                f"operation-{row.id}",
                row.title,
                row.date,
                row.vehicle_id,
                f"/supplier-portal/{module}?record={row.id}",
                {"delivery": "Teslim", "return": "İade", "maintenance": "Bakım"}[row.kind],
            )
    for row in (
        db.query(m.Rental)
        .filter_by(supplier_id=ctx["id"])
        .filter(m.Rental.status.notin_(["İptal", "Tamamlandı"]))
        .all()
    ):
        if row.status == "Teslim Bekliyor" and not row.delivery_id:
            add(
                f"rental-delivery-{row.id}",
                "Teslimat planla",
                row.starts_at,
                row.vehicle_id,
                f"/supplier-portal/contracts?record={row.contract_id}",
                "Teslim",
            )
        if row.status != "Teslim Bekliyor" and not row.return_id:
            add(
                f"rental-return-{row.id}",
                "Kiralama dönüşünü planla",
                row.ends_at,
                row.vehicle_id,
                f"/supplier-portal/contracts?record={row.contract_id}",
                "İade",
            )
    cars = {v.id for v in db.query(m.Vehicle).filter_by(supplier_id=ctx["id"]).all()}
    for row in (
        db.query(m.Request)
        .filter(
            m.Request.vehicle_id.in_(cars), m.Request.type.in_(["servis", "lastik", "yol_yardim"])
        )
        .all()
    ):
        if row.status not in {"Tamamlandı", "İptal", "Reddedildi"}:
            details = row.details or {}
            add(
                f"service-{row.id}",
                f"Servis: {row.status}",
                details.get("appointment_date") or row.created_at,
                row.vehicle_id,
                f"/supplier-portal/service?record={row.id}",
                "Servis",
            )
    for row in (
        db.query(m.FleetReservation).filter_by(supplier_id=ctx["id"], status="Onaylandı").all()
    ):
        add(
            f"reservation-{row.id}",
            f"Rezervasyon #{row.id} — sözleşme hazırlığı",
            row.start_date,
            row.vehicle_id,
            "/supplier-portal/reservations",
            "Rezervasyon",
            row.pickup_branch_id,
        )
    for task in sources.values():
        loc = (
            db.query(m.FleetVehicleLocation)
            .filter_by(vehicle_id=task["vehicle_id"], supplier_id=ctx["id"])
            .first()
            if task["vehicle_id"]
            else None
        )
        if not task["branch_id"] and loc:
            task["branch_id"] = loc.current_branch_id
    return sources


@router.get("/tasks")
def tasks(ctx=Depends(context), db: Session = Depends(get_db)):
    result = task_sources(db, ctx)
    for row in db.query(m.FleetTask).filter_by(supplier_id=ctx["id"]).all():
        if row.source_key.startswith("manual-"):
            result[row.source_key] = {
                "key": row.source_key,
                "title": row.title,
                "due_date": row.due_date,
                "vehicle_id": row.vehicle_id,
                "branch_id": row.branch_id,
                "url": None,
                "category": "Görev",
                "derived": False,
            }
        if row.source_key in result:
            result[row.source_key].update(
                assignee_id=row.assignee_id,
                note=row.note,
                version=row.version,
                status=row.status if row.source_key.startswith("manual-") else "Açık",
                updated_by=row.updated_by,
            )
    return sorted(result.values(), key=lambda r: (r["due_date"], r["key"]))


@router.post("/tasks")
def create_task(data: TaskInput, ctx=Depends(context), db: Session = Depends(get_db)):
    task_permit(ctx)
    if data.vehicle_id:
        vehicle(db, ctx, data.vehicle_id)
    if data.branch_id:
        branch(db, ctx["id"], data.branch_id)
    member(db, ctx["id"], data.assignee_id)
    db.add(
        m.FleetTask(
            supplier_id=ctx["id"],
            source_key="manual-" + secrets.token_hex(12),
            **{**data.model_dump(), "due_date": data.due_date.isoformat()},
            updated_by=ctx["actor"],
            updated_at=stamp(),
        )
    )
    db.commit()
    return tasks(ctx, db)


@router.put("/tasks/{key}")
def update_task(key: str, data: TaskUpdate, ctx=Depends(context), db: Session = Depends(get_db)):
    task_permit(ctx)
    schedule_lock(db, ctx["id"])
    member(db, ctx["id"], data.assignee_id)
    row = db.query(m.FleetTask).filter_by(supplier_id=ctx["id"], source_key=key).first()
    source = task_sources(db, ctx).get(key)
    if not row and not source:
        raise HTTPException(404, "Görev bulunamadı.")
    if not key.startswith("manual-") and (
        not source or data.status != "Açık" or data.due_date is not None or data.title is not None
    ):
        raise HTTPException(409, "Bağlı işi kendi işlem ekranından tamamlayın.")
    values = {
        **data.model_dump(exclude={"version", "due_date", "title"}),
        "updated_at": stamp(),
        "updated_by": ctx["actor"],
    }
    if data.due_date is not None:
        values["due_date"] = data.due_date.isoformat()
    if data.title is not None:
        values["title"] = data.title
    if row:
        save_version(db, m.FleetTask, row, data.version, values)
    else:
        if data.version != 0:
            raise HTTPException(409, "Görev değişti. Yenileyin.")
        db.add(
            m.FleetTask(
                supplier_id=ctx["id"],
                source_key=key,
                title=source["title"],
                due_date=source["due_date"],
                vehicle_id=source["vehicle_id"],
                branch_id=source["branch_id"],
                **values,
            )
        )
    db.commit()
    return tasks(ctx, db)
