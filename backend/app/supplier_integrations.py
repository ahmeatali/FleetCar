"""Company-scoped GPS ingestion. Provider data is never trusted as vehicle identity."""

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models as m
from app.common.time import stamp
from app.database import get_db
from app.supplier_context import context, vehicle

router = APIRouter(prefix="/api/supplier-workspace/integrations", tags=["Supplier integrations"])
ENDPOINT = "https://ws.arvento.com/v1/report.asmx/GetVehicleStatus"
MAX_RESPONSE = 8 * 1024 * 1024


class ArventoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Response columns differ by report/account. Require explicit mapping; do not guess units.
    device_column: str = Field(min_length=1, max_length=100)
    time_column: str = Field(min_length=1, max_length=100)
    latitude_column: str = Field(min_length=1, max_length=100)
    longitude_column: str = Field(min_length=1, max_length=100)
    mileage_column: Optional[str] = Field(None, min_length=1, max_length=100)
    mileage_unit: str = Field("km", pattern="^(km|m)$")
    time_format: Optional[str] = Field(None, max_length=100)
    timezone_offset_minutes: int = Field(180, ge=-840, le=840)


class MappingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    external_id: str = Field(min_length=1, max_length=150)
    vehicle_id: str = Field(min_length=1, max_length=200)

    @field_validator("external_id")
    @classmethod
    def clean_id(cls, value):
        if not value.strip():
            raise ValueError("Cihaz kimliği boş olamaz.")
        return value.strip()


class GpsPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_id: str = Field(min_length=1, max_length=150)
    occurred_at: datetime
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    mileage: Optional[int] = Field(None, ge=0, le=10000000)

    @field_validator("occurred_at")
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None:
            raise ValueError("GPS kaydı saat dilimi içermeli.")
        value = value.astimezone(timezone.utc)
        if value > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError("GPS kaydı gelecekte olamaz.")
        return value


def owner(ctx):
    if ctx["role"] != "owner":
        raise HTTPException(403, "Entegrasyon yönetimi için şirket sahibi yetkisi gerekli.")


def credentials(sid):
    return {
        key: os.environ.get(f"ARVENTO_{sid}_{key.upper()}", "")
        for key in ("Username", "PIN1", "PIN2")
    }


def config(db, sid):
    row = db.query(m.SupplierSetting).filter_by(supplier_id=sid).first()
    return (row.value or {}).get("arvento") if row else None


def dataset_rows(raw):
    """Decode the documented .NET DataSet, ignoring XSD metadata and rejecting entities."""
    if (
        len(raw) > MAX_RESPONSE
        or b"\x00" in raw
        or b"<!DOCTYPE" in raw.upper()
        or b"<!ENTITY" in raw.upper()
    ):
        raise ValueError("Geçersiz Arvento XML yanıtı.")
    root = ET.fromstring(raw)
    if any(e.tag.split("}")[-1] == "Fault" for e in root.iter()):
        raise ValueError("Arvento servis hatası.")
    rows = []
    for elem in root.iter():
        children = list(elem)
        if children and all(
            not list(c) and not c.tag.startswith("{http://www.w3.org/2001/XMLSchema}")
            for c in children
        ):
            rows.append({c.tag.split("}")[-1]: c.text or "" for c in children})
    return rows


