import datetime
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
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
    RequestCreate, RequestResponse,
    SupplierCreate, SupplierResponse, StatusUpdate,
    VehicleRemoval, QuoteUpdate,
    CustomerCreate, CustomerUpdate, BidCreate, BidResponse,
    AdminLoginRequest, SetPasswordRequest,
    ServiceCheckIn, ServiceWorkOrder, ServiceInvoice,
    CustomerRegisterRequest, CustomerDocumentUpload,
    ForgotPasswordRequest, ResetPasswordRequest, ResendVerificationRequest
)

app = FastAPI(title="FleetRent API", version="2.0.0")

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
        "is_email_verified": getattr(s, 'is_email_verified', True) if getattr(s, 'is_email_verified', None) is not None else True
    }


def vehicle_dict(v: models.Vehicle, db: Session = None) -> dict:
    d = {
        "id": v.id, "chassis_no": v.chassis_no, "plate": v.plate,
        "brand": v.brand, "model": v.model, "year": v.year, "fuel": v.fuel,
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
        "created_at": r.created_at, "details": r.details or {}
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
        "documents_uploaded": getattr(c, 'documents_uploaded', False) or False,
        "documents": getattr(c, 'documents', {}) or {},
        "is_email_verified": getattr(c, 'is_email_verified', True) if getattr(c, 'is_email_verified', None) is not None else True
    }
    if actual is not None:
        d["actual_vehicle_count"] = actual
        d["vehicle_deficit"] = deficit
    return d


# ─────────────────── QUOTES ────────────────────────────────────────────────

@app.get("/api/quotes", response_model=List[QuoteResponse])
def get_quotes(db: Session = Depends(get_db)):
    return [quote_dict(q, db) for q in db.query(models.Quote).all()]


@app.post("/api/quotes", response_model=QuoteResponse)
def create_quote(quote: QuoteCreate, db: Session = Depends(get_db)):
    cust_id = None
    cust_info = {}
    if quote.email:
        cust = db.query(models.Customer).filter(models.Customer.email == quote.email).first()
        if cust:
            if not getattr(cust, 'documents_uploaded', False):
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
    db.add(v); db.commit(); db.refresh(v)
    return vehicle_dict(v, db)


