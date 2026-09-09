import datetime
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import models
from app.auth import verify_password, hash_password
from app.email_utils import generate_invitation_token, send_supplier_invitation_email, APP_BASE_URL
from app.init_db import create_tables, seed
from app.schemas import (
    QuoteCreate, QuoteResponse,
    VehicleCreate, VehicleResponse,
    RequestCreate, RequestResponse,
    SupplierCreate, SupplierResponse, StatusUpdate,
    VehicleRemoval, QuoteUpdate,
    CustomerCreate, CustomerUpdate, BidCreate, BidResponse,
    AdminLoginRequest, SetPasswordRequest
)

app = FastAPI(title="FleetCar API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()
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
        "has_password": bool(getattr(s, 'password_hash', None))
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
        "supplier_id": v.supplier_id, "customer_id": v.customer_id
    }
    if db:
        if v.customer_id:
            c = db.query(models.Customer).filter(models.Customer.id == v.customer_id).first()
            if c: d["customer_name"] = c.company_name
        if v.supplier_id:
            s = db.query(models.Supplier).filter(models.Supplier.id == v.supplier_id).first()
            if s: d["supplier_name"] = s.name
    return d


def quote_dict(q: models.Quote) -> dict:
    return {
        "id": q.id, "company_name": q.company_name,
        "email": q.email, "phone": q.phone,
        "vehicle_count": q.vehicle_count, "duration_months": q.duration_months,
        "vehicle_segment": q.vehicle_segment, "vehicle_type": q.vehicle_type,
        "estimated_annual_mileage": q.estimated_annual_mileage,
        "monthly_price_try": q.monthly_price_try, "status": q.status,
        "created_at": q.created_at, "contract_amount": q.contract_amount
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
        "has_password": bool(getattr(c, 'password_hash', None))
    }
    if actual is not None:
        d["actual_vehicle_count"] = actual
        d["vehicle_deficit"] = deficit
    return d


# ─────────────────── QUOTES ────────────────────────────────────────────────

@app.get("/api/quotes", response_model=List[QuoteResponse])
def get_quotes(db: Session = Depends(get_db)):
    return [quote_dict(q) for q in db.query(models.Quote).all()]


@app.post("/api/quotes", response_model=QuoteResponse)
def create_quote(quote: QuoteCreate, db: Session = Depends(get_db)):
    q = models.Quote(
        company_name=quote.company_name, email=quote.email, phone=quote.phone,
        vehicle_count=quote.vehicle_count, duration_months=quote.duration_months,
        vehicle_segment=quote.vehicle_segment, vehicle_type=quote.vehicle_type,
        estimated_annual_mileage=quote.estimated_annual_mileage,
        monthly_price_try=calculate_quote_price(quote),
        status="Teklif Verildi", created_at=now_str()
    )
    db.add(q); db.commit(); db.refresh(q)
    return quote_dict(q)


@app.put("/api/quotes/{quote_id}/status")
def update_quote_status(quote_id: int, status_update: StatusUpdate, db: Session = Depends(get_db)):
    q = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Quote not found")

    q.status = status_update.status

    if status_update.status == "Sözleşme İmzalandı":
        amount = status_update.contract_amount or q.monthly_price_try
        q.contract_amount = amount

        existing = db.query(models.Customer).filter(
            models.Customer.company_name.ilike(q.company_name)
        ).first()

        if not existing:
            legal = (f"{q.company_name} Anonim Şirketi"
                     if any(w in q.company_name.lower() for w in ["holding", "a.ş."])
                     else f"{q.company_name} Limited Şirketi")
            c = models.Customer(
                company_name=q.company_name, legal_title=legal,
                email=q.email, phone=q.phone,
                registered_vehicles_count=q.vehicle_count,
                status="Aktif",
                address="Maslak Plazalar, Şişli, İstanbul",
                contract_amount=amount, signed_at=now_str()
            )
            db.add(c)
        else:
            existing.registered_vehicles_count += q.vehicle_count
            existing.contract_amount = (existing.contract_amount or 0) + amount

    db.commit()
    return quote_dict(q)


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

    b.status = status_update.status

    if status_update.status == "Kabul Edildi":
        db.query(models.SupplierBid).filter(
            models.SupplierBid.quote_id == b.quote_id,
            models.SupplierBid.id != bid_id
        ).update({"status": "Reddedildi"})
        q = db.query(models.Quote).filter(models.Quote.id == b.quote_id).first()
        if q: q.monthly_price_try = b.monthly_price_try

    db.commit(); db.refresh(b)
    return bid_dict(b)


# ─────────────────── VEHICLES ──────────────────────────────────────────────

@app.get("/api/vehicles", response_model=List[VehicleResponse])
def get_vehicles(db: Session = Depends(get_db)):
    return [vehicle_dict(v, db) for v in db.query(models.Vehicle).all()]


@app.post("/api/vehicles", response_model=VehicleResponse)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    if db.query(models.Vehicle).filter(models.Vehicle.chassis_no == vehicle.chassis_no).first():
        raise HTTPException(status_code=400, detail="Bu şase numarasına sahip bir araç zaten kayıtlı.")

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
        customer_id=vehicle.customer_id
    )
    db.add(v); db.commit(); db.refresh(v)
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
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    is_configured = bool(smtp_host and smtp_user)
    return {
        "configured": is_configured,
        "smtp_host": smtp_host or "Tanımlanmamış",
        "smtp_user": smtp_user or "Tanımlanmamış"
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

    return {
        "status": "success",
        "token": f"customer_token_{c.id}_{datetime.datetime.now().timestamp()}",
        "customer": customer_dict(c)
    }


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


# ─────────────────── DASHBOARD ─────────────────────────────────────────────

@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    active = db.query(models.Vehicle).filter(models.Vehicle.is_active == True).all()
    total = len(active)
    fuel_stats = {}
    for v in active:
        fuel_stats[v.fuel] = fuel_stats.get(v.fuel, 0) + 1

    reqs = db.query(models.Request).all()
    return {
        "total_vehicles":       total,
        "active_vehicles":      sum(1 for v in active if v.status == "Aktif"),
        "in_service":           sum(1 for v in active if v.status == "Serviste"),
        "tire_change":          sum(1 for v in active if v.status == "Lastik Değişiminde"),
        "roadside_assistance":  sum(1 for v in active if v.status == "Yol Yardımında"),
        "replacement_waiting":  sum(1 for v in active if v.status == "İkame Araç Bekliyor"),
        "total_requests":       len(reqs),
        "pending_requests":     sum(1 for r in reqs if r.status in ["Beklemede", "Onaylandı"]),
        "completed_requests":   sum(1 for r in reqs if r.status == "Tamamlandı"),
        "avg_mileage":          int(sum(v.mileage for v in active) / total) if total else 0,
        "fuel_stats":           fuel_stats
    }


# ─────────────────── COMPANY PROFILE ───────────────────────────────────────

@app.get("/api/company/profile")
def get_company_profile(db: Session = Depends(get_db)):
    c = db.query(models.Customer).first()
    active_count = db.query(models.Vehicle).filter(models.Vehicle.is_active == True).count()
    if c:
        return {
            "company_name": c.company_name, "legal_title": c.legal_title,
            "registered_vehicles_count": active_count,
            "email": c.email, "phone": c.phone, "address": c.address
        }
    return {"company_name": "FleetCar", "registered_vehicles_count": active_count}


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
