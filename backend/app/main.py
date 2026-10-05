import datetime
import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db, SessionLocal, engine
from app import models
from app.auth import verify_password, hash_password
from app.email_utils import (
    generate_invitation_token, send_supplier_invitation_email,
    send_password_reset_email, send_email_verification_email, APP_BASE_URL
)
from app.init_db import create_tables, seed
from app.schemas import (
    QuoteCreate, QuoteResponse,
    VehicleCreate, VehicleResponse, VehicleUpdate,
    VehicleExpenseCreate, VehicleExpenseResponse,
    HgsTransactionCreate, HgsTransactionResponse,
    VehicleLocationCreate, VehicleLocationResponse, VehicleFileResponse,
    TireRecordCreate, TireRecordUpdate, TireRecordResponse,
    TireOperationCreate, TireOperationResponse,
    RoadsideCaseCreate, RoadsideCaseUpdate, RoadsideCaseResponse,
    RoadsideEventCreate, RoadsideEventResponse,
    RequestCreate, RequestResponse,
    SupplierCreate, SupplierResponse, StatusUpdate,
    VehicleRemoval, QuoteUpdate,
    CustomerCreate, CustomerUpdate, BidCreate, BidResponse,
    AdminLoginRequest, SetPasswordRequest,
    ServiceCheckIn, ServiceWorkOrder, ServiceInvoice,
    CustomerRegisterRequest, SupplierRegisterRequest, CustomerDocumentUpload,
    ForgotPasswordRequest, ResetPasswordRequest, ResendVerificationRequest
)

app = FastAPI(title="FleetRent API", version="2.0.0")
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "vehicles"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/vehicles", StaticFiles(directory=UPLOADS_DIR), name="vehicle-uploads")
CUSTOMER_UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "customer-documents"
CUSTOMER_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/customer-documents", StaticFiles(directory=CUSTOMER_UPLOADS_DIR), name="customer-documents")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_database_columns():
    db = SessionLocal()
    try:
        res = db.execute(text("PRAGMA table_info(quotes);")).fetchall()
        columns = [row[1] for row in res]
        if "customer_id" not in columns:
            db.execute(text("ALTER TABLE quotes ADD COLUMN customer_id INTEGER;"))
            db.commit()
    except Exception as e:
        print("Column migration notice:", e)
    finally:
        db.close()


@app.on_event("startup")
def startup():
    create_tables()
    check_database_columns()
    seed()
    # Migrate historical roadside requests into the dedicated tracking records.
    db = SessionLocal()
    try:
        legacy_requests = db.query(models.Request).filter(models.Request.type == "yol_yardim").all()
        for request in legacy_requests:
            if db.query(models.RoadsideCase).filter_by(request_id=request.id).first():
                continue
            details = request.details or {}
            incidents = details.get("incidents") or []
            old_status = request.status or "Beklemede"
            case_status = ("Çözüldü" if old_status == "Tamamlandı" else
                           "Yolda" if old_status in ("İşlemde", "Yol Yardımında", "Yolda") else
                           "Ekip Atandı" if old_status == "Onaylandı" else old_status)
            progress = {"Beklemede": 0, "Ekip Atandı": 15, "Yolda": 60,
                        "Çözüldü": 100, "İptal Edildi": 0}.get(case_status, 0)
            case = models.RoadsideCase(
                request_id=request.id, vehicle_id=request.vehicle_id,
                case_no=details.get("roadside_case_no") or f"YA-{datetime.datetime.now().year}-{request.id:04d}",
                incident=", ".join(incidents) if isinstance(incidents, list) and incidents else details.get("incident", "Yol Yardım"),
                location=details.get("location") or " / ".join(filter(None, [details.get("district"), details.get("city")])),
                latitude=details.get("latitude"), longitude=details.get("longitude"),
                description=request.description, status=case_status, progress=progress,
                photos=details.get("photos", [details["photo"]] if details.get("photo") else []),
                created_at=request.created_at or now_str(), updated_at=request.created_at or now_str()
            )
            db.add(case); db.flush()
            db.add(models.RoadsideEvent(case_id=case.id, status=case_status,
                title="Önceki yol yardım talebi", description=request.description,
                created_at=request.created_at or now_str()))
        db.commit()
    except Exception as exc:
        db.rollback()
        print("Roadside request migration notice:", exc)
    finally:
        db.close()


# ─────────────────── HELPERS ───────────────────────────────────────────────

def now_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def calculate_quote_price(data: QuoteCreate) -> int:
    base = 12000
    seg  = {"A": 0.70, "B": 0.85, "C": 1.0, "D": 1.30, "E": 1.70}.get(data.vehicle_segment, 1.0)
    typ  = {"Sedan": 1.0, "SUV": 1.20, "Hatchback": 0.95, "Hafif Ticari": 1.15, "Station Wagon": 1.05}.get(data.vehicle_type, 1.0)
    dur  = {12: 1.0, 24: 0.90, 36: 0.82, 48: 0.75}.get(data.duration_months, 0.90)
    km   = {10000: 0.95, 20000: 1.0, 30000: 1.12, 40000: 1.25, 50000: 1.40}.get(data.estimated_annual_mileage, 1.0)
    return int(base * seg * typ * dur * km * data.vehicle_count)


def supplier_dict(s: models.Supplier) -> dict:
    return {
        "id": s.id, "name": s.name, "type": s.type,
        "phone": s.phone, "location": s.location or f"{s.district}, {s.city}",
        "city": s.city, "district": s.district,
        "services": s.services or [], "contract_type": s.contract_type,
        "email": getattr(s, 'email', None),
        "invitation_status": getattr(s, 'invitation_status', 'Davet Edilmedi') or 'Davet Edilmedi',
        "has_password": bool(getattr(s, 'password_hash', None)),
        "is_email_verified": getattr(s, 'is_email_verified', False) if getattr(s, 'is_email_verified', None) is not None else False
    }


def vehicle_dict(v: models.Vehicle, db: Session = None) -> dict:
    d = {
        "id": v.id, "chassis_no": v.chassis_no, "plate": v.plate,
        "brand": v.brand, "model": v.model, "year": v.year, "fuel": v.fuel,
        "color": getattr(v, "color", None),
        "contract_start_date": getattr(v, "contract_start_date", None),
        "contract_end_date": getattr(v, "contract_end_date", None),
        "monthly_rent": getattr(v, "monthly_rent", None),
        "monthly_km_limit": getattr(v, "monthly_km_limit", None),
        "version": getattr(v, "version", None), "engine_no": getattr(v, "engine_no", None),
        "horsepower": getattr(v, "horsepower", None), "cylinder_count": getattr(v, "cylinder_count", None),
        "transmission": getattr(v, "transmission", None), "seat_count": getattr(v, "seat_count", None),
        "trunk_volume_l": getattr(v, "trunk_volume_l", None), "tire_size": getattr(v, "tire_size", None),
        "registration_date": getattr(v, "registration_date", None),
        "traffic_insurance_policy_no": getattr(v, "traffic_insurance_policy_no", None),
        "traffic_insurance_expiry_date": getattr(v, "traffic_insurance_expiry_date", None),
        "casco_policy_no": getattr(v, "casco_policy_no", None),
        "casco_insurance_expiry_date": getattr(v, "casco_insurance_expiry_date", None),
        "hgs_no": getattr(v, "hgs_no", None), "hgs_balance": getattr(v, "hgs_balance", None),
        "hgs_last_reload_date": getattr(v, "hgs_last_reload_date", None),
        "hgs_active": getattr(v, "hgs_active", False),
        "delivery_date": getattr(v, "delivery_date", None), "delivered_by": getattr(v, "delivered_by", None),
        "received_by": getattr(v, "received_by", None), "delivery_location": getattr(v, "delivery_location", None),
        "delivery_notes": getattr(v, "delivery_notes", None), "contract_no": getattr(v, "contract_no", None),
        "contract_duration_months": getattr(v, "contract_duration_months", None),
        "contract_committed_km": getattr(v, "contract_committed_km", None),
        "contract_signed_at": getattr(v, "contract_signed_at", None), "erp_id": getattr(v, "erp_id", None),
        "assignment_user": getattr(v, "assignment_user", None),
        "operating_company": getattr(v, "operating_company", None), "vehicle_group": getattr(v, "vehicle_group", None),
        "current_month_km": getattr(v, "current_month_km", None),
        "next_service_due_date": getattr(v, "next_service_due_date", None),
        "next_service_due_km": getattr(v, "next_service_due_km", None),
        "gps_latitude": getattr(v, "gps_latitude", None), "gps_longitude": getattr(v, "gps_longitude", None),
        "gps_location_label": getattr(v, "gps_location_label", None),
        "gps_last_seen_at": getattr(v, "gps_last_seen_at", None),
        "status": v.status, "mileage": v.mileage,
        "license_serial_no": v.license_serial_no,
        "inspection_date": v.inspection_date,
        "vehicle_segment": v.vehicle_segment, "vehicle_type": v.vehicle_type,
        "tire_change_date": v.tire_change_date,
        "last_service_date": v.last_service_date,
        "last_service_mileage": v.last_service_mileage,
        "is_active": v.is_active,
        "removal_reason": v.removal_reason, "removed_at": v.removed_at,
        "supplier_id": v.supplier_id, "customer_id": v.customer_id,
        "gps_device_id": getattr(v, "gps_device_id", None),
        "utts_code": getattr(v, "utts_code", None)
    }
    if db:
        if v.customer_id:
            c = db.query(models.Customer).filter(models.Customer.id == v.customer_id).first()
            if c: d["customer_name"] = c.company_name
        if v.supplier_id:
            s = db.query(models.Supplier).filter(models.Supplier.id == v.supplier_id).first()
            if s: d["supplier_name"] = s.name
    return d


def quote_dict(q: models.Quote, db: Session = None) -> dict:
    bids_list = []
    customer_info = None
    if db:
        bids = db.query(models.SupplierBid).filter(models.SupplierBid.quote_id == q.id).all()
        bids_list = [bid_dict(b) for b in bids]
        cid = getattr(q, 'customer_id', None)
        if cid:
            cust = db.query(models.Customer).filter(models.Customer.id == cid).first()
            if cust:
                customer_info = customer_dict(cust)
        elif q.email:
            cust = db.query(models.Customer).filter(models.Customer.email == q.email).first()
            if cust:
                customer_info = customer_dict(cust)

    details = getattr(q, 'details', {}) or {}
    if customer_info and 'customer_info' not in details:
        details = {**details, "customer_info": customer_info}

    return {
        "id": q.id,
        "customer_id": getattr(q, 'customer_id', None),
        "customer_info": customer_info,
        "company_name": q.company_name,
        "email": q.email,
        "phone": q.phone,
        "vehicle_count": q.vehicle_count,
        "duration_months": q.duration_months,
        "vehicle_segment": q.vehicle_segment,
        "vehicle_type": q.vehicle_type,
        "estimated_annual_mileage": q.estimated_annual_mileage,
        "monthly_price_try": q.monthly_price_try,
        "status": q.status,
        "created_at": q.created_at,
        "contract_amount": q.contract_amount,
        "items": getattr(q, 'items', []) or [],
        "bids": bids_list,
        "details": details
    }


def request_dict(r: models.Request) -> dict:
    return {
        "id": r.id, "vehicle_id": r.vehicle_id, "supplier_id": r.supplier_id,
        "type": r.type, "status": r.status, "description": r.description,
        "created_at": r.created_at, "completed_at": r.completed_at, "details": r.details or {}
    }


def bid_dict(b: models.SupplierBid) -> dict:
    return {
        "id": b.id, "quote_id": b.quote_id, "supplier_id": b.supplier_id,
        "supplier_name": b.supplier_name, "monthly_price_try": b.monthly_price_try,
        "notes": b.notes, "created_at": b.created_at, "status": b.status
    }


def customer_dict(c: models.Customer, actual: int = None, deficit: int = None) -> dict:
    d = {
        "id": c.id, "company_name": c.company_name, "legal_title": c.legal_title,
        "email": c.email, "phone": c.phone,
        "registered_vehicles_count": c.registered_vehicles_count,
        "status": c.status, "address": c.address,
        "contract_amount": c.contract_amount, "signed_at": c.signed_at,
        "invitation_status": getattr(c, 'invitation_status', 'Davet Edilmedi') or 'Davet Edilmedi',
        "has_password": bool(getattr(c, 'password_hash', None)),
        "documents_uploaded": has_actual_customer_documents(c),
        "documents": getattr(c, 'documents', {}) or {},
        "is_email_verified": getattr(c, 'is_email_verified', False) if getattr(c, 'is_email_verified', None) is not None else False
    }
    if actual is not None:
        d["actual_vehicle_count"] = actual
        d["vehicle_deficit"] = deficit
    return d


def has_actual_customer_documents(customer: models.Customer) -> bool:
    required = ("tax_plate", "signature_circular", "activity_certificate", "trade_registry")
    documents = customer.documents or {}
    return all(isinstance(documents.get(key), dict) and bool(documents[key].get("url")) for key in required)


# ─────────────────── QUOTES ────────────────────────────────────────────────