@app.put("/api/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: str, vehicle_update: VehicleUpdate, db: Session = Depends(get_db)):
    v = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    update_data = vehicle_update.dict(exclude_unset=True)
    for field, val in update_data.items():
        if hasattr(v, field):
            setattr(v, field, val)

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


@app.get("/api/vehicles/removals")
def get_vehicle_removals(db: Session = Depends(get_db)):
    return [{"registry_no": r.registry_no, "reason": r.reason, "removed_at": r.removed_at}
            for r in db.query(models.VehicleRemoval).all()]


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
def get_suppliers(type: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Supplier)
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
    smtp_from = os.environ.get("SMTP_FROM", "").strip()
    is_configured = bool(smtp_host and smtp_user)
    return {
        "configured": is_configured,
        "smtp_host": smtp_host or "Tanımlanmamış",
        "smtp_user": smtp_user or "Tanımlanmamış",
        "smtp_from": smtp_from or smtp_user or "Tanımlanmamış"
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
            "account_type": "supplier"
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
        db.commit()
        return {
            "status": "success",
            "message": "Şifreniz başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz."
        }

    c = db.query(models.Customer).filter(models.Customer.invitation_token == req.token).first()
    if c:
        c.password_hash = hash_password(req.password)
        c.invitation_status = "Aktif"
        c.invitation_token = None
        db.commit()
        return {
            "status": "success",
            "message": "Şifreniz başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz."
        }

    raise HTTPException(status_code=404, detail="Geçersiz veya süresi dolmuş davet bağlantısı.")


@app.post("/api/supplier/login")
def supplier_login(creds: AdminLoginRequest, db: Session = Depends(get_db)):
    email_clean = creds.email.lower().strip()
    s = db.query(models.Supplier).filter(models.Supplier.email == email_clean).first()
    
    if not s:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"[{email_clean}] e-posta adresine tanımlı bir tedarikçi veya servis bulunamadı. Lütfen yöneticinizle iletişime geçin."
        )

    if s.password_hash:
        if not verify_password(creds.password, s.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Hatalı şifre! Lütfen girmiş olduğunuz şifreyi kontrol edin."
            )
    else:
        # If admin added email but supplier hasn't set password yet via invite, set it now
        s.password_hash = hash_password(creds.password)
        s.invitation_status = "Aktif"
        db.commit()

    if getattr(s, 'is_email_verified', False) is not True:
        s.is_email_verified = True
        db.commit()

    return {
        "status": "success",
        "token": f"supplier_token_{s.id}_{datetime.datetime.now().timestamp()}",
        "supplier": supplier_dict(s)
    }


@app.post("/api/customer/login")
def customer_login(creds: AdminLoginRequest, db: Session = Depends(get_db)):
    email_clean = creds.email.lower().strip()
    c = db.query(models.Customer).filter(models.Customer.email.ilike(email_clean)).first()
    
    if not c:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"[{email_clean}] e-posta adresine tanımlı aktif bir müşteri bulunamadı. Lütfen yöneticinizle iletişime geçin."
        )

    if c.password_hash:
        if not verify_password(creds.password, c.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Hatalı şifre! Lütfen girmiş olduğunuz şifreyi kontrol edin."
            )
    else:
        # First time login setup fallback
        c.password_hash = hash_password(creds.password)
        c.invitation_status = "Aktif"
        db.commit()

    if getattr(c, 'is_email_verified', False) is not True:
        c.is_email_verified = True
        db.commit()

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
        db.commit()
        return {
            "status": "success",
            "message": "E-posta adresiniz başarıyla doğrulandı! Artık platformdaki tüm işlemleri gerçekleştirebilirsiniz.",
            "customer": customer_dict(c)
        }

    s = db.query(models.Supplier).filter(models.Supplier.verification_token == token).first()
    if s:
        s.is_email_verified = True
        s.verification_token = None
        db.commit()
        return {
            "status": "success",
            "message": "E-posta adresiniz başarıyla doğrulandı! Artık platformdaki tüm işlemleri gerçekleştirebilirsiniz.",
            "supplier": supplier_dict(s)
        }

    raise HTTPException(status_code=404, detail="Geçersiz veya süresi dolmuş e-posta doğrulama bağlantısı.")


@app.post("/api/auth/resend-verification")
def resend_verification_email(req: ResendVerificationRequest, db: Session = Depends(get_db)):
    email_clean = req.email.lower().strip()
    
    # 1. Customer
    c = db.query(models.Customer).filter(models.Customer.email.ilike(email_clean)).first()
    if c:
        if c.is_email_verified:
            return {"status": "info", "message": "E-posta adresiniz zaten doğrulanmıştır."}

        v_token = c.verification_token or generate_invitation_token()
        c.verification_token = v_token
        db.commit()
        res = send_email_verification_email(c.email, c.company_name, v_token)
        email_sent = res.get("email_sent", False)
        return {
            "status": "success" if email_sent else "warning",
            "message": f"Doğrulama bağlantısı [{c.email}] adresine gönderildi." if email_sent else "SMTP e-posta sunucusu henüz yapılandırılmadığından e-posta gönderilemedi. Lütfen sistem yöneticinizle iletişime geçiniz.",
            "email_sent": email_sent,
            "smtp_configured": res.get("smtp_configured", False)
        }

    # 2. Supplier
    s = db.query(models.Supplier).filter(models.Supplier.email == email_clean).first()
    if s:
        if s.is_email_verified:
            return {"status": "info", "message": "E-posta adresiniz zaten doğrulanmıştır."}

        v_token = s.verification_token or generate_invitation_token()
        s.verification_token = v_token
        db.commit()
        res = send_email_verification_email(s.email, s.name, v_token)
        email_sent = res.get("email_sent", False)
        return {
            "status": "success" if email_sent else "warning",
            "message": f"Doğrulama bağlantısı [{s.email}] adresine gönderildi." if email_sent else "SMTP e-posta sunucusu henüz yapılandırılmadığından e-posta gönderilemedi. Lütfen sistem yöneticinizle iletişime geçiniz.",
            "email_sent": email_sent,
            "smtp_configured": res.get("smtp_configured", False)
        }

    raise HTTPException(status_code=404, detail="Kayıtlı e-posta adresi bulunamadı.")