def normalize(raw, cfg):
    points = []
    for row in dataset_rows(raw):
        if cfg.device_column not in row:
            continue
        moment = (
            datetime.strptime(row[cfg.time_column], cfg.time_format)
            if cfg.time_format
            else datetime.fromisoformat(row[cfg.time_column].replace("Z", "+00:00"))
        )
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone(timedelta(minutes=cfg.timezone_offset_minutes)))
        mileage = None
        if cfg.mileage_column and row.get(cfg.mileage_column, "").strip():
            value = float(row[cfg.mileage_column])
            if cfg.mileage_unit == "m":
                value /= 1000
            # Rounding down reflects only full verified kilometres.
            if value < 0:
                raise ValueError("Negatif kilometre.")
            mileage = int(value)
        points.append(
            GpsPoint(
                device_id=row[cfg.device_column].strip(),
                occurred_at=moment,
                latitude=row[cfg.latitude_column],
                longitude=row[cfg.longitude_column],
                mileage=mileage,
            )
        )
    if not points:
        raise ValueError("Yanıt eşlenen GPS alanlarını içermiyor. Alan eşlemesini doğrulayın.")
    return points


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_arvento(sid):
    fields = credentials(sid)
    if not all(fields.values()):
        raise HTTPException(503, "Arvento sunucu erişim bilgileri yapılandırılmadı.")
    request = urllib.request.Request(
        ENDPOINT,
        data=urllib.parse.urlencode({**fields, "Language": "0"}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=25) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError("Yanıt sınırı aşıldı.")
            return raw
    except (urllib.error.URLError, TimeoutError, ValueError):
        # Provider errors can contain PINs/URLs; never relay their text or body.
        raise HTTPException(502, "Arvento bağlantısı tamamlanamadı. Sunucu erişimini kontrol edin.")


def process(db, ctx, event):
    point = GpsPoint.model_validate(event.payload)
    mapping = (
        db.query(m.IntegrationMapping)
        .filter_by(supplier_id=ctx["id"], provider="arvento", external_id=point.device_id)
        .first()
    )
    if not mapping:
        event.status, event.reason = (
            "Eşleştirme Bekliyor",
            "Arvento cihazı bir filo aracına bağlanmalı.",
        )
        return
    car = (
        db.query(m.Vehicle)
        .filter_by(id=mapping.vehicle_id, supplier_id=ctx["id"])
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not car:
        raise HTTPException(404, "Tedarikçiye ait araç bulunamadı.")
    latest = (
        db.query(m.IntegrationEvent)
        .filter(
            m.IntegrationEvent.supplier_id == ctx["id"],
            m.IntegrationEvent.vehicle_id == car.id,
            m.IntegrationEvent.provider == "arvento",
            m.IntegrationEvent.status == "İşlendi",
            m.IntegrationEvent.id != event.id,
        )
        .order_by(m.IntegrationEvent.occurred_at.desc())
        .first()
    )
    event.vehicle_id = car.id
    if latest and event.occurred_at <= latest.occurred_at:
        event.status, event.reason = "Eski Kayıt", "Daha güncel doğrulanmış GPS verisi var."
        return
    if point.mileage is not None and point.mileage < (car.mileage or 0):
        event.status, event.reason = (
            "İnceleme Bekliyor",
            "Kilometre mevcut doğrulanmış değerden düşük; araç güncellenmedi.",
        )
        return
    # All writes belong to the same transaction as the event, including derived history.
    db.add(
        m.VehicleLocation(
            vehicle_id=car.id,
            latitude=point.latitude,
            longitude=point.longitude,
            label="Arvento",
            source="arvento",
            recorded_at=event.occurred_at,
        )
    )
    if point.mileage is not None:
        car.mileage = point.mileage
        db.add(
            m.VehicleMileageRecord(
                vehicle_id=car.id,
                mileage=point.mileage,
                source="arvento",
                recorded_at=event.occurred_at,
            )
        )
    car.gps_latitude, car.gps_longitude = point.latitude, point.longitude
    car.gps_location_label, car.gps_last_seen_at = "Arvento", event.occurred_at
    event.status, event.reason, event.processed_at = "İşlendi", None, stamp()
    if point.mileage is not None:
        from app.maintenance_automation import suggest

        suggest(db, ctx, car, event)


def ingest(db, ctx, points):
    counts = {"processed": 0, "duplicate": 0, "pending": 0, "stale": 0}
    for point in points:
        payload = point.model_dump(mode="json")
        when = point.occurred_at.isoformat()
        key = hashlib.sha256(f"{point.device_id}\0{when}".encode()).hexdigest()
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        existing = (
            db.query(m.IntegrationEvent)
            .filter_by(supplier_id=ctx["id"], provider="arvento", external_id=key)
            .first()
        )
        if existing:
            if existing.payload_hash != digest:
                raise HTTPException(
                    409, "Aynı cihaz ve zaman için farklı içerik geldi; kayıt üzerine yazılmadı."
                )
            counts["duplicate"] += 1
            continue
        event = m.IntegrationEvent(
            supplier_id=ctx["id"],
            provider="arvento",
            external_id=key,
            payload_hash=digest,
            payload=payload,
            status="Alındı",
            occurred_at=when,
            received_at=stamp(),
        )
        db.add(event)
        db.flush()
        process(db, ctx, event)
        db.flush()
        counts[{"İşlendi": "processed", "Eski Kayıt": "stale"}.get(event.status, "pending")] += 1
    return counts


@router.get("/arvento")
def overview(ctx=Depends(context), db: Session = Depends(get_db)):
    mappings = (
        db.query(m.IntegrationMapping).filter_by(supplier_id=ctx["id"], provider="arvento").all()
    )
    events = (
        db.query(m.IntegrationEvent)
        .filter_by(supplier_id=ctx["id"], provider="arvento")
        .order_by(m.IntegrationEvent.id.desc())
        .limit(100)
        .all()
    )
    return {
        "provider": "Arvento",
        "credentials_configured": all(credentials(ctx["id"]).values()),
        "config": config(db, ctx["id"]),
        "mappings": [{"external_id": r.external_id, "vehicle_id": r.vehicle_id} for r in mappings],
        "events": [
            {
                "id": r.id,
                "device_id": r.payload["device_id"],
                "vehicle_id": r.vehicle_id,
                "status": r.status,
                "reason": r.reason,
                "occurred_at": r.occurred_at,
                "received_at": r.received_at,
                "processed_at": r.processed_at,
                "mileage": r.payload.get("mileage"),
            }
            for r in events
        ],
    }


@router.put("/arvento/config")
def save_config(data: ArventoConfig, ctx=Depends(context), db: Session = Depends(get_db)):
    owner(ctx)
    row = db.query(m.SupplierSetting).filter_by(supplier_id=ctx["id"]).first()
    if not row:
        row = m.SupplierSetting(supplier_id=ctx["id"], value={})
        db.add(row)
    row.value = {**(row.value or {}), "arvento": data.model_dump()}
    db.commit()
    return overview(ctx, db)


@router.put("/arvento/mappings")
def save_mapping(data: MappingInput, ctx=Depends(context), db: Session = Depends(get_db)):
    owner(ctx)
    vehicle(db, ctx, data.vehicle_id)
    row = (
        db.query(m.IntegrationMapping)
        .filter_by(supplier_id=ctx["id"], provider="arvento", external_id=data.external_id)
        .first()
    )
    if row and row.vehicle_id != data.vehicle_id:
        raise HTTPException(
            409, "Cihaz mevcut araca bağlı. Geçmişi korumak için cihazı başka araca taşıyamazsınız."
        )
    if not row:
        db.add(
            m.IntegrationMapping(
                supplier_id=ctx["id"],
                provider="arvento",
                external_id=data.external_id,
                vehicle_id=data.vehicle_id,
                created_at=stamp(),
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Araç başka bir Arvento cihazına bağlı.")
    return overview(ctx, db)


@router.post("/arvento/sync")
def sync(ctx=Depends(context), db: Session = Depends(get_db)):
    owner(ctx)
    value = config(db, ctx["id"])
    if not value:
        raise HTTPException(400, "Önce Arvento yanıt alanlarını eşleyin.")
    raw = fetch_arvento(ctx["id"])
    try:
        points = normalize(raw, ArventoConfig.model_validate(value))
    except (ValueError, OverflowError, KeyError, ET.ParseError):
        raise HTTPException(
            502,
            "Arvento yanıtı doğrulanamadı. Alan, saat dilimi ve kilometre birimini kontrol edin.",
        )
    try:
        result = ingest(db, ctx, sorted(points, key=lambda p: p.occurred_at))
        db.commit()
        return result
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Senkronizasyon başka işlem tarafından kaydedildi. Tekrar deneyin."
        )
    except Exception:
        db.rollback()
        raise


@router.post("/arvento/events/{eid}/retry")
def retry(eid: int, ctx=Depends(context), db: Session = Depends(get_db)):
    owner(ctx)
    event = (
        db.query(m.IntegrationEvent)
        .filter_by(id=eid, supplier_id=ctx["id"], provider="arvento")
        .first()
    )
    if not event:
        raise HTTPException(404, "Entegrasyon kaydı bulunamadı.")
    if event.status == "İşlendi":
        raise HTTPException(409, "İşlenen kayıt tekrar uygulanamaz.")
    try:
        process(db, ctx, event)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return overview(ctx, db)