@app.get("/api/quotes", response_model=List[QuoteResponse])
def get_quotes(customer_id: Optional[int] = None, supplier_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Quote)
    if customer_id:
        query = query.filter(models.Quote.customer_id == customer_id)
    if supplier_id:
        quote_ids = db.query(models.SupplierBid.quote_id).filter_by(supplier_id=supplier_id).subquery()
        query = query.filter((models.Quote.status.in_(["Teklif Bekleniyor", "Değerlendirmede", "Teklif Verildi"])) | (models.Quote.id.in_(quote_ids)))
    return [quote_dict(q, db) for q in query.order_by(models.Quote.created_at.desc()).all()]


@app.post("/api/quotes", response_model=QuoteResponse)
def create_quote(quote: QuoteCreate, db: Session = Depends(get_db)):
    cust_id = None
    cust_info = {}
    if quote.email:
        cust = db.query(models.Customer).filter(models.Customer.email == quote.email).first()
        if cust:
            if not has_actual_customer_documents(cust):
                raise HTTPException(
                    status_code=400,
                    detail="Kiralama teklif talebi oluşturabilmek için şirket evraklarınızı (Vergi Levhası, İmza Sirküsü, Faaliyet Belgesi) yüklemeniz zorunludur."
                )
            cust_id = cust.id
            cust_info = {
                "id": cust.id,
                "company_name": cust.company_name,
                "email": cust.email,
                "phone": cust.phone,
                "legal_title": cust.legal_title or cust.company_name,
                "address": cust.address or "-",
                "documents_uploaded": getattr(cust, 'documents_uploaded', False)
            }

    details_dict = quote.details or {}
    if cust_info:
        details_dict["customer_info"] = cust_info

    items_list = []
    if quote.items:
        items_list = [item.dict() for item in quote.items]

    if items_list:
        total_price = 0
        total_count = 0
        for item in items_list:
            base = 12000
            seg  = {"A": 0.70, "B": 0.85, "C": 1.0, "D": 1.30, "E": 1.70}.get(item["vehicle_segment"], 1.0)
            typ  = {"Sedan": 1.0, "SUV": 1.20, "Hatchback": 0.95, "Hafif Ticari": 1.15, "Station Wagon": 1.05}.get(item["vehicle_type"], 1.0)
            dur  = {12: 1.0, 24: 0.90, 36: 0.82, 48: 0.75}.get(item["duration_months"], 0.90)
            km   = {10000: 0.95, 20000: 1.0, 30000: 1.12, 40000: 1.25, 50000: 1.40}.get(item["estimated_annual_mileage"], 1.0)
            item_price = int(base * seg * typ * dur * km * item["vehicle_count"])
            item["monthly_price_try"] = item_price
            total_price += item_price
            total_count += item["vehicle_count"]

        first_item = items_list[0]
        v_segment = first_item["vehicle_segment"] if len(items_list) == 1 else f"Çoklu ({len(items_list)} Grup)"
        v_type = first_item["vehicle_type"] if len(items_list) == 1 else "Çoklu Gövde Tipi"
        v_duration = first_item["duration_months"] if len(items_list) == 1 else items_list[0]["duration_months"]
        v_km = first_item["estimated_annual_mileage"] if len(items_list) == 1 else items_list[0]["estimated_annual_mileage"]

        q = models.Quote(
            customer_id=cust_id,
            company_name=quote.company_name, email=quote.email, phone=quote.phone,
            vehicle_count=total_count, duration_months=v_duration,
            vehicle_segment=v_segment, vehicle_type=v_type,
            estimated_annual_mileage=v_km,
            monthly_price_try=total_price,
            items=items_list,
            details=details_dict,
            status="Teklif Bekleniyor", created_at=now_str()
        )
    else:
        q = models.Quote(
            customer_id=cust_id,
            company_name=quote.company_name, email=quote.email, phone=quote.phone,
            vehicle_count=quote.vehicle_count or 1, duration_months=quote.duration_months or 12,
            vehicle_segment=quote.vehicle_segment or "C", vehicle_type=quote.vehicle_type or "Sedan",
            estimated_annual_mileage=quote.estimated_annual_mileage or 20000,
            monthly_price_try=calculate_quote_price(quote),
            items=[],
            details=details_dict,
            status="Teklif Bekleniyor", created_at=now_str()
        )
    db.add(q); db.commit(); db.refresh(q)
    return quote_dict(q, db)


@app.delete("/api/quotes/{quote_id}")
@app.put("/api/quotes/{quote_id}/status")
def update_quote_status(quote_id: int, status_update: Optional[StatusUpdate] = None, db: Session = Depends(get_db)):
    q = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")

    new_status = status_update.status if status_update else "İstek Silindi"
    q.status = new_status

    if new_status == "Sözleşme İmzalandı" and status_update:
        amount = status_update.contract_amount or q.monthly_price_try
        q.contract_amount = amount

        existing = db.query(models.Customer).filter(
            models.Customer.company_name.ilike(q.company_name) | (models.Customer.email == q.email)
        ).first()

        if existing:
            existing.registered_vehicles_count = (existing.registered_vehicles_count or 0) + (q.vehicle_count or 1)
            existing.contract_amount = (existing.contract_amount or 0) + amount

    db.commit()
    return quote_dict(q, db)


@app.put("/api/quotes/{quote_id}", response_model=QuoteResponse)
def update_quote(quote_id: int, updated: QuoteUpdate, db: Session = Depends(get_db)):
    q = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")
    q.company_name = updated.company_name; q.email = updated.email
    q.phone = updated.phone; q.vehicle_count = updated.vehicle_count
    q.duration_months = updated.duration_months; q.vehicle_segment = updated.vehicle_segment
    q.vehicle_type = updated.vehicle_type; q.estimated_annual_mileage = updated.estimated_annual_mileage
    q.monthly_price_try = updated.monthly_price_try; q.status = updated.status
    db.commit(); db.refresh(q)
    return quote_dict(q)


# ─────────────────── BIDS ──────────────────────────────────────────────────

@app.get("/api/quotes/{quote_id}/bids", response_model=List[BidResponse])
def get_quote_bids(quote_id: int, db: Session = Depends(get_db)):
    return [bid_dict(b) for b in db.query(models.SupplierBid).filter(models.SupplierBid.quote_id == quote_id).all()]


@app.post("/api/quotes/{quote_id}/bids", response_model=BidResponse)
def create_quote_bid(quote_id: int, bid: BidCreate, supplier_id: int, db: Session = Depends(get_db)):
    q = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
    if not q: raise HTTPException(status_code=404, detail="Quote not found")
    s = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not s: raise HTTPException(status_code=404, detail="Supplier not found")

    existing = db.query(models.SupplierBid).filter(
        models.SupplierBid.quote_id == quote_id,
        models.SupplierBid.supplier_id == supplier_id
    ).first()

    if existing:
        existing.monthly_price_try = bid.monthly_price_try
        existing.notes = bid.notes
        existing.created_at = now_str()
        existing.status = "Beklemede"
        db.commit(); db.refresh(existing)
        return bid_dict(existing)

    b = models.SupplierBid(
        quote_id=quote_id, supplier_id=supplier_id, supplier_name=s.name,
        monthly_price_try=bid.monthly_price_try, notes=bid.notes,
        created_at=now_str(), status="Beklemede"
    )
    db.add(b); db.commit(); db.refresh(b)
    return bid_dict(b)


@app.get("/api/suppliers/{supplier_id}/bids", response_model=List[BidResponse])
def get_supplier_bids(supplier_id: int, db: Session = Depends(get_db)):
    return [bid_dict(b) for b in db.query(models.SupplierBid).filter(models.SupplierBid.supplier_id == supplier_id).all()]


@app.put("/api/bids/{bid_id}/status", response_model=BidResponse)
def update_bid_status(bid_id: int, status_update: StatusUpdate, db: Session = Depends(get_db)):
    b = db.query(models.SupplierBid).filter(models.SupplierBid.id == bid_id).first()
    if not b: raise HTTPException(status_code=404, detail="Bid not found")

    new_st = status_update.status
    if new_st in ["Kabul Edildi", "Onaylandı"]:
        b.status = "Onaylandı"
        db.query(models.SupplierBid).filter(
            models.SupplierBid.quote_id == b.quote_id,
            models.SupplierBid.id != bid_id
        ).update({"status": "Reddedildi"})
        
        q = db.query(models.Quote).filter(models.Quote.id == b.quote_id).first()
        if q:
            q.monthly_price_try = b.monthly_price_try
            q.contract_amount = b.monthly_price_try
            q.status = "Sözleşme İmzalandı"

            c = db.query(models.Customer).filter(
                models.Customer.company_name.ilike(q.company_name) | (models.Customer.email == q.email)
            ).first()
            if c:
                c.registered_vehicles_count = (c.registered_vehicles_count or 0) + (q.vehicle_count or 1)
                c.contract_amount = (c.contract_amount or 0) + b.monthly_price_try
                c.signed_at = now_str()
    else:
        b.status = new_st

    db.commit(); db.refresh(b)
    return bid_dict(b)


# ─────────────────── VEHICLES ──────────────────────────────────────────────