@app.post("/api/customer/register")
def customer_register(req: CustomerRegisterRequest, db: Session = Depends(get_db)):
    email_clean = req.email.lower().strip()
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalıdır.")

    v_token = generate_invitation_token()

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
            existing.invitation_status = "Aktif"
            existing.is_email_verified = True
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
            invitation_status="Aktif",
            address="Maslak, İstanbul",
            documents_uploaded=False,
            documents={},
            is_email_verified=True,
            verification_token=v_token
        )
        db.add(c)
        db.commit()
        db.refresh(c)

    return {
        "status": "success",
        "message": "Hesabınız başarıyla oluşturuldu!",
        "token": f"customer_token_{c.id}_{datetime.datetime.now().timestamp()}",
        "customer": customer_dict(c)
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
    c.documents_uploaded = all(k in c.documents for k in required_keys)

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
        "documents_uploaded": bool(c.documents_uploaded),
        "documents": c.documents or {}
    }


@app.delete("/api/customer/documents/{doc_type}")
def delete_customer_document(doc_type: str, customer_id: int, db: Session = Depends(get_db)):
    c = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı.")

    current_docs = dict(c.documents or {})
    if doc_type in current_docs:
        del current_docs[doc_type]
        c.documents = dict(current_docs)
        
        required_keys = ["tax_plate", "signature_circular", "activity_certificate", "trade_registry"]
        c.documents_uploaded = all(k in c.documents for k in required_keys)

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
    d["supplier_name"]      = s.name if s else "Bilinmeyen"
    return d


@app.get("/api/requests")
def get_requests(db: Session = Depends(get_db)):
    return [_enrich_request(r, db) for r in db.query(models.Request).all()]


@app.post("/api/requests", response_model=RequestResponse)
def create_request(req: RequestCreate, db: Session = Depends(get_db)):
    v = db.query(models.Vehicle).filter(models.Vehicle.id == req.vehicle_id).first()
    if not v: raise HTTPException(status_code=404, detail="Vehicle not found")
    s = db.query(models.Supplier).filter(models.Supplier.id == req.supplier_id).first()
    if not s: raise HTTPException(status_code=404, detail="Supplier not found")

    r = models.Request(
        vehicle_id=req.vehicle_id, supplier_id=req.supplier_id,
        type=req.type, status="Beklemede",
        description=req.description, created_at=now_str(), details=req.details
    )
    db.add(r)
    v.status = STATUS_MAP.get(req.type, "Aktif")
    db.commit(); db.refresh(r)
    return request_dict(r)


@app.put("/api/requests/{request_id}/status")
def update_request_status(request_id: int, status_update: StatusUpdate, db: Session = Depends(get_db)):
    r = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not r: raise HTTPException(status_code=404, detail="Request not found")
    r.status = status_update.status

    if status_update.status in ["Tamamlandı", "İptal Edildi"]:
        v = db.query(models.Vehicle).filter(models.Vehicle.id == r.vehicle_id).first()
        if v:
            other = db.query(models.Request).filter(
                models.Request.vehicle_id == v.id,
                models.Request.id != request_id,
                models.Request.status.notin_(["Tamamlandı", "İptal Edildi"])
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
        details["work_order_no"] = f"SERV-2026-{r.id:04d}"
    
    r.details = details
    r.status = "Servise Girdi"
    
    v = db.query(models.Vehicle).filter(models.Vehicle.id == r.vehicle_id).first()
    if v and data.entry_mileage > (v.mileage or 0):
        v.mileage = data.entry_mileage

    db.commit()
    return _enrich_request(r, db)


@app.put("/api/requests/{request_id}/work-order")
def service_work_order(request_id: int, data: ServiceWorkOrder, db: Session = Depends(get_db)):
    r = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not r: raise HTTPException(status_code=404, detail="Request not found")
    
    details = dict(r.details or {})
    if data.diagnosis_notes is not None:
        details["diagnosis_notes"] = data.diagnosis_notes
    if data.parts_list is not None:
        details["parts_list"] = data.parts_list
    if data.labor_cost is not None:
        details["labor_cost"] = data.labor_cost
    if data.total_estimated_cost is not None:
        details["total_estimated_cost"] = data.total_estimated_cost
    
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
        "total_usage_minutes":  sum(getattr(v, 'usage_minutes', 0) or 0 for v in active),
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
            "documents_uploaded": getattr(c, 'documents_uploaded', False) or False,
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