@app.get("/api/vehicles", response_model=List[VehicleResponse])
def get_vehicles(customer_id: Optional[int] = None, supplier_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(models.Vehicle)
    if customer_id:
        unassigned = db.query(models.Vehicle).filter(models.Vehicle.customer_id == None).all()
        if unassigned:
            for u in unassigned:
                u.customer_id = customer_id
            db.commit()
        q = q.filter(models.Vehicle.customer_id == customer_id)
    if supplier_id:
        q = q.filter(models.Vehicle.supplier_id == supplier_id)
    return [vehicle_dict(v, db) for v in q.all()]


@app.post("/api/vehicles", response_model=VehicleResponse)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    if db.query(models.Vehicle).filter(models.Vehicle.chassis_no == vehicle.chassis_no).first():
        raise HTTPException(status_code=400, detail="Bu şase numarasına sahip bir araç zaten kayıtlı.")

    cid = vehicle.customer_id
    if not cid:
        c = db.query(models.Customer).first()
        if c:
            cid = c.id

    v = models.Vehicle(
        id=vehicle.chassis_no, chassis_no=vehicle.chassis_no,
        plate=vehicle.plate.upper(), brand=vehicle.brand, model=vehicle.model,
        year=vehicle.year, fuel=vehicle.fuel, status="Aktif",
        color=vehicle.color, contract_start_date=vehicle.contract_start_date,
        contract_end_date=vehicle.contract_end_date,
        monthly_rent=vehicle.monthly_rent, monthly_km_limit=vehicle.monthly_km_limit,
        mileage=vehicle.mileage, license_serial_no=vehicle.license_serial_no,
        inspection_date=vehicle.inspection_date, vehicle_segment=vehicle.vehicle_segment,
        vehicle_type=vehicle.vehicle_type, tire_change_date=vehicle.tire_change_date,
        last_service_date=vehicle.last_service_date,
        last_service_mileage=vehicle.last_service_mileage,
        is_active=True, supplier_id=vehicle.supplier_id,
        customer_id=cid,
        gps_device_id=vehicle.gps_device_id,
        utts_code=vehicle.utts_code
    )
    for field, value in vehicle.dict(exclude_unset=True).items():
        if hasattr(v, field):
            setattr(v, field, value)
    db.add(v)
    db.flush()
    db.add(models.VehicleMileageRecord(vehicle_id=v.id, mileage=int(v.mileage or 0), recorded_at=now_str(), source="vehicle_record"))
    db.commit(); db.refresh(v)
    return vehicle_dict(v, db)


@app.put("/api/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: str, vehicle_update: VehicleUpdate, db: Session = Depends(get_db)):
    v = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    update_data = vehicle_update.dict(exclude_unset=True)
    previous_mileage = int(v.mileage or 0)
    for field, val in update_data.items():
        if hasattr(v, field):
            setattr(v, field, val)

    if "mileage" in update_data and int(v.mileage or 0) != previous_mileage:
        db.add(models.VehicleMileageRecord(vehicle_id=v.id, mileage=int(v.mileage or 0), recorded_at=now_str(), source="vehicle_update"))
    db.commit()
    db.refresh(v)
    return vehicle_dict(v, db)


@app.post("/api/vehicles/{vehicle_id}/remove", response_model=VehicleResponse)
def remove_vehicle(vehicle_id: str, removal: VehicleRemoval, db: Session = Depends(get_db)):
    v = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not v: raise HTTPException(status_code=404, detail="Vehicle not found")
    v.is_active = False; v.removal_reason = removal.reason
    v.removed_at = now_str(); v.status = "Kaldırıldı"
    db.add(models.VehicleRemoval(registry_no=v.chassis_no, reason=removal.reason, removed_at=v.removed_at))
    db.commit(); db.refresh(v)
    return vehicle_dict(v, db)


@app.post("/api/vehicles/{vehicle_id}/reactivate", response_model=VehicleResponse)
def reactivate_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    v = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not v: raise HTTPException(status_code=404, detail="Vehicle not found")
    v.is_active = True; v.removal_reason = None; v.removed_at = None; v.status = "Aktif"
    db.commit(); db.refresh(v)
    return vehicle_dict(v, db)


def vehicle_expense_dict(expense: models.VehicleExpense) -> dict:
    return {
        "id": expense.id, "vehicle_id": expense.vehicle_id, "kind": expense.kind,
        "amount": expense.amount, "date": expense.date, "liters": expense.liters,
        "mileage": expense.mileage, "note": expense.note
    }


@app.get("/api/vehicle-expenses", response_model=List[VehicleExpenseResponse])
def get_vehicle_expenses(customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.VehicleExpense)
    if customer_id:
        query = query.join(models.Vehicle).filter(models.Vehicle.customer_id == customer_id)
    records = query.order_by(models.VehicleExpense.date.desc(), models.VehicleExpense.id.desc()).all()
    return [vehicle_expense_dict(record) for record in records]


@app.post("/api/vehicle-expenses", response_model=VehicleExpenseResponse)
def create_vehicle_expense(expense: VehicleExpenseCreate, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == expense.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    record = models.VehicleExpense(**expense.dict())
    db.add(record)
    if int(expense.mileage) > int(vehicle.mileage or 0):
        vehicle.mileage = int(expense.mileage)
        db.add(models.VehicleMileageRecord(vehicle_id=vehicle.id, mileage=vehicle.mileage, recorded_at=expense.date, source="expense"))
    db.commit()
    db.refresh(record)
    return vehicle_expense_dict(record)


def tire_record_dict(record: models.TireRecord, vehicle: models.Vehicle) -> dict:
    return {
        "id": record.id, "vehicle_id": record.vehicle_id, "plate": vehicle.plate,
        "vehicle_brand": vehicle.brand, "vehicle_model": vehicle.model, "vehicle_year": vehicle.year,
        "vehicle_mileage": vehicle.mileage, "brand": record.brand, "size": record.size,
        "set_no": record.set_no, "season": record.season, "production_date": record.production_date,
        "installed_at": record.installed_at, "changed_at": record.changed_at,
        "inspected_at": record.inspected_at, "tread_depth_mm": record.tread_depth_mm, "status": record.status,
        "remaining_km": record.remaining_km, "position": record.position, "notes": record.notes,
        "updated_at": record.updated_at
    }


@app.get("/api/tires", response_model=List[TireRecordResponse])
def get_tire_records(customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.TireRecord, models.Vehicle).join(models.Vehicle, models.TireRecord.vehicle_id == models.Vehicle.id)
    if customer_id:
        query = query.filter(models.Vehicle.customer_id == customer_id)
    return [tire_record_dict(tire, vehicle) for tire, vehicle in query.order_by(models.TireRecord.updated_at.desc()).all()]


@app.post("/api/tires", response_model=TireRecordResponse)
def create_tire_record(data: TireRecordCreate, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    stamp = now_str()
    values = data.dict()
    record = models.TireRecord(**values, created_at=stamp, updated_at=stamp)
    db.add(record)
    if data.changed_at:
        vehicle.tire_change_date = data.changed_at
    db.commit(); db.refresh(record)
    return tire_record_dict(record, vehicle)


@app.put("/api/tires/{tire_id}", response_model=TireRecordResponse)
def update_tire_record(tire_id: int, data: TireRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(models.TireRecord).filter(models.TireRecord.id == tire_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Lastik kaydı bulunamadı.")
    values = data.dict(exclude_unset=True)
    vehicle_id = values.pop("vehicle_id", record.vehicle_id)
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    for key, value in values.items():
        setattr(record, key, value)
    record.vehicle_id = vehicle_id
    record.updated_at = now_str()
    if values.get("changed_at"):
        vehicle.tire_change_date = values["changed_at"]
    db.commit(); db.refresh(record)
    return tire_record_dict(record, vehicle)


@app.delete("/api/tires/{tire_id}")
def delete_tire_record(tire_id: int, db: Session = Depends(get_db)):
    record = db.query(models.TireRecord).filter(models.TireRecord.id == tire_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Lastik kaydı bulunamadı.")
    db.query(models.TireOperation).filter(models.TireOperation.tire_id == tire_id).update({"tire_id": None})
    db.delete(record); db.commit()
    return {"success": True}


def tire_operation_dict(record: models.TireOperation, vehicle: models.Vehicle) -> dict:
    return {"id": record.id, "vehicle_id": record.vehicle_id, "tire_id": record.tire_id,
            "plate": vehicle.plate, "type": record.type, "date": record.date,
            "mileage": record.mileage, "description": record.description, "status": record.status}


@app.get("/api/tire-operations", response_model=List[TireOperationResponse])
def get_tire_operations(customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.TireOperation, models.Vehicle).join(models.Vehicle, models.TireOperation.vehicle_id == models.Vehicle.id)
    if customer_id:
        query = query.filter(models.Vehicle.customer_id == customer_id)
    return [tire_operation_dict(operation, vehicle) for operation, vehicle in query.order_by(models.TireOperation.date.desc(), models.TireOperation.id.desc()).all()]


@app.post("/api/tire-operations", response_model=TireOperationResponse)
def create_tire_operation(data: TireOperationCreate, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    if data.tire_id and not db.query(models.TireRecord).filter_by(id=data.tire_id, vehicle_id=data.vehicle_id).first():
        raise HTTPException(status_code=404, detail="Bu araca bağlı lastik kaydı bulunamadı.")
    payload = data.dict()
    payload["date"] = payload["date"] or now_str()
    record = models.TireOperation(**payload)
    db.add(record)
    db.commit(); db.refresh(record)
    return tire_operation_dict(record, vehicle)


def vehicle_file_dict(record: models.VehicleFile) -> dict:
    return {
        "id": record.id, "vehicle_id": record.vehicle_id, "category": record.category,
        "document_type": record.document_type, "original_name": record.original_name,
        "content_type": record.content_type, "file_size": record.file_size,
        "uploaded_at": record.uploaded_at, "expiry_date": record.expiry_date,
        "url": "/uploads/vehicles/" + record.stored_name
    }


@app.get("/api/vehicles/{vehicle_id}/files", response_model=List[VehicleFileResponse])
def get_vehicle_files(vehicle_id: str, customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle or (customer_id is not None and vehicle.customer_id != customer_id):
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    records = db.query(models.VehicleFile).filter(models.VehicleFile.vehicle_id == vehicle_id).order_by(models.VehicleFile.uploaded_at.desc()).all()
    return [vehicle_file_dict(record) for record in records]


@app.post("/api/vehicles/{vehicle_id}/files", response_model=VehicleFileResponse)
async def upload_vehicle_file(
    vehicle_id: str, request: Request, category: str = Query(...),
    original_name: str = Query(...), document_type: Optional[str] = Query(None),
    expiry_date: Optional[str] = Query(None), db: Session = Depends(get_db)
):
    if category not in ("photo", "document"):
        raise HTTPException(status_code=400, detail="Dosya türü geçersiz.")
    if not db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first():
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    mime_type = request.headers.get("content-type", "application/octet-stream").split(";")[0].lower()
    allowed = {"image/jpeg", "image/png", "image/webp"} if category == "photo" else {"application/pdf", "image/jpeg", "image/png"}
    if mime_type not in allowed:
        raise HTTPException(status_code=415, detail="Bu dosya türü desteklenmiyor.")
    data = await request.body()
    if not data or len(data) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Dosya boş olamaz ve en fazla 15 MB olmalıdır.")
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".pdf"}:
        suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}[mime_type]
    stored_name = uuid.uuid4().hex + suffix
    (UPLOADS_DIR / stored_name).write_bytes(data)
    record = models.VehicleFile(
        vehicle_id=vehicle_id, category=category, document_type=document_type,
        original_name=Path(original_name).name[:250], stored_name=stored_name,
        content_type=mime_type, file_size=len(data), uploaded_at=now_str(), expiry_date=expiry_date
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return vehicle_file_dict(record)


@app.delete("/api/vehicles/{vehicle_id}/files/{file_id}")
def delete_vehicle_file(vehicle_id: str, file_id: int, db: Session = Depends(get_db)):
    record = db.query(models.VehicleFile).filter_by(id=file_id, vehicle_id=vehicle_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dosya bulunamadı.")
    try:
        (UPLOADS_DIR / record.stored_name).unlink(missing_ok=True)
    finally:
        db.delete(record)
        db.commit()
    return {"status": "deleted", "id": file_id}


def hgs_transaction_dict(record: models.HgsTransaction) -> dict:
    return {"id": record.id, "vehicle_id": record.vehicle_id, "type": record.type, "amount": record.amount, "date": record.date, "description": record.description, "balance": record.balance}


@app.get("/api/vehicles/{vehicle_id}/hgs", response_model=List[HgsTransactionResponse])
def get_vehicle_hgs(vehicle_id: str, customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle or (customer_id is not None and vehicle.customer_id != customer_id):
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    records = db.query(models.HgsTransaction).filter_by(vehicle_id=vehicle_id).order_by(models.HgsTransaction.date.desc(), models.HgsTransaction.id.desc()).all()
    return [hgs_transaction_dict(record) for record in records]


@app.post("/api/vehicles/{vehicle_id}/hgs", response_model=HgsTransactionResponse)
def create_vehicle_hgs_transaction(vehicle_id: str, data: HgsTransactionCreate, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    if data.type not in ("Yükleme", "Geçiş") or data.amount <= 0:
        raise HTTPException(status_code=400, detail="Yükleme veya geçiş türünde, sıfırdan büyük bir tutar girin.")
    balance = float(vehicle.hgs_balance or 0)
    balance += data.amount if data.type == "Yükleme" else -data.amount
    record = models.HgsTransaction(vehicle_id=vehicle_id, type=data.type, amount=data.amount, date=data.date, description=data.description, balance=balance)
    vehicle.hgs_balance = balance
    vehicle.hgs_active = True
    if data.type == "Yükleme":
        vehicle.hgs_last_reload_date = data.date
    db.add(record)
    db.commit()
    db.refresh(record)
    return hgs_transaction_dict(record)


def vehicle_location_dict(record: models.VehicleLocation) -> dict:
    return {"id": record.id, "vehicle_id": record.vehicle_id, "latitude": record.latitude, "longitude": record.longitude, "label": record.label, "source": record.source, "recorded_at": record.recorded_at}


@app.get("/api/vehicles/{vehicle_id}/locations", response_model=List[VehicleLocationResponse])
def get_vehicle_locations(vehicle_id: str, customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle or (customer_id is not None and vehicle.customer_id != customer_id):
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    records = db.query(models.VehicleLocation).filter_by(vehicle_id=vehicle_id).order_by(models.VehicleLocation.recorded_at.desc()).limit(100).all()
    return [vehicle_location_dict(record) for record in records]


@app.post("/api/vehicles/{vehicle_id}/locations", response_model=VehicleLocationResponse)
def create_vehicle_location(vehicle_id: str, data: VehicleLocationCreate, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    if not (-90 <= data.latitude <= 90 and -180 <= data.longitude <= 180):
        raise HTTPException(status_code=400, detail="Enlem veya boylam değeri geçersiz.")
    record = models.VehicleLocation(vehicle_id=vehicle_id, latitude=data.latitude, longitude=data.longitude, label=data.label, source="manual", recorded_at=now_str())
    vehicle.gps_latitude = data.latitude
    vehicle.gps_longitude = data.longitude
    vehicle.gps_location_label = data.label
    vehicle.gps_last_seen_at = record.recorded_at
    db.add(record)
    db.commit()
    db.refresh(record)
    return vehicle_location_dict(record)


@app.get("/api/reports")
def get_customer_reports(customer_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None,
                         db: Session = Depends(get_db)):
    """Aggregate only persisted customer data; unavailable metrics remain null/empty."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="Başlangıç tarihi bitiş tarihinden sonra olamaz.")
    vehicles = db.query(models.Vehicle).filter(models.Vehicle.customer_id == customer_id).all()
    vehicle_ids = [v.id for v in vehicles]
    if not vehicle_ids:
        return {"vehicles": [], "period": {"start": start_date, "end": end_date}}
    def in_range(value):
        day = (value or "")[:10]
        return (not start_date or day >= start_date) and (not end_date or day <= end_date)
    expenses = db.query(models.VehicleExpense).filter(models.VehicleExpense.vehicle_id.in_(vehicle_ids)).all()
    hgs = db.query(models.HgsTransaction).filter(models.HgsTransaction.vehicle_id.in_(vehicle_ids)).all()
    requests = db.query(models.Request).filter(models.Request.vehicle_id.in_(vehicle_ids)).all()
    tires = db.query(models.TireOperation).filter(models.TireOperation.vehicle_id.in_(vehicle_ids)).all()
    mileage = db.query(models.VehicleMileageRecord).filter(models.VehicleMileageRecord.vehicle_id.in_(vehicle_ids)).all()
    usage = db.query(models.VehicleUsageRecord).filter(models.VehicleUsageRecord.vehicle_id.in_(vehicle_ids)).all()
    locations = db.query(models.VehicleLocation).filter(models.VehicleLocation.vehicle_id.in_(vehicle_ids)).all()
    rows = []
    for vehicle in vehicles:
        ve = [e for e in expenses if e.vehicle_id == vehicle.id and in_range(e.date)]
        vh = [e for e in hgs if e.vehicle_id == vehicle.id and in_range(e.date)]
        vr = [r for r in requests if r.vehicle_id == vehicle.id and in_range(r.created_at)]
        vt = [t for t in tires if t.vehicle_id == vehicle.id and in_range(t.date)]
        vm_history = sorted([m for m in mileage if m.vehicle_id == vehicle.id], key=lambda x: x.recorded_at)
        vm = [m for m in vm_history if in_range(m.recorded_at)]
        vu = [u for u in usage if u.vehicle_id == vehicle.id and in_range(u.started_at)]
        vl = [l for l in locations if l.vehicle_id == vehicle.id and in_range(l.recorded_at)]
        categories = {}
        for item in ve:
            categories[item.kind] = categories.get(item.kind, 0) + float(item.amount or 0)
        hgs_total = sum(float(x.amount or 0) for x in vh if x.type == "Geçiş")
        service_total = sum(float((r.details or {}).get("invoice_amount") or (r.details or {}).get("total_estimated_cost") or 0) for r in vr if r.type == "servis")
        monthly_km = {}
        for idx, reading in enumerate(vm_history):
            if not in_range(reading.recorded_at): continue
            month = reading.recorded_at[:7]
            prev = vm_history[idx - 1].mileage if idx else None
            if prev is not None and reading.mileage >= prev:
                monthly_km[month] = monthly_km.get(month, 0) + reading.mileage - prev
        usage_minutes = 0
        for item in vu:
            try:
                usage_minutes += max(0, int((datetime.datetime.fromisoformat(item.ended_at) - datetime.datetime.fromisoformat(item.started_at)).total_seconds() // 60))
            except ValueError:
                pass
        usage_months = {}
        for item in vu:
            try:
                minutes = max(0, int((datetime.datetime.fromisoformat(item.ended_at) - datetime.datetime.fromisoformat(item.started_at)).total_seconds() // 60))
                key = item.started_at[:7]
                usage_months[key] = usage_months.get(key, 0) + minutes
            except ValueError:
                pass
        expense_map = {"Yakıt": "fuel", "Otopark": "parking", "HGS / OGS": "hgs", "Lastik": "tire", "Servis": "service", "Hasar": "damage"}
        normalized_expenses = {expense_map.get(k, k): v for k, v in categories.items()}
        service_days = {"maintenance": [], "tire": [], "damage": [], "mechanical": []}
        for req in vr:
            if req.type not in ("servis", "lastik"): continue
            if not req.completed_at: continue
            try: days = max(0, (datetime.datetime.fromisoformat(req.completed_at) - datetime.datetime.fromisoformat(req.created_at)).total_seconds() / 86400)
            except (ValueError, TypeError): continue
            category = "tire" if req.type == "lastik" else "damage" if "hasar" in str((req.details or {}).get("service_type", req.description)).lower() else "mechanical" if "mekanik" in str((req.details or {}).get("service_type", req.description)).lower() else "maintenance"
            service_days[category].append(days)
        average_days = {key: round(sum(values)/len(values), 1) if values else None for key, values in service_days.items()}
        available_days = [x for values in service_days.values() for x in values]
        average_days["total"] = round(sum(available_days)/len(available_days), 1) if available_days else None
        rows.append({"vehicle_id": vehicle.id, "plate": vehicle.plate, "user": vehicle.assignment_user,
            "current_mileage": vehicle.mileage, "monthly_km": monthly_km,
            "expenses": normalized_expenses, "hgs": hgs_total if vh else None, "service_cost": service_total if any(r.type == "servis" and ((r.details or {}).get("invoice_amount") is not None or (r.details or {}).get("total_estimated_cost") is not None) for r in vr) else None,
            "tire_operations": len(vt), "requests": {"total": len(vr), "accident": sum(1 for r in vr if r.type == "hasar" or "hasar" in (r.description or "").lower())},
            "usage_minutes": usage_minutes if vu else None,
            "usage_months": usage_months,
            "service_days": average_days,
            "monthly_rent": vehicle.monthly_rent,
            "locations": [{"latitude": l.latitude, "longitude": l.longitude, "label": l.label, "recorded_at": l.recorded_at} for l in sorted(vl, key=lambda x: x.recorded_at)],
            "location_duration": None})
    return {"vehicles": rows, "period": {"start": start_date, "end": end_date}}


@app.get("/api/vehicles/{vehicle_id}/mileage-records")
def get_mileage_records(vehicle_id: str, db: Session = Depends(get_db)):
    if not db.query(models.Vehicle).filter_by(id=vehicle_id).first(): raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    return [{"id": r.id, "vehicle_id": r.vehicle_id, "mileage": r.mileage, "recorded_at": r.recorded_at, "source": r.source}
        for r in db.query(models.VehicleMileageRecord).filter_by(vehicle_id=vehicle_id).order_by(models.VehicleMileageRecord.recorded_at.asc()).all()]


@app.post("/api/vehicles/{vehicle_id}/mileage-records")
def create_mileage_record(vehicle_id: str, payload: dict, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter_by(id=vehicle_id).first()
    if not vehicle: raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    value = int(payload.get("mileage", -1))
    if value < 0 or value < int(vehicle.mileage or 0): raise HTTPException(status_code=400, detail="Kilometre mevcut kayıttan düşük olamaz.")
    record = models.VehicleMileageRecord(vehicle_id=vehicle_id, mileage=value, recorded_at=payload.get("recorded_at") or now_str(), source=payload.get("source", "manual"))
    vehicle.mileage = value
    db.add(record); db.commit(); db.refresh(record)
    return {"id": record.id, "vehicle_id": record.vehicle_id, "mileage": record.mileage, "recorded_at": record.recorded_at, "source": record.source}


@app.get("/api/vehicles/{vehicle_id}/usage-records")
def get_usage_records(vehicle_id: str, db: Session = Depends(get_db)):
    if not db.query(models.Vehicle).filter_by(id=vehicle_id).first(): raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    return [{"id": r.id, "vehicle_id": r.vehicle_id, "started_at": r.started_at, "ended_at": r.ended_at, "source": r.source}
        for r in db.query(models.VehicleUsageRecord).filter_by(vehicle_id=vehicle_id).order_by(models.VehicleUsageRecord.started_at.desc()).all()]


@app.post("/api/vehicles/{vehicle_id}/usage-records")
def create_usage_record(vehicle_id: str, payload: dict, db: Session = Depends(get_db)):
    if not db.query(models.Vehicle).filter_by(id=vehicle_id).first(): raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    started, ended = payload.get("started_at"), payload.get("ended_at")
    try:
        if datetime.datetime.fromisoformat(ended) <= datetime.datetime.fromisoformat(started): raise ValueError()
    except (TypeError, ValueError): raise HTTPException(status_code=422, detail="Başlangıç ve bitiş tarihi geçerli olmalı; bitiş başlangıçtan sonra olmalı.")
    record = models.VehicleUsageRecord(vehicle_id=vehicle_id, started_at=started, ended_at=ended, source=payload.get("source", "manual"))
    db.add(record); db.commit(); db.refresh(record)
    return {"id": record.id, "vehicle_id": record.vehicle_id, "started_at": record.started_at, "ended_at": record.ended_at, "source": record.source}


@app.get("/api/vehicles/removals")
def get_vehicle_removals(db: Session = Depends(get_db)):
    return [{"registry_no": r.registry_no, "reason": r.reason, "removed_at": r.removed_at}
            for r in db.query(models.VehicleRemoval).all()]


@app.get("/api/vehicles/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: str, customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle or (customer_id is not None and vehicle.customer_id != customer_id):
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    return vehicle_dict(vehicle, db)


@app.get("/api/admin/vehicles/{vehicle_id}/services")
def get_vehicle_services(vehicle_id: str, db: Session = Depends(get_db)):
    reqs = db.query(models.Request).filter(models.Request.vehicle_id == vehicle_id).all()
    enriched = []
    for r in reqs:
        s = db.query(models.Supplier).filter(models.Supplier.id == r.supplier_id).first()
        enriched.append({
            **request_dict(r),
            "supplier_name": s.name if s else "Bilinmeyen"
        })
    return enriched



# ─────────────────── SUPPLIERS ─────────────────────────────────────────────

@app.get("/api/suppliers", response_model=List[SupplierResponse])
def get_suppliers(type: Optional[str] = None, include_unverified: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.Supplier)
    if not include_unverified:
        q = q.filter(models.Supplier.is_email_verified == True)
    if type:
        q = q.filter(models.Supplier.type == type)
    return [supplier_dict(s) for s in q.all()]


@app.post("/api/suppliers", response_model=SupplierResponse)
@app.post("/api/admin/suppliers", response_model=SupplierResponse)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    email_clean = supplier.email.lower().strip() if (supplier.email and supplier.email.strip()) else None

    if email_clean:
        existing = db.query(models.Supplier).filter(models.Supplier.email == email_clean).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"[{email_clean}] e-posta adresi zaten '{existing.name}' adıyla başka bir tedarikçiye kayıtlı."
            )

    token = None
    inv_status = "Davet Edilmedi"
    if supplier.send_invite and email_clean:
        token = generate_invitation_token()
        inv_status = "Davet Gönderildi"
        send_supplier_invitation_email(email_clean, supplier.name, token)

    try:
        s = models.Supplier(
            name=supplier.name, type=supplier.type, phone=supplier.phone,
            location=f"{supplier.district}, {supplier.city}",
            city=supplier.city, district=supplier.district,
            services=supplier.services, contract_type=supplier.contract_type,
            email=email_clean,
            invitation_token=token,
            invitation_status=inv_status
        )
        db.add(s); db.commit(); db.refresh(s)
        return supplier_dict(s)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tedarikçi eklenirken veritabanı hatası oluştu: {str(e)}"
        )


@app.post("/api/admin/suppliers/{supplier_id}/invite")
def send_supplier_invite(supplier_id: int, db: Session = Depends(get_db)):
    s = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Tedarikçi/Servis bulunamadı.")
    if not s.email:
        raise HTTPException(status_code=400, detail="Lütfen önce tedarikçiye bir e-posta adresi ekleyin.")
    
    token = generate_invitation_token()
    s.invitation_token = token
    s.invitation_status = "Davet Gönderildi"
    db.commit()
    
    result = send_supplier_invitation_email(s.email, s.name, token)
    return {
        "status": "success",
        "email": s.email,
        "supplier_name": s.name,
        "email_sent": result.get("email_sent", False),
        "smtp_configured": result.get("smtp_configured", False),
        "message": result.get("message", ""),
        "invite_url": result.get("invite_url", f"{APP_BASE_URL}/setup-password?token={token}")
    }


@app.get("/api/admin/smtp-status")
def get_smtp_status():
    import os
    from app.email_utils import _load_env_file
    _load_env_file()
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    gmail_api_configured = all(os.environ.get(key, "").strip() for key in (
        "GMAIL_API_CLIENT_ID",
        "GMAIL_API_CLIENT_SECRET",
        "GMAIL_API_REFRESH_TOKEN",
        "GMAIL_API_SENDER",
    ))
    smtp_configured = bool(smtp_host and smtp_user and smtp_pass)
    is_configured = smtp_configured or gmail_api_configured
    return {
        "configured": is_configured,
        "smtp_configured": smtp_configured,
        "gmail_api_configured": gmail_api_configured,
        "host_configured": bool(smtp_host),
        "user_configured": bool(smtp_user),
        "password_configured": bool(smtp_pass)
    }


@app.get("/api/supplier/verify-token/{token}")
@app.get("/api/customer/verify-token/{token}")
def verify_supplier_token(token: str, db: Session = Depends(get_db)):
    s = db.query(models.Supplier).filter(models.Supplier.invitation_token == token).first()
    if s:
        return {
            "status": "valid",
            "supplier_name": s.name,
            "email": s.email,
            "account_type": "service" if str(s.type or "").lower() in SERVICE_SUPPLIER_TYPES else "supplier"
        }
    c = db.query(models.Customer).filter(models.Customer.invitation_token == token).first()
    if c:
        return {
            "status": "valid",
            "supplier_name": c.company_name,
            "email": c.email,
            "account_type": "customer"
        }
    raise HTTPException(status_code=404, detail="Geçersiz veya kullanılmış davet bağlantısı.")


@app.post("/api/supplier/set-password")
@app.post("/api/customer/set-password")
def set_supplier_password(req: SetPasswordRequest, db: Session = Depends(get_db)):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalıdır.")

    s = db.query(models.Supplier).filter(models.Supplier.invitation_token == req.token).first()
    if s:
        s.password_hash = hash_password(req.password)
        s.invitation_status = "Aktif"
        s.invitation_token = None
        # The invitation link is delivered to this address; consuming it proves mailbox access.
        s.is_email_verified = True
        s.verification_token = None
        db.commit()
        return {
            "status": "success",
            "message": "Şifreniz oluşturuldu, e-posta adresiniz doğrulandı. Giriş yapabilirsiniz.",
            "account_type": "service" if str(s.type or "").lower() in SERVICE_SUPPLIER_TYPES else "supplier"
        }

    c = db.query(models.Customer).filter(models.Customer.invitation_token == req.token).first()
    if c:
        c.password_hash = hash_password(req.password)
        c.invitation_status = "Aktif"
        c.invitation_token = None
        c.is_email_verified = True
        c.verification_token = None
        db.commit()
        return {
            "status": "success",
            "message": "Şifreniz oluşturuldu, e-posta adresiniz doğrulandı. Giriş yapabilirsiniz.",
            "account_type": "customer"
        }

    raise HTTPException(status_code=404, detail="Geçersiz veya süresi dolmuş davet bağlantısı.")


SERVICE_SUPPLIER_TYPES = {"servis", "lastik", "yol_yardim"}


@app.post("/api/supplier/register")
def supplier_register(req: SupplierRegisterRequest, db: Session = Depends(get_db)):
    email_clean = req.email.lower().strip()
    name = req.name.strip()
    if not name or not email_clean:
        raise HTTPException(status_code=400, detail="Firma adı ve e-posta zorunludur.")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Şifre en az 8 karakter olmalıdır.")
    if req.account_type == "service" and not req.service_type:
        raise HTTPException(status_code=400, detail="Servis türünü seçin.")

    if db.query(models.Supplier).filter(models.Supplier.email.ilike(email_clean)).first():
        raise HTTPException(status_code=409, detail="Bu e-posta adresi zaten kayıtlı.")
    if db.query(models.Customer).filter(models.Customer.email.ilike(email_clean)).first():
        raise HTTPException(status_code=409, detail="Bu e-posta adresi başka bir hesapta kayıtlı.")
    if db.query(models.CustomerPortalUser).filter(models.CustomerPortalUser.email.ilike(email_clean)).first():
        raise HTTPException(status_code=409, detail="Bu e-posta adresi başka bir hesapta kayıtlı.")

    account_type = req.account_type
    supplier_type = req.service_type if account_type == "service" else "ikame_arac"
    token = generate_invitation_token()
    supplier = models.Supplier(
        name=name,
        type=supplier_type,
        email=email_clean,
        phone=(req.phone or "").strip(),
        location="",
        city="",
        district="",
        services=[supplier_type],
        contract_type="Başvuru Bekliyor",
        password_hash=hash_password(req.password),
        invitation_status="E-posta Doğrulaması Bekleniyor",
        is_email_verified=False,
        verification_token=token,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    email_result = send_email_verification_email(supplier.email, supplier.name, token)
    return {
        "status": "pending_verification",
        "message": "Kayıt oluşturuldu. Giriş yapmadan önce e-posta adresinizi doğrulayın.",
        "account_type": account_type,
        "email_sent": email_result.get("email_sent", False),
        "smtp_configured": email_result.get("smtp_configured", False),
        "supplier": supplier_dict(supplier),
    }


def _supplier_login(creds: AdminLoginRequest, db: Session, expected_type: str):
    email_clean = creds.email.lower().strip()
    s = db.query(models.Supplier).filter(models.Supplier.email == email_clean).first()
    
    if not s:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"[{email_clean}] e-posta adresine tanımlı bir tedarikçi veya servis bulunamadı. Lütfen yöneticinizle iletişime geçin."
        )

    is_service_account = str(s.type or "").lower() in SERVICE_SUPPLIER_TYPES
    if expected_type == "service" and not is_service_account:
        raise HTTPException(status_code=403, detail="Bu hesap tedarikçi portalına aittir. Tedarikçi girişini kullanın.")
    if expected_type == "supplier" and is_service_account:
        raise HTTPException(status_code=403, detail="Bu hesap servis portalına aittir. Servis girişini kullanın.")

    if not s.password_hash or not verify_password(creds.password, s.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı. Davetli hesaplar önce e-postalarındaki bağlantıdan şifre oluşturmalıdır."
        )

    if getattr(s, "is_email_verified", False) is not True:
        if not getattr(s, 'verification_token', None):
            v_token = generate_invitation_token()
            s.verification_token = v_token
            db.commit()
            send_email_verification_email(s.email, s.name, v_token)
        raise HTTPException(status_code=403, detail="E-posta adresiniz henüz doğrulanmadı. E-postanızdaki doğrulama bağlantısını kullanın veya yeniden gönderin.")

    return {
        "status": "success",
        "token": f"supplier_token_{s.id}_{datetime.datetime.now().timestamp()}",
        "supplier": supplier_dict(s)
    }


@app.post("/api/supplier/login")
def supplier_login(creds: AdminLoginRequest, db: Session = Depends(get_db)):
    return _supplier_login(creds, db, "supplier")


@app.post("/api/service/login")
def service_login(creds: AdminLoginRequest, db: Session = Depends(get_db)):
    return _supplier_login(creds, db, "service")


@app.post("/api/customer/login")
def customer_login(creds: AdminLoginRequest, db: Session = Depends(get_db)):
    email_clean = creds.email.lower().strip()
    c = db.query(models.Customer).filter(models.Customer.email.ilike(email_clean)).first()
    
    if not c:
        user = db.query(models.CustomerPortalUser).filter(models.CustomerPortalUser.email.ilike(email_clean), models.CustomerPortalUser.is_active == True).first()
        if not user or not user.password_hash or not verify_password(creds.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-posta veya şifre hatalı.")
        if not getattr(user, "is_email_verified", False):
            if not user.verification_token:
                user.verification_token = generate_invitation_token()
                db.commit()
                send_email_verification_email(user.email, user.name, user.verification_token)
            raise HTTPException(status_code=403, detail="E-posta adresiniz henüz doğrulanmadı. E-postanızdaki doğrulama bağlantısını kullanın veya yeniden gönderin.")
        c = db.query(models.Customer).filter_by(id=user.customer_id).first()
        if not c: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı şirket hesabı bulunamadı.")
        return {"status":"success", "token":f"customer_user_token_{user.id}_{datetime.datetime.now().timestamp()}",
            "customer":customer_dict(c), "user":{"id":user.id,"name":user.name,"email":user.email,"role":user.role,"assigned_plate":user.assigned_plate}}

    if c.password_hash:
        if not verify_password(creds.password, c.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Hatalı şifre! Lütfen girmiş olduğunuz şifreyi kontrol edin."
            )
    else:
        raise HTTPException(status_code=401, detail="Bu müşteri hesabı için henüz şifre oluşturulmamış. E-postanızdaki davet bağlantısını kullanın.")

    if getattr(c, "is_email_verified", False) is not True:
        if not getattr(c, 'verification_token', None):
            v_token = generate_invitation_token()
            c.verification_token = v_token
            db.commit()
            send_email_verification_email(c.email, c.company_name, v_token)
        raise HTTPException(status_code=403, detail="E-posta adresiniz henüz doğrulanmadı. E-postanızdaki doğrulama bağlantısını kullanın veya yeniden gönderin.")

    return {
        "status": "success",
        "token": f"customer_token_{c.id}_{datetime.datetime.now().timestamp()}",
        "customer": customer_dict(c)
    }


@app.post("/api/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    import secrets
    email_clean = req.email.lower().strip()
    if not email_clean:
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir e-posta adresi girin.")

    reset_token = secrets.token_urlsafe(32)
    user_found = False
    recipient_name = "Kullanıcı"

    # 1. Search Customer
    c = db.query(models.Customer).filter(models.Customer.email.ilike(email_clean)).first()
    if c:
        c.reset_token = reset_token
        c.reset_token_expires = str(datetime.datetime.now() + datetime.timedelta(hours=2))
        recipient_name = c.company_name
        user_found = True

    # 2. Search Supplier if not found
    if not user_found:
        s = db.query(models.Supplier).filter(models.Supplier.email == email_clean).first()
        if s:
            s.reset_token = reset_token
            s.reset_token_expires = str(datetime.datetime.now() + datetime.timedelta(hours=2))
            recipient_name = s.name
            user_found = True

    # 3. Search AdminUser if not found
    if not user_found:
        a = db.query(models.AdminUser).filter(models.AdminUser.email == email_clean).first()
        if a:
            a.reset_token = reset_token
            a.reset_token_expires = str(datetime.datetime.now() + datetime.timedelta(hours=2))
            recipient_name = "Yönetici"
            user_found = True

    if user_found:
        db.commit()
        send_password_reset_email(email_clean, recipient_name, reset_token)

    return {
        "status": "success",
        "message": "Eğer e-posta sistemimizde kayıtlı ise şifre sıfırlama bağlantısı gönderilmiştir. Lütfen gelen kutunuzu ve spam klasörünüzü kontrol edin."
    }


@app.post("/api/auth/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalıdır.")

    if not req.token:
        raise HTTPException(status_code=400, detail="Geçersiz veya eksik doğrulama kodu.")

    # 1. Customer
    c = db.query(models.Customer).filter(models.Customer.reset_token == req.token).first()
    if c:
        c.password_hash = hash_password(req.password)
        c.reset_token = None
        c.reset_token_expires = None
        db.commit()
        return {"status": "success", "message": "Şifreniz başarıyla sıfırlandı! Şimdi giriş yapabilirsiniz."}

    # 2. Supplier
    s = db.query(models.Supplier).filter(models.Supplier.reset_token == req.token).first()
    if s:
        s.password_hash = hash_password(req.password)
        s.reset_token = None
        s.reset_token_expires = None
        db.commit()
        return {"status": "success", "message": "Şifreniz başarıyla sıfırlandı! Şimdi giriş yapabilirsiniz."}

    # 3. Admin
    a = db.query(models.AdminUser).filter(models.AdminUser.reset_token == req.token).first()
    if a:
        a.password_hash = hash_password(req.password)
        a.reset_token = None
        a.reset_token_expires = None
        db.commit()
        return {"status": "success", "message": "Şifreniz başarıyla sıfırlandı! Şimdi giriş yapabilirsiniz."}

    raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş şifre sıfırlama bağlantısı.")


@app.get("/api/auth/verify-email/{token}")
@app.post("/api/auth/verify-email/{token}")
def verify_email_token(token: str, db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=400, detail="Geçersiz veya eksik doğrulama kodu.")

    c = db.query(models.Customer).filter(models.Customer.verification_token == token).first()
    if c:
        c.is_email_verified = True
        c.verification_token = None
        if c.password_hash:
            c.invitation_status = "Aktif"
        db.commit()
        return {
            "status": "success",
            "message": "E-posta adresiniz başarıyla doğrulandı! Artık platformdaki tüm işlemleri gerçekleştirebilirsiniz.",
            "customer": customer_dict(c),
            "account_type": "customer",
        }

    s = db.query(models.Supplier).filter(models.Supplier.verification_token == token).first()
    if s:
        s.is_email_verified = True
        s.verification_token = None
        if s.password_hash:
            s.invitation_status = "Aktif"
        db.commit()
        return {
            "status": "success",
            "message": "E-posta adresiniz başarıyla doğrulandı! Artık platformdaki tüm işlemleri gerçekleştirebilirsiniz.",
            "supplier": supplier_dict(s),
            "account_type": "service" if str(s.type or "").lower() in SERVICE_SUPPLIER_TYPES else "supplier"
        }

    user = db.query(models.CustomerPortalUser).filter(models.CustomerPortalUser.verification_token == token).first()
    if user:
        user.is_email_verified = True
        user.verification_token = None
        db.commit()
        return {
            "status": "success",
            "message": "E-posta adresiniz başarıyla doğrulandı. Artık giriş yapabilirsiniz.",
            "account_type": "customer",
        }

    raise HTTPException(status_code=404, detail="Geçersiz veya süresi dolmuş e-posta doğrulama bağlantısı.")


@app.post("/api/auth/resend-verification")
def resend_verification_email(req: ResendVerificationRequest, db: Session = Depends(get_db)):
    email_clean = req.email.lower().strip()
    kind = req.account_type
    account = None
    if kind in (None, "customer"):
        account = db.query(models.Customer).filter(models.Customer.email.ilike(email_clean)).first()
        if account:
            name = account.company_name
    if not account and kind in (None, "customer_user"):
        account = db.query(models.CustomerPortalUser).filter(models.CustomerPortalUser.email.ilike(email_clean), models.CustomerPortalUser.is_active == True).first()
        if account:
            name = account.name
    if not account and kind in (None, "service", "supplier"):
        candidate = db.query(models.Supplier).filter(models.Supplier.email.ilike(email_clean)).first()
        if candidate:
            is_service = str(candidate.type or "").lower() in SERVICE_SUPPLIER_TYPES
            if kind is None or (kind == "service") == is_service:
                account = candidate
                name = candidate.name

    if not account:
        raise HTTPException(status_code=404, detail="Bu hesap türü için kayıtlı e-posta adresi bulunamadı.")
    if account.is_email_verified:
        return {"status": "info", "message": "E-posta adresiniz zaten doğrulanmıştır."}

    v_token = account.verification_token or generate_invitation_token()
    account.verification_token = v_token
    db.commit()
    res = send_email_verification_email(account.email, name, v_token)
    email_sent = res.get("email_sent", False)
    return {
        "status": "success" if email_sent else "warning",
        "message": f"Doğrulama bağlantısı [{account.email}] adresine gönderildi." if email_sent else "E-posta gönderilemedi. Lütfen daha sonra tekrar deneyin veya sistem yöneticisiyle iletişime geçin.",
        "email_sent": email_sent,
        "smtp_configured": res.get("smtp_configured", False),
    }


@app.post("/api/customer/register")
def customer_register(req: CustomerRegisterRequest, db: Session = Depends(get_db)):
    email_clean = req.email.lower().strip()
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalıdır.")

    v_token = generate_invitation_token()

    if db.query(models.Supplier).filter(models.Supplier.email.ilike(email_clean)).first() or db.query(models.CustomerPortalUser).filter(models.CustomerPortalUser.email.ilike(email_clean)).first():
        raise HTTPException(status_code=409, detail="Bu e-posta adresi başka bir hesapta kayıtlı.")

    existing = db.query(models.Customer).filter(models.Customer.email.ilike(email_clean)).first()
    if existing:
        if existing.password_hash:
            raise HTTPException(
                status_code=400,
                detail="Bu e-posta adresi ile zaten kayıtlı bir müşteri bulunuyor. Lütfen giriş yapın."
            )
        else:
            existing.password_hash = hash_password(req.password)
            if req.company_name:
                existing.company_name = req.company_name
            if req.phone:
                existing.phone = req.phone
            existing.invitation_status = "E-posta Doğrulaması Bekleniyor"
            existing.invitation_token = None
            existing.is_email_verified = False
            existing.verification_token = v_token
            db.commit()
            c = existing
    else:
        company_name = req.company_name.strip() if req.company_name else email_clean.split("@")[0].capitalize() + " A.Ş."
        c = models.Customer(
            company_name=company_name,
            legal_title=company_name + " Anonim Şirketi",
            email=email_clean,
            phone=req.phone or "",
            password_hash=hash_password(req.password),
            status="Aktif",
            invitation_status="E-posta Doğrulaması Bekleniyor",
            address="Maslak, İstanbul",
            documents_uploaded=False,
            documents={},
            is_email_verified=False,
            verification_token=v_token
        )
        db.add(c)
        db.commit()
        db.refresh(c)

    # Send verification email
    email_result = send_email_verification_email(c.email, c.company_name, v_token)

    return {
        "status": "success",
        "message": "Hesabınız başarıyla oluşturuldu! Lütfen e-posta kutunuza gönderilen doğrulama bağlantısına tıklayarak hesabınızı onaylayın.",
        "account_type": "customer",
        "email_sent": email_result.get("email_sent", False),
        "smtp_configured": email_result.get("smtp_configured", False),
        "customer": customer_dict(c),
    }


@app.post("/api/customer/documents")
def upload_customer_documents(payload: CustomerDocumentUpload, db: Session = Depends(get_db)):
    if not payload.customer_id:
        raise HTTPException(status_code=400, detail="Müşteri ID gereklidir.")

    c = db.query(models.Customer).filter(models.Customer.id == payload.customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")

    current_docs = dict(c.documents or {})
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if payload.tax_plate:
        current_docs["tax_plate"] = {
            "file_name": payload.tax_plate,
            "uploaded_at": timestamp_str,
            "status": "Onaylandı"
        }
    if payload.signature_circular:
        current_docs["signature_circular"] = {
            "file_name": payload.signature_circular,
            "uploaded_at": timestamp_str,
            "status": "Onaylandı"
        }
    if payload.activity_certificate:
        current_docs["activity_certificate"] = {
            "file_name": payload.activity_certificate,
            "uploaded_at": timestamp_str,
            "status": "Onaylandı"
        }
    if payload.trade_registry:
        current_docs["trade_registry"] = {
            "file_name": payload.trade_registry,
            "uploaded_at": timestamp_str,
            "status": "Onaylandı"
        }

    c.documents = dict(current_docs)
    required_keys = ["tax_plate", "signature_circular", "activity_certificate", "trade_registry"]
    c.documents_uploaded = all(k in c.documents and isinstance(c.documents[k], dict) and bool(c.documents[k].get("url")) for k in required_keys)

    db.commit()
    return {
        "status": "success",
        "message": "Şirket evrakları başarıyla kaydedildi.",
        "customer": customer_dict(c)
    }


@app.get("/api/customer/documents")
def get_customer_documents(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    return {
        "documents_uploaded": has_actual_customer_documents(c),
        "documents": c.documents or {}
    }


@app.post("/api/customer/documents/{doc_type}/file")
async def upload_customer_document_file(doc_type: str, customer_id: int, original_name: str, request: Request, db: Session = Depends(get_db)):
    allowed_types = {"tax_plate", "signature_circular", "activity_certificate", "trade_registry"}
    if doc_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Belge türü geçersiz.")
    customer = db.query(models.Customer).filter_by(id=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    content_type = request.headers.get("content-type", "application/octet-stream").split(";")[0].lower()
    if content_type not in {"application/pdf", "image/jpeg", "image/png"}:
        raise HTTPException(status_code=415, detail="PDF, JPEG veya PNG dosyası yükleyin.")
    data = await request.body()
    if not data or len(data) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Dosya boş olamaz ve en fazla 15 MB olabilir.")
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".pdf", ".jpg", ".jpeg", ".png"}:
        suffix = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}[content_type]
    stored = f"{customer_id}_{uuid.uuid4().hex}{suffix}"
    (CUSTOMER_UPLOADS_DIR / stored).write_bytes(data)
    documents = dict(customer.documents or {})
    documents[doc_type] = {"file_name": Path(original_name).name[:250], "url": f"/uploads/customer-documents/{stored}", "content_type": content_type, "file_size": len(data), "uploaded_at": now_str(), "status": "İncelemede"}
    customer.documents = documents
    customer.documents_uploaded = all(key in documents and isinstance(documents[key], dict) and bool(documents[key].get("url")) for key in allowed_types)
    db.commit()
    return {"status": "success", "customer": customer_dict(customer)}


@app.get("/api/customer/settings/{key}")
def get_customer_setting(key: str, customer_id: int, db: Session = Depends(get_db)):
    setting = db.query(models.CustomerSetting).filter_by(customer_id=customer_id, key=key).first()
    value = dict(setting.value or {}) if setting else {}
    secret_key = "apiSecret" if key == "gps" else "clientCode" if key == "utts" else None
    if secret_key:
        configured = bool(value.pop(secret_key, ""))
        value[f"{secret_key}_configured"] = configured
    return {"key": key, "value": value}


@app.put("/api/customer/settings/{key}")
def save_customer_setting(key: str, customer_id: int, payload: dict, db: Session = Depends(get_db)):
    if not db.query(models.Customer).filter_by(id=customer_id).first():
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    setting = db.query(models.CustomerSetting).filter_by(customer_id=customer_id, key=key).first()
    stored_value = dict(setting.value or {}) if setting else {}
    secret_key = "apiSecret" if key == "gps" else "clientCode" if key == "utts" else None
    incoming = dict(payload)
    if secret_key:
        secret = incoming.pop(secret_key, "")
        incoming.pop(f"{secret_key}_configured", None)
        if secret: stored_value[secret_key] = secret
    stored_value.update(incoming)
    if not setting:
        setting = models.CustomerSetting(customer_id=customer_id, key=key, value=stored_value)
        db.add(setting)
    else:
        setting.value = stored_value
    db.commit()
    return get_customer_setting(key, customer_id, db)


def customer_user_dict(user):
    return {"id": user.id, "customer_id": user.customer_id, "name": user.name, "email": user.email,
            "phone": user.phone, "role": user.role, "assigned_plate": user.assigned_plate,
            "is_active": user.is_active, "is_email_verified": bool(user.is_email_verified),
            "created_at": user.created_at, "has_password": bool(user.password_hash)}


@app.get("/api/customer/users")
def list_customer_users(customer_id: int, db: Session = Depends(get_db)):
    return [customer_user_dict(u) for u in db.query(models.CustomerPortalUser).filter_by(customer_id=customer_id).order_by(models.CustomerPortalUser.id.desc()).all()]


@app.post("/api/customer/users")
def create_customer_user(payload: dict, db: Session = Depends(get_db)):
    customer_id = payload.get("customer_id")
    if not db.query(models.Customer).filter_by(id=customer_id).first():
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    if not payload.get("name") or not payload.get("email"):
        raise HTTPException(status_code=422, detail="Ad ve e-posta zorunludur.")
    if not payload.get("password") or len(payload["password"]) < 8:
        raise HTTPException(status_code=422, detail="İlk giriş şifresi en az 8 karakter olmalıdır.")
    duplicate = db.query(models.CustomerPortalUser).filter(models.CustomerPortalUser.email.ilike(payload["email"].strip())).first()
    owner = db.query(models.Customer).filter(models.Customer.email.ilike(payload["email"].strip())).first()
    supplier_owner = db.query(models.Supplier).filter(models.Supplier.email.ilike(payload["email"].strip())).first()
    if duplicate or owner or supplier_owner: raise HTTPException(status_code=409, detail="Bu e-posta adresi zaten kayıtlı.")
    verification_token = generate_invitation_token()
    user = models.CustomerPortalUser(customer_id=customer_id, name=payload["name"], email=payload["email"],
        password_hash=hash_password(payload["password"]),
        phone=payload.get("phone"), role=payload.get("role", "Sürücü"), assigned_plate=payload.get("assigned_plate"),
        is_active=payload.get("is_active", True), is_email_verified=False,
        verification_token=verification_token, created_at=now_str())
    db.add(user); db.commit(); db.refresh(user)
    email_result = send_email_verification_email(user.email, user.name, verification_token)
    return {**customer_user_dict(user), "email_sent": email_result.get("email_sent", False),
            "smtp_configured": email_result.get("smtp_configured", False)}


@app.put("/api/customer/users/{user_id}")
def update_customer_user(user_id: int, customer_id: int, payload: dict, db: Session = Depends(get_db)):
    user = db.query(models.CustomerPortalUser).filter_by(id=user_id, customer_id=customer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if payload.get("email"):
        duplicate = db.query(models.CustomerPortalUser).filter(models.CustomerPortalUser.email.ilike(payload["email"].strip()), models.CustomerPortalUser.id != user_id).first()
        owner = db.query(models.Customer).filter(models.Customer.email.ilike(payload["email"].strip())).first()
        supplier_owner = db.query(models.Supplier).filter(models.Supplier.email.ilike(payload["email"].strip())).first()
        if duplicate or owner or supplier_owner: raise HTTPException(status_code=409, detail="Bu e-posta adresi zaten kayıtlı.")
        email_changed = payload["email"].strip().lower() != user.email.strip().lower()
    else:
        email_changed = False
    for key in ("name", "email", "phone", "role", "assigned_plate", "is_active"):
        if key in payload: setattr(user, key, payload[key])
    if payload.get("password"):
        if len(payload["password"]) < 8: raise HTTPException(status_code=422, detail="Şifre en az 8 karakter olmalıdır.")
        user.password_hash = hash_password(payload["password"])
    if email_changed:
        user.is_email_verified = False
        user.verification_token = generate_invitation_token()
        db.commit()
        send_email_verification_email(user.email, user.name, user.verification_token)
    db.commit(); db.refresh(user)
    return customer_user_dict(user)


@app.delete("/api/customer/users/{user_id}")
def delete_customer_user(user_id: int, customer_id: int, db: Session = Depends(get_db)):
    user = db.query(models.CustomerPortalUser).filter_by(id=user_id, customer_id=customer_id).first()
    if not user: raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    db.delete(user); db.commit()
    return {"status": "deleted"}


@app.get("/api/customer/delivery-forms")
def list_delivery_forms(customer_id: int, db: Session = Depends(get_db)):
    return [{"id": f.id, "vehicle_id": f.vehicle_id, "plate": db.query(models.Vehicle.plate).filter_by(id=f.vehicle_id).scalar(),
        "receiver": f.receiver, "issuer": f.issuer, "date": f.date, "km": f.mileage, "notes": f.notes}
        for f in db.query(models.DeliveryForm).filter_by(customer_id=customer_id).order_by(models.DeliveryForm.date.desc()).all()]


@app.post("/api/customer/delivery-forms")
def create_delivery_form(payload: dict, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter_by(id=payload.get("vehicle_id"), customer_id=payload.get("customer_id")).first()
    if not vehicle: raise HTTPException(status_code=404, detail="Müşteriye ait araç bulunamadı.")
    form = models.DeliveryForm(customer_id=vehicle.customer_id, vehicle_id=vehicle.id, receiver=payload.get("receiver", ""),
        issuer=payload.get("issuer"), date=payload.get("date") or now_str(), mileage=int(payload.get("km") or 0), notes=payload.get("notes"))
    db.add(form); db.commit(); db.refresh(form)
    return {"id": form.id, "vehicle_id": form.vehicle_id, "plate": vehicle.plate, "receiver": form.receiver,
        "issuer": form.issuer, "date": form.date, "km": form.mileage, "notes": form.notes}


@app.delete("/api/customer/documents/{doc_type}")
def delete_customer_document(doc_type: str, customer_id: int, db: Session = Depends(get_db)):
    c = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")

    current_docs = dict(c.documents or {})
    if doc_type in current_docs:
        old_document = current_docs[doc_type]
        if isinstance(old_document, dict) and old_document.get("url", "").startswith("/uploads/customer-documents/"):
            try: (CUSTOMER_UPLOADS_DIR / Path(old_document["url"]).name).unlink(missing_ok=True)
            except OSError: pass
        del current_docs[doc_type]
        c.documents = dict(current_docs)
        
        required_keys = ["tax_plate", "signature_circular", "activity_certificate", "trade_registry"]
        c.documents_uploaded = all(k in c.documents and isinstance(c.documents[k], dict) and bool(c.documents[k].get("url")) for k in required_keys)

        db.commit()

        return {
            "status": "success",
            "message": "Belge başarıyla silindi.",
            "customer": customer_dict(c)
        }
    else:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")



@app.delete("/api/admin/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    s = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Tedarikçi/Servis bulunamadı.")
    db.delete(s)
    db.commit()
    return {"status": "success", "message": f"'{s.name}' başarıyla silindi."}


# ─────────────────── REQUESTS ──────────────────────────────────────────────

STATUS_MAP = {
    "servis": "Serviste", "lastik": "Lastik Değişiminde",
    "yol_yardim": "Yol Yardımında", "ikame_arac": "İkame Araç Bekliyor"
}


def _enrich_request(r: models.Request, db: Session) -> dict:
    d = request_dict(r)
    v = db.query(models.Vehicle).filter(models.Vehicle.id == r.vehicle_id).first()
    s = db.query(models.Supplier).filter(models.Supplier.id == r.supplier_id).first()
    d["vehicle_plate"]      = v.plate if v else "Bilinmeyen"
    d["vehicle_brand_model"] = f"{v.brand} {v.model}" if v else "Bilinmeyen"
    d["supplier_name"]      = s.name if s else ("Otomatik Atanacak" if not r.supplier_id else "Bilinmeyen")
    if r.type == "yol_yardim":
        case = db.query(models.RoadsideCase).filter_by(request_id=r.id).first()
        if case:
            d["roadside_case"] = {"id":case.id,"team_name":case.team_name,"team_phone":case.team_phone,"eta_minutes":case.eta_minutes,"distance_km":case.distance_km,"progress":case.progress}
    return d


@app.get("/api/requests")
def get_requests(customer_id: Optional[int] = None, supplier_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Request)
    if customer_id:
        query = query.join(models.Vehicle, models.Request.vehicle_id == models.Vehicle.id).filter(models.Vehicle.customer_id == customer_id)
    if supplier_id:
        query = query.filter(models.Request.supplier_id == supplier_id)
    return [_enrich_request(r, db) for r in query.order_by(models.Request.created_at.desc(), models.Request.id.desc()).all()]


@app.post("/api/requests", response_model=RequestResponse)
def create_request(req: RequestCreate, db: Session = Depends(get_db)):
    v = db.query(models.Vehicle).filter(models.Vehicle.id == req.vehicle_id).first()
    if not v: raise HTTPException(status_code=404, detail="Vehicle not found")
    if req.supplier_id is not None:
        s = db.query(models.Supplier).filter(models.Supplier.id == req.supplier_id).first()
        if not s: raise HTTPException(status_code=404, detail="Supplier not found")

    r = models.Request(
        vehicle_id=req.vehicle_id, supplier_id=req.supplier_id,
        type=req.type, status="Beklemede",
        description=req.description, created_at=now_str(), details=req.details
    )
    db.add(r)
    if req.type == "servis":
        db.flush()
        details = dict(req.details or {})
        prefix = "HS" if "hasar" in str(details.get("service_type", "")).lower() or "kaza" in str(details.get("service_type", "")).lower() else "IS"
        details.setdefault("work_order_no", f"{prefix}-{datetime.datetime.now().year}-{r.id:04d}")
        r.details = details
    elif req.type == "yol_yardim":
        db.flush()
        details = dict(req.details or {})
        case_no = f"YA-{datetime.datetime.now().year}-{r.id:04d}"
        details["roadside_case_no"] = case_no
        r.details = details
        case = models.RoadsideCase(
            request_id=r.id, vehicle_id=v.id, case_no=case_no,
            incident=", ".join(details.get("incidents") or []) or details.get("incident", "Yol Yardım"),
            location=details.get("location") or " / ".join(filter(None, [details.get("district"), details.get("city")])),
            latitude=details.get("latitude"), longitude=details.get("longitude"),
            description=req.description, status="Beklemede", progress=0,
            photos=details.get("photos", [details["photo"]] if details.get("photo") else []),
            created_at=now_str(), updated_at=now_str()
        )
        db.add(case)
        db.flush()
        db.add(models.RoadsideEvent(case_id=case.id, status="Beklemede", title="Talep Oluşturuldu", description=req.description, created_at=r.created_at))
    v.status = STATUS_MAP.get(req.type, "Aktif")
    db.commit(); db.refresh(r)
    return request_dict(r)


ROADSIDE_PROGRESS = {
    "Beklemede": 0, "Ekip Atandı": 15, "Yola Çıktı": 40, "Yolda": 60,
    "Ekip Varış Noktasında": 85, "Çözüldü": 100, "İptal Edildi": 0
}


def roadside_case_dict(case: models.RoadsideCase, vehicle: models.Vehicle) -> dict:
    return {
        "id": case.id, "request_id": case.request_id, "vehicle_id": case.vehicle_id,
        "case_no": case.case_no, "plate": vehicle.plate, "vehicle_brand": vehicle.brand,
        "vehicle_model": vehicle.model, "vehicle_year": vehicle.year, "chassis_no": vehicle.chassis_no,
        "engine_no": getattr(vehicle, "engine_no", None), "color": getattr(vehicle, "color", None),
        "contract_start_date": getattr(vehicle, "contract_start_date", None),
        "contract_end_date": getattr(vehicle, "contract_end_date", None),
        "incident": case.incident, "location": case.location,
        "latitude": case.latitude, "longitude": case.longitude,
        "description": case.description, "status": case.status, "progress": case.progress,
        "team_name": case.team_name, "team_phone": case.team_phone,
        "dispatched_at": case.dispatched_at, "eta_minutes": case.eta_minutes,
        "distance_km": case.distance_km, "arrived_at": case.arrived_at,
        "resolved_at": case.resolved_at, "response_minutes": case.response_minutes,
        "photos": case.photos or [], "created_at": case.created_at, "updated_at": case.updated_at
    }


def roadside_event_dict(event: models.RoadsideEvent) -> dict:
    return {"id": event.id, "case_id": event.case_id, "status": event.status,
            "title": event.title, "description": event.description,
            "eta_minutes": event.eta_minutes, "distance_km": event.distance_km,
            "created_at": event.created_at}


@app.get("/api/roadside-cases", response_model=List[RoadsideCaseResponse])
def get_roadside_cases(customer_id: Optional[int] = None, status: Optional[str] = None,
                       days: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.RoadsideCase, models.Vehicle).join(
        models.Vehicle, models.RoadsideCase.vehicle_id == models.Vehicle.id
    )
    if customer_id:
        query = query.filter(models.Vehicle.customer_id == customer_id)
    if status:
        query = query.filter(models.RoadsideCase.status == status)
    if days:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=min(days, 3650))).strftime("%Y-%m-%d")
        query = query.filter(models.RoadsideCase.created_at >= cutoff)
    return [roadside_case_dict(case, vehicle) for case, vehicle in query.order_by(
        models.RoadsideCase.created_at.desc(), models.RoadsideCase.id.desc()
    ).all()]


@app.post("/api/roadside-cases", response_model=RoadsideCaseResponse)
def create_roadside_case(data: RoadsideCaseCreate, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Araç bulunamadı.")
    if (data.latitude is None) != (data.longitude is None):
        raise HTTPException(status_code=400, detail="Konum için enlem ve boylam birlikte girilmelidir.")
    if data.latitude is not None and (not -90 <= data.latitude <= 90 or not -180 <= data.longitude <= 180):
        raise HTTPException(status_code=400, detail="Konum koordinatları geçersiz.")
    stamp = now_str()
    request_details = {"incident": data.incident, "location": data.location,
                       "latitude": data.latitude, "longitude": data.longitude,
                       "photos": data.photos or []}
    request = models.Request(vehicle_id=vehicle.id, supplier_id=None, type="yol_yardim",
                             status="Beklemede", description=data.description or data.incident,
                             created_at=stamp, details=request_details)
    db.add(request); db.flush()
    case_no = f"YA-{datetime.datetime.now().year}-{request.id:04d}"
    request_details["roadside_case_no"] = case_no
    request.details = request_details
    case = models.RoadsideCase(
        request_id=request.id, vehicle_id=vehicle.id, case_no=case_no,
        incident=data.incident, location=data.location, latitude=data.latitude,
        longitude=data.longitude, description=data.description,
        status="Beklemede", progress=0, photos=data.photos or [],
        created_at=stamp, updated_at=stamp
    )
    db.add(case); db.flush()
    vehicle.status = "Yol Yardımında"
    db.add(models.RoadsideEvent(case_id=case.id, status="Beklemede", title="Talep Oluşturuldu",
                                description=data.description or data.incident, created_at=stamp))
    if data.latitude is not None:
        vehicle.gps_latitude = data.latitude; vehicle.gps_longitude = data.longitude
        vehicle.gps_location_label = data.location; vehicle.gps_last_seen_at = stamp
        db.add(models.VehicleLocation(vehicle_id=vehicle.id, latitude=data.latitude,
                                      longitude=data.longitude, label=data.location,
                                      source="roadside_customer", recorded_at=stamp))
    db.commit(); db.refresh(case)
    return roadside_case_dict(case, vehicle)


@app.get("/api/roadside-cases/{case_id}", response_model=RoadsideCaseResponse)
def get_roadside_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(models.RoadsideCase).filter(models.RoadsideCase.id == case_id).first()
    if not case: raise HTTPException(status_code=404, detail="Yol yardım talebi bulunamadı.")
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == case.vehicle_id).first()
    return roadside_case_dict(case, vehicle)


@app.put("/api/roadside-cases/{case_id}", response_model=RoadsideCaseResponse)
def update_roadside_case(case_id: int, data: RoadsideCaseUpdate, db: Session = Depends(get_db)):
    case = db.query(models.RoadsideCase).filter(models.RoadsideCase.id == case_id).first()
    if not case: raise HTTPException(status_code=404, detail="Yol yardım talebi bulunamadı.")
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == case.vehicle_id).first()
    values = data.dict(exclude_unset=True)
    latitude = values.get("latitude", case.latitude)
    longitude = values.get("longitude", case.longitude)
    if (latitude is None) != (longitude is None):
        raise HTTPException(status_code=400, detail="Konum için enlem ve boylam birlikte girilmelidir.")
    if latitude is not None and (not -90 <= latitude <= 90 or not -180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Konum koordinatları geçersiz.")
    old_status = case.status
    for key, value in values.items(): setattr(case, key, value)
    if "status" in values:
        case.progress = values.get("progress", ROADSIDE_PROGRESS.get(case.status, case.progress))
        if case.status in ("Yola Çıktı", "Yolda") and not case.dispatched_at: case.dispatched_at = now_str()
        if case.status in ("Ekip Varış Noktasında", "Çözüldü") and not case.arrived_at:
            case.arrived_at = now_str()
            start = case.dispatched_at or case.created_at
            try: case.response_minutes = max(0, int((datetime.datetime.now() - datetime.datetime.strptime(start, "%Y-%m-%d %H:%M")).total_seconds() // 60))
            except (ValueError, TypeError): pass
        if case.status == "Çözüldü": case.resolved_at = now_str()
        if case.request_id:
            request = db.query(models.Request).filter(models.Request.id == case.request_id).first()
            if request: request.status = case.status
        if case.status in ("Çözüldü", "İptal Edildi") and vehicle:
            other = db.query(models.Request).filter(
                models.Request.vehicle_id == vehicle.id,
                models.Request.id != case.request_id,
                models.Request.status.notin_(["Tamamlandı", "Çözüldü", "İptal Edildi"])
            ).first()
            vehicle.status = {"servis": "Serviste", "lastik": "Lastik Değişiminde",
                              "yol_yardim": "Yol Yardımında", "ikame_arac": "İkame Araç Bekliyor"}.get(other.type, "Aktif") if other else "Aktif"
    if "latitude" in values and vehicle:
        vehicle.gps_latitude = case.latitude; vehicle.gps_longitude = case.longitude
        vehicle.gps_location_label = case.location; vehicle.gps_last_seen_at = now_str()
        db.add(models.VehicleLocation(vehicle_id=vehicle.id, latitude=case.latitude,
                                      longitude=case.longitude, label=case.location,
                                      source="roadside_customer", recorded_at=vehicle.gps_last_seen_at))
    case.updated_at = now_str()
    if case.status != old_status:
        db.add(models.RoadsideEvent(case_id=case.id, status=case.status,
            title={"Beklemede":"Talep Oluşturuldu", "Ekip Atandı":"Yol Yardım Ekibi Atandı",
                   "Yola Çıktı":"Ekip Yola Çıktı", "Yolda":"Ekip Yola Çıktı",
                   "Ekip Varış Noktasında":"Ekip Varış Noktasında", "Çözüldü":"Sorun Çözüldü",
                   "İptal Edildi":"Talep İptal Edildi"}.get(case.status, case.status),
            description=case.description, eta_minutes=case.eta_minutes,
            distance_km=case.distance_km, created_at=case.updated_at))
    db.commit(); db.refresh(case)
    return roadside_case_dict(case, vehicle)


@app.get("/api/roadside-cases/{case_id}/events", response_model=List[RoadsideEventResponse])
def get_roadside_events(case_id: int, db: Session = Depends(get_db)):
    if not db.query(models.RoadsideCase).filter(models.RoadsideCase.id == case_id).first():
        raise HTTPException(status_code=404, detail="Yol yardım talebi bulunamadı.")
    rows = db.query(models.RoadsideEvent).filter_by(case_id=case_id).order_by(
        models.RoadsideEvent.created_at.asc(), models.RoadsideEvent.id.asc()).all()
    return [roadside_event_dict(event) for event in rows]


@app.post("/api/roadside-cases/{case_id}/events", response_model=RoadsideEventResponse)
def create_roadside_event(case_id: int, data: RoadsideEventCreate, db: Session = Depends(get_db)):
    case = db.query(models.RoadsideCase).filter(models.RoadsideCase.id == case_id).first()
    if not case: raise HTTPException(status_code=404, detail="Yol yardım talebi bulunamadı.")
    event = models.RoadsideEvent(case_id=case.id, status=data.status, title=data.title,
        description=data.description, eta_minutes=data.eta_minutes,
        distance_km=data.distance_km, created_at=now_str())
    db.add(event); db.commit(); db.refresh(event)
    return roadside_event_dict(event)


@app.put("/api/requests/{request_id}/status")
def update_request_status(request_id: int, status_update: StatusUpdate, db: Session = Depends(get_db)):
    r = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not r: raise HTTPException(status_code=404, detail="Request not found")
    r.status = status_update.status

    roadside_case = db.query(models.RoadsideCase).filter(models.RoadsideCase.request_id == r.id).first() if r.type == "yol_yardim" else None
    if roadside_case:
        roadside_case.status = status_update.status
        roadside_case.progress = ROADSIDE_PROGRESS.get(status_update.status, roadside_case.progress)
        for field in ("team_name", "team_phone", "eta_minutes", "distance_km"):
            value = getattr(status_update, field, None)
            if value is not None: setattr(roadside_case, field, value)
        if status_update.status in ("Yola Çıktı", "Yolda") and not roadside_case.dispatched_at: roadside_case.dispatched_at = now_str()
        if status_update.status in ("Ekip Varış Noktasında", "Çözüldü") and not roadside_case.arrived_at:
            roadside_case.arrived_at = now_str()
            start = roadside_case.dispatched_at or roadside_case.created_at
            try: roadside_case.response_minutes = max(0, int((datetime.datetime.strptime(roadside_case.arrived_at, "%Y-%m-%d %H:%M") - datetime.datetime.strptime(start, "%Y-%m-%d %H:%M")).total_seconds() // 60))
            except (ValueError, TypeError): pass
        if status_update.status == "Çözüldü": roadside_case.resolved_at = now_str()
        roadside_case.updated_at = now_str()
        db.add(models.RoadsideEvent(case_id=roadside_case.id, status=status_update.status,
            title=status_update.status, description=r.description,
            eta_minutes=roadside_case.eta_minutes, distance_km=roadside_case.distance_km,
            created_at=roadside_case.updated_at))

    if status_update.status in ("Tamamlandı", "Çözüldü"):
        r.completed_at = now_str()
    elif status_update.status in ("İptal Edildi", "Beklemede", "Onaylandı", "İşlemde"):
        r.completed_at = None

    if status_update.status in ["Tamamlandı", "Çözüldü", "İptal Edildi"]:
        v = db.query(models.Vehicle).filter(models.Vehicle.id == r.vehicle_id).first()
        if v:
            other = db.query(models.Request).filter(
                models.Request.vehicle_id == v.id,
                models.Request.id != request_id,
                models.Request.status.notin_(["Tamamlandı", "Çözüldü", "İptal Edildi"])
            ).first()
            v.status = STATUS_MAP.get(other.type, "Aktif") if other else "Aktif"

    db.commit()
    return request_dict(r)


@app.post("/api/requests/{request_id}/checkin")
def service_checkin(request_id: int, data: ServiceCheckIn, db: Session = Depends(get_db)):
    r = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not r: raise HTTPException(status_code=404, detail="Request not found")
    
    details = dict(r.details or {})
    details["entry_date"] = now_str()
    details["entry_mileage"] = data.entry_mileage
    details["fuel_level"] = data.fuel_level
    details["driver_name"] = data.driver_name
    details["driver_phone"] = data.driver_phone
    details["entry_notes"] = data.entry_notes
    if not details.get("work_order_no"):
        details["work_order_no"] = f"SERV-{datetime.datetime.now().year}-{r.id:04d}"
    
    r.details = details
    r.status = "Servise Girdi"
    
    v = db.query(models.Vehicle).filter(models.Vehicle.id == r.vehicle_id).first()
    if v and data.entry_mileage > (v.mileage or 0):
        v.mileage = data.entry_mileage
        db.add(models.VehicleMileageRecord(vehicle_id=v.id, mileage=data.entry_mileage, recorded_at=now_str(), source="service_checkin"))

    db.commit()
    return _enrich_request(r, db)


@app.put("/api/requests/{request_id}/work-order")
def service_work_order(request_id: int, data: ServiceWorkOrder, db: Session = Depends(get_db)):
    r = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not r: raise HTTPException(status_code=404, detail="Request not found")
    
    details = dict(r.details or {})
    for key, value in data.dict(exclude_unset=True).items():
        details[key] = value
    if not details.get("work_order_no"):
        details["work_order_no"] = f"SERV-{datetime.datetime.now().year}-{r.id:04d}"
    
    r.details = details
    db.commit()
    return _enrich_request(r, db)


@app.post("/api/requests/{request_id}/invoice")
def service_invoice(request_id: int, data: ServiceInvoice, db: Session = Depends(get_db)):
    r = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not r: raise HTTPException(status_code=404, detail="Request not found")
    
    details = dict(r.details or {})
    details["invoice_no"] = data.invoice_no
    details["invoice_date"] = data.invoice_date
    details["invoice_amount"] = data.invoice_amount
    details["invoice_notes"] = data.invoice_notes
    details["invoice_status"] = "Yüklendi / Onay Bekliyor"
    if data.file_name:
        details["invoice_file_name"] = data.file_name
    if data.file_url:
        details["invoice_file_url"] = data.file_url

    r.details = details
    db.commit()
    return _enrich_request(r, db)


# ─────────────────── DASHBOARD ─────────────────────────────────────────────

@app.get("/api/dashboard/stats")
def get_dashboard_stats(customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    if customer_id:
        unassigned = db.query(models.Vehicle).filter(models.Vehicle.customer_id == None).all()
        if unassigned:
            for u in unassigned:
                u.customer_id = customer_id
            db.commit()

    q = db.query(models.Vehicle).filter(models.Vehicle.is_active == True)
    if customer_id:
        q = q.filter(models.Vehicle.customer_id == customer_id)
    active = q.all()
    total = len(active)
    fuel_stats = {}
    for v in active:
        fuel_stats[v.fuel] = fuel_stats.get(v.fuel, 0) + 1

    vehicle_ids = [v.id for v in active]
    req_q = db.query(models.Request)
    if customer_id:
        req_q = req_q.filter(models.Request.vehicle_id.in_(vehicle_ids))
    reqs = req_q.all()

    total_km = sum(v.mileage for v in active if v.mileage)
    return {
        "total_vehicles":       total,
        "active_vehicles":      sum(1 for v in active if v.status == "Aktif"),
        "in_service":           sum(1 for v in active if v.status in ["Serviste", "Servis"]),
        "tire_change":          sum(1 for v in active if v.status in ["Lastik Değişiminde", "Lastik"]),
        "roadside_assistance":  sum(1 for v in active if v.status in ["Yol Yardımında", "Yol Yardım"]),
        "replacement_waiting":  sum(1 for v in active if v.status in ["İkame Araç Bekliyor", "İkame Araç"]),
        "total_requests":       len(reqs),
        "pending_requests":     sum(1 for r in reqs if r.status in ["Beklemede", "Onaylandı", "İşlemde"]),
        "completed_requests":   sum(1 for r in reqs if r.status == "Tamamlandı"),
        "avg_mileage":          int(total_km / total) if total else 0,
        "total_km":             total_km,
        "total_usage_minutes":  sum(max(0, int((datetime.datetime.fromisoformat(item.ended_at) - datetime.datetime.fromisoformat(item.started_at)).total_seconds() // 60)) for item in db.query(models.VehicleUsageRecord).filter(models.VehicleUsageRecord.vehicle_id.in_([v.id for v in active])).all()),
        "fuel_stats":           fuel_stats
    }


# ─────────────────── COMPANY PROFILE ───────────────────────────────────────

@app.get("/api/company/profile")
def get_company_profile(customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    c = None
    if customer_id:
        c = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not c:
        c = db.query(models.Customer).first()

    if c:
        active_count = db.query(models.Vehicle).filter(models.Vehicle.customer_id == c.id, models.Vehicle.is_active == True).count()
        return {
            "id": c.id,
            "company_name": c.company_name,
            "legal_title": c.legal_title or c.company_name,
            "registered_vehicles_count": c.registered_vehicles_count or 0,
            "actual_vehicles_count": active_count,
            "email": c.email or "-",
            "phone": c.phone or "-",
            "address": c.address or "-",
            "documents_uploaded": has_actual_customer_documents(c),
            "documents": getattr(c, 'documents', {}) or {}
        }
    return {
        "id": 0,
        "company_name": "Müşteri Portalı",
        "legal_title": "Müşteri Portalı A.Ş.",
        "registered_vehicles_count": 0,
        "actual_vehicles_count": 0,
        "email": "-",
        "phone": "-",
        "address": "-"
    }


# ─────────────────── ADMIN — AUTH ───────────────────────────────────────────

@app.post("/api/admin/login")
@app.post("/admin/login")
def admin_login(creds: AdminLoginRequest, db: Session = Depends(get_db)):
    email_clean = creds.email.lower().strip()
    admin_user = db.query(models.AdminUser).filter(models.AdminUser.email == email_clean).first()
    
    if not admin_user or not verify_password(creds.password, admin_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı e-posta adresi veya şifre!"
        )
    
    return {
        "status": "success",
        "email": admin_user.email,
        "token": f"admin_token_{admin_user.id}_{datetime.datetime.now().timestamp()}"
    }


# ─────────────────── ADMIN — CUSTOMERS ─────────────────────────────────────

@app.get("/api/admin/customers")
def get_admin_customers(db: Session = Depends(get_db)):
    result = []
    for c in db.query(models.Customer).all():
        actual = db.query(models.Vehicle).filter(
            models.Vehicle.customer_id == c.id,
            models.Vehicle.is_active == True
        ).count()
        deficit = max(0, c.registered_vehicles_count - actual)
        result.append(customer_dict(c, actual=actual, deficit=deficit))
    return result


@app.post("/api/customers")
@app.post("/api/admin/customers")
def create_admin_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    email_clean = customer.email.lower().strip() if (customer.email and customer.email.strip()) else None

    token = None
    inv_status = "Davet Edilmedi"
    if customer.send_invite and email_clean:
        token = generate_invitation_token()
        inv_status = "Davet Gönderildi"
        send_supplier_invitation_email(email_clean, customer.company_name, token)

    c = models.Customer(
        company_name=customer.company_name,
        legal_title=customer.legal_title,
        email=email_clean,
        phone=customer.phone,
        address=customer.address,
        registered_vehicles_count=customer.registered_vehicles_count,
        contract_amount=customer.contract_amount,
        status="Aktif",
        invitation_token=token,
        invitation_status=inv_status,
        signed_at=now_str()
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return customer_dict(c, actual=0, deficit=customer.registered_vehicles_count)


@app.post("/api/admin/customers/{customer_id}/invite")
def send_customer_invite(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    if not c.email:
        raise HTTPException(status_code=400, detail="Lütfen önce müşteriye bir e-posta adresi ekleyin.")
    
    token = generate_invitation_token()
    c.invitation_token = token
    c.invitation_status = "Davet Gönderildi"
    db.commit()
    
    result = send_supplier_invitation_email(c.email, c.company_name, token)
    return {
        "status": "success",
        "email": c.email,
        "customer_name": c.company_name,
        "company_name": c.company_name,
        "email_sent": result.get("email_sent", False),
        "smtp_configured": result.get("smtp_configured", False),
        "message": result.get("message", ""),
        "invite_url": result.get("invite_url", f"{APP_BASE_URL}/setup-password?token={token}")
    }


@app.delete("/api/admin/customers/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")
    db.delete(c)
    db.commit()
    return {"status": "success", "message": f"'{c.company_name}' başarıyla silindi."}


@app.put("/api/admin/customers/{customer_id}")
def update_admin_customer(customer_id: int, updated: CustomerUpdate, db: Session = Depends(get_db)):
    c = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not c: raise HTTPException(status_code=404, detail="Customer not found")
    c.company_name = updated.company_name; c.legal_title = updated.legal_title
    c.email = updated.email; c.phone = updated.phone; c.address = updated.address
    c.registered_vehicles_count = updated.registered_vehicles_count
    c.contract_amount = updated.contract_amount
    db.commit(); db.refresh(c)
    actual = db.query(models.Vehicle).filter(models.Vehicle.customer_id == c.id, models.Vehicle.is_active == True).count()
    return customer_dict(c, actual=actual, deficit=max(0, c.registered_vehicles_count - actual))


@app.get("/api/admin/customers/{customer_id}/vehicles")
def get_customer_vehicles(customer_id: int, db: Session = Depends(get_db)):
    return [vehicle_dict(v) for v in db.query(models.Vehicle).filter(models.Vehicle.customer_id == customer_id).all()]


@app.get("/api/admin/customers/{customer_id}/services")
def get_customer_services(customer_id: int, db: Session = Depends(get_db)):
    vehicle_ids = [v.id for v in db.query(models.Vehicle).filter(models.Vehicle.customer_id == customer_id).all()]
    reqs = db.query(models.Request).filter(models.Request.vehicle_id.in_(vehicle_ids)).all()
    return [_enrich_request(r, db) for r in reqs]
