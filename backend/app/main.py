import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import random

from app.db import VEHICLES, SUPPLIERS, REQUESTS, QUOTES, VEHICLE_REMOVALS, CUSTOMERS, SUPPLIER_BIDS
from app.schemas import (
    QuoteCreate, QuoteResponse,
    VehicleCreate, VehicleResponse,
    RequestCreate, RequestResponse,
    SupplierCreate, SupplierResponse, StatusUpdate,
    VehicleRemoval, QuoteUpdate,
    CustomerUpdate, BidCreate,
    BidResponse
)

app = FastAPI(title="FleetCar API", version="1.0.0")

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- HELPERS -----------------
def calculate_quote_price(data: QuoteCreate) -> int:
    # Base monthly price per vehicle in TRY
    base_price = 12000
    
    # Segment multiplier (A, B, C, D, E)
    segment_multipliers = {
        "A": 0.70,
        "B": 0.85,
        "C": 1.0,
        "D": 1.30,
        "E": 1.70
    }
    seg_mult = segment_multipliers.get(data.vehicle_segment, 1.0)
    
    # Type multiplier (Sedan, SUV, Hatchback, Hafif Ticari, Station Wagon)
    type_multipliers = {
        "Sedan": 1.0,
        "SUV": 1.20,
        "Hatchback": 0.95,
        "Hafif Ticari": 1.15,
        "Station Wagon": 1.05
    }
    type_mult = type_multipliers.get(data.vehicle_type, 1.0)
    
    # Duration multiplier (longer contract = discount)
    duration_multipliers = {
        12: 1.0,
        24: 0.90,
        36: 0.82,
        48: 0.75
    }
    dur_mult = duration_multipliers.get(data.duration_months, 0.90)
    
    # Mileage multiplier (more km = higher price)
    mileage_multipliers = {
        10000: 0.95,
        20000: 1.0,
        30000: 1.12,
        40000: 1.25,
        50000: 1.40
    }
    km_mult = mileage_multipliers.get(data.estimated_annual_mileage, 1.0)
    
    # Calculate price
    price_per_vehicle = base_price * seg_mult * type_mult * dur_mult * km_mult
    total_monthly = price_per_vehicle * data.vehicle_count
    
    return int(total_monthly)

# ----------------- LANDING & QUOTES -----------------
@app.get("/api/quotes", response_model=List[QuoteResponse])
def get_quotes():
    return QUOTES

@app.post("/api/quotes", response_model=QuoteResponse)
def create_quote(quote: QuoteCreate):
    price = calculate_quote_price(quote)
    new_quote = {
        "id": len(QUOTES) + 1,
        "company_name": quote.company_name,
        "email": quote.email,
        "phone": quote.phone,
        "vehicle_count": quote.vehicle_count,
        "duration_months": quote.duration_months,
        "vehicle_segment": quote.vehicle_segment,
        "vehicle_type": quote.vehicle_type,
        "estimated_annual_mileage": quote.estimated_annual_mileage,
        "monthly_price_try": price,
        "status": "Teklif Verildi",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    QUOTES.append(new_quote)
    return new_quote

@app.put("/api/quotes/{quote_id}/status")
def update_quote_status(quote_id: int, status_update: StatusUpdate):
    quote = next((q for q in QUOTES if q["id"] == quote_id), None)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
        
    quote["status"] = status_update.status
    
    if status_update.status == "Sözleşme İmzalandı":
        amount = status_update.contract_amount or quote["monthly_price_try"]
        quote["contract_amount"] = amount
        
        # Add to CUSTOMERS list
        customer = next((c for c in CUSTOMERS if c["company_name"].lower() == quote["company_name"].lower()), None)
        if not customer:
            new_customer = {
                "id": len(CUSTOMERS) + 1,
                "company_name": quote["company_name"],
                "legal_title": f"{quote['company_name']} Anonim Şirketi" if "holding" in quote["company_name"].lower() or "a.ş." in quote["company_name"].lower() else f"{quote['company_name']} Limited Şirketi",
                "email": quote["email"],
                "phone": quote["phone"],
                "registered_vehicles_count": quote["vehicle_count"],
                "status": "Aktif",
                "address": "Maslak Plazalar, Şişli, İstanbul",
                "contract_amount": amount,
                "signed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            CUSTOMERS.append(new_customer)
        else:
            customer["registered_vehicles_count"] += quote["vehicle_count"]
            customer["contract_amount"] += amount
            
    return quote

@app.put("/api/quotes/{quote_id}", response_model=QuoteResponse)
def update_quote(quote_id: int, updated: QuoteUpdate):
    quote = next((q for q in QUOTES if q["id"] == quote_id), None)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote["company_name"] = updated.company_name
    quote["email"] = updated.email
    quote["phone"] = updated.phone
    quote["vehicle_count"] = updated.vehicle_count
    quote["duration_months"] = updated.duration_months
    quote["vehicle_segment"] = updated.vehicle_segment
    quote["vehicle_type"] = updated.vehicle_type
    quote["estimated_annual_mileage"] = updated.estimated_annual_mileage
    quote["monthly_price_try"] = updated.monthly_price_try
    quote["status"] = updated.status
    return quote

@app.get("/api/quotes/{quote_id}/bids", response_model=List[BidResponse])
def get_quote_bids(quote_id: int):
    return [b for b in SUPPLIER_BIDS if b["quote_id"] == quote_id]

@app.post("/api/quotes/{quote_id}/bids", response_model=BidResponse)
def create_quote_bid(quote_id: int, bid: BidCreate, supplier_id: int):
    quote = next((q for q in QUOTES if q["id"] == quote_id), None)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
        
    supplier = next((s for s in SUPPLIERS if s["id"] == supplier_id), None)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
        
    # Check if a bid already exists by this supplier
    existing = next((b for b in SUPPLIER_BIDS if b["quote_id"] == quote_id and b["supplier_id"] == supplier_id), None)
    if existing:
        existing["monthly_price_try"] = bid.monthly_price_try
        existing["notes"] = bid.notes
        existing["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        existing["status"] = "Beklemede"
        return existing
        
    new_bid = {
        "id": len(SUPPLIER_BIDS) + 1,
        "quote_id": quote_id,
        "supplier_id": supplier_id,
        "supplier_name": supplier["name"],
        "monthly_price_try": bid.monthly_price_try,
        "notes": bid.notes,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "Beklemede"
    }
    SUPPLIER_BIDS.append(new_bid)
    return new_bid

@app.get("/api/suppliers/{supplier_id}/bids", response_model=List[BidResponse])
def get_supplier_bids(supplier_id: int):
    return [b for b in SUPPLIER_BIDS if b["supplier_id"] == supplier_id]

@app.put("/api/bids/{bid_id}/status", response_model=BidResponse)
def update_bid_status(bid_id: int, status_update: StatusUpdate):
    bid = next((b for b in SUPPLIER_BIDS if b["id"] == bid_id), None)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
        
    bid["status"] = status_update.status
    
    if status_update.status == "Kabul Edildi":
        for other in SUPPLIER_BIDS:
            if other["quote_id"] == bid["quote_id"] and other["id"] != bid_id:
                other["status"] = "Reddedildi"
                
        quote = next((q for q in QUOTES if q["id"] == bid["quote_id"]), None)
        if quote:
            quote["monthly_price_try"] = bid["monthly_price_try"]
            
    return bid

# ----------------- VEHICLES -----------------
@app.get("/api/vehicles", response_model=List[VehicleResponse])
def get_vehicles():
    return VEHICLES

@app.post("/api/vehicles", response_model=VehicleResponse)
def create_vehicle(vehicle: VehicleCreate):
    # Check if chassis number already exists
    if any(v["chassis_no"] == vehicle.chassis_no for v in VEHICLES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu şase numarasına sahip bir araç zaten kayıtlı."
        )
        
    new_vehicle = {
        "id": vehicle.chassis_no,
        "chassis_no": vehicle.chassis_no,
        "plate": vehicle.plate.upper(),
        "brand": vehicle.brand,
        "model": vehicle.model,
        "year": vehicle.year,
        "fuel": vehicle.fuel,
        "status": "Aktif",
        "mileage": vehicle.mileage,
        "license_serial_no": vehicle.license_serial_no,
        "inspection_date": vehicle.inspection_date,
        "vehicle_segment": vehicle.vehicle_segment,
        "vehicle_type": vehicle.vehicle_type,
        "tire_change_date": vehicle.tire_change_date,
        "last_service_date": vehicle.last_service_date,
        "last_service_mileage": vehicle.last_service_mileage,
        "is_active": True,
        "removal_reason": None,
        "removed_at": None,
        "supplier_id": vehicle.supplier_id
    }
    VEHICLES.append(new_vehicle)
    return new_vehicle

@app.post("/api/vehicles/{vehicle_id}/remove", response_model=VehicleResponse)
def remove_vehicle(vehicle_id: str, removal: VehicleRemoval):
    vehicle = next((v for v in VEHICLES if v["id"] == vehicle_id), None)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle["is_active"] = False
    vehicle["removal_reason"] = removal.reason
    vehicle["removed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    vehicle["status"] = "Kaldırıldı"
    
    # Save removal log linked by registration/chassis number
    VEHICLE_REMOVALS.append({
        "registry_no": vehicle["chassis_no"],
        "reason": removal.reason,
        "removed_at": vehicle["removed_at"]
    })
    
    return vehicle

@app.post("/api/vehicles/{vehicle_id}/reactivate", response_model=VehicleResponse)
def reactivate_vehicle(vehicle_id: str):
    vehicle = next((v for v in VEHICLES if v["id"] == vehicle_id), None)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle["is_active"] = True
    vehicle["removal_reason"] = None
    vehicle["removed_at"] = None
    vehicle["status"] = "Aktif"
    return vehicle

@app.get("/api/vehicles/removals")
def get_vehicle_removals():
    return VEHICLE_REMOVALS

# ----------------- SUPPLIERS -----------------
@app.get("/api/suppliers", response_model=List[SupplierResponse])
def get_suppliers(type: Optional[str] = None):
    if type:
        return [s for s in SUPPLIERS if s["type"] == type]
    return SUPPLIERS

@app.post("/api/suppliers", response_model=SupplierResponse)
def create_supplier(supplier: SupplierCreate):
    new_supplier = {
        "id": max((s["id"] for s in SUPPLIERS), default=0) + 1,
        "name": supplier.name,
        "type": supplier.type,
        "phone": supplier.phone,
        "location": f"{supplier.district}, {supplier.city}",
        "city": supplier.city,
        "district": supplier.district,
        "services": supplier.services,
        "contract_type": supplier.contract_type
    }
    SUPPLIERS.append(new_supplier)
    return new_supplier

# ----------------- REQUESTS (TEDARİKÇİ TALEPLERİ) -----------------
@app.get("/api/requests")
def get_requests():
    # Enrich request data with vehicle plate and supplier name for UI ease
    enriched_requests = []
    for r in REQUESTS:
        vehicle = next((v for v in VEHICLES if v["id"] == r["vehicle_id"]), None)
        supplier = next((s for s in SUPPLIERS if s["id"] == r["supplier_id"]), None)
        
        enriched_requests.append({
            **r,
            "vehicle_plate": vehicle["plate"] if vehicle else "Bilinmeyen",
            "vehicle_brand_model": f"{vehicle['brand']} {vehicle['model']}" if vehicle else "Bilinmeyen",
            "supplier_name": supplier["name"] if supplier else "Bilinmeyen",
        })
    return enriched_requests

@app.post("/api/requests", response_model=RequestResponse)
def create_request(req: RequestCreate):
    # Verify vehicle exists
    vehicle = next((v for v in VEHICLES if v["id"] == req.vehicle_id), None)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    # Verify supplier exists
    supplier = next((s for s in SUPPLIERS if s["id"] == req.supplier_id), None)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
        
    # Create request
    new_request = {
        "id": len(REQUESTS) + 1,
        "vehicle_id": req.vehicle_id,
        "supplier_id": req.supplier_id,
        "type": req.type,
        "status": "Beklemede",
        "description": req.description,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "details": req.details
    }
    REQUESTS.append(new_request)
    
    # Automatically update vehicle status based on type
    status_map = {
        "servis": "Serviste",
        "lastik": "Lastik Değişiminde",
        "yol_yardim": "Yol Yardımında",
        "ikame_arac": "İkame Araç Bekliyor"
    }
    vehicle["status"] = status_map.get(req.type, "Aktif")
    
    return new_request

@app.put("/api/requests/{request_id}/status")
def update_request_status(request_id: int, status_update: StatusUpdate):
    req = next((r for r in REQUESTS if r["id"] == request_id), None)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    req["status"] = status_update.status
    
    # If the request status is updated to completed ("Tamamlandı") or cancelled ("İptal Edildi"), 
    # check if the vehicle has other active requests, else revert vehicle status to "Aktif"
    if status_update.status in ["Tamamlandı", "İptal Edildi"]:
        vehicle = next((v for v in VEHICLES if v["id"] == req["vehicle_id"]), None)
        if vehicle:
            # Check if there are other pending or active requests for this vehicle
            other_active = [r for r in REQUESTS if r["vehicle_id"] == vehicle["id"] and r["id"] != request_id and r["status"] not in ["Tamamlandı", "İptal Edildi"]]
            if not other_active:
                vehicle["status"] = "Aktif"
            else:
                # Set to the type of the remaining active request
                status_map = {
                    "servis": "Serviste",
                    "lastik": "Lastik Değişiminde",
                    "yol_yardim": "Yol Yardımında",
                    "ikame_arac": "İkame Araç Bekliyor"
                }
                vehicle["status"] = status_map.get(other_active[0]["type"], "Aktif")
                
    return req

# ----------------- DASHBOARD STATS -----------------
@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    active_vehicles_list = [v for v in VEHICLES if v.get("is_active", True)]
    total_vehicles = len(active_vehicles_list)
    active_vehicles = len([v for v in active_vehicles_list if v["status"] == "Aktif"])
    in_service = len([v for v in active_vehicles_list if v["status"] == "Serviste"])
    tire_change = len([v for v in active_vehicles_list if v["status"] == "Lastik Değişiminde"])
    roadside_assistance = len([v for v in active_vehicles_list if v["status"] == "Yol Yardımında"])
    replacement_waiting = len([v for v in active_vehicles_list if v["status"] == "İkame Araç Bekliyor"])
    
    total_requests = len(REQUESTS)
    pending_requests = len([r for r in REQUESTS if r["status"] in ["Beklemede", "Onaylandı"]])
    completed_requests = len([r for r in REQUESTS if r["status"] == "Tamamlandı"])
    
    # Calculate vehicle mileage statistics
    avg_mileage = int(sum(v["mileage"] for v in active_vehicles_list) / total_vehicles) if total_vehicles > 0 else 0
    
    # Fuel breakdown
    fuel_stats = {}
    for v in active_vehicles_list:
        fuel_stats[v["fuel"]] = fuel_stats.get(v["fuel"], 0) + 1
        
    return {
        "total_vehicles": total_vehicles,
        "active_vehicles": active_vehicles,
        "in_service": in_service,
        "tire_change": tire_change,
        "roadside_assistance": roadside_assistance,
        "replacement_waiting": replacement_waiting,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "completed_requests": completed_requests,
        "avg_mileage": avg_mileage,
        "fuel_stats": fuel_stats
    }

# ----------------- COMPANY PROFILE -----------------
@app.get("/api/company/profile")
def get_company_profile():
    return {
        "company_name": "Tekno Holding",
        "legal_title": "Tekno Holding Anonim Şirketi",
        "registered_vehicles_count": len([v for v in VEHICLES if v.get("is_active", True)]),
        "email": "info@teknoholding.com",
        "phone": "+90 212 999 8877",
        "address": "Maslak Plazalar No: 18, Kat: 14, Şişli, İstanbul"
    }

@app.get("/api/admin/customers")
def get_admin_customers():
    result = []
    for c in CUSTOMERS:
        actual = len([v for v in VEHICLES if v.get("customer_id") == c["id"] and v.get("is_active", True)])
        deficit = max(0, c["registered_vehicles_count"] - actual)
        result.append({
            **c,
            "actual_vehicle_count": actual,
            "vehicle_deficit": deficit
        })
    return result

@app.put("/api/admin/customers/{customer_id}")
def update_admin_customer(customer_id: int, updated: CustomerUpdate):
    customer = next((c for c in CUSTOMERS if c["id"] == customer_id), None)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer["company_name"] = updated.company_name
    customer["legal_title"] = updated.legal_title
    customer["email"] = updated.email
    customer["phone"] = updated.phone
    customer["address"] = updated.address
    customer["registered_vehicles_count"] = updated.registered_vehicles_count
    customer["contract_amount"] = updated.contract_amount
    return customer

# ----------------- ADMIN CUSTOMER DETAIL ENDPOINTS -----------------

@app.get('/api/admin/customers/{customer_id}/vehicles')
def get_customer_vehicles(customer_id: int):
    """Return vehicles belonging to a specific customer."""
    return [v for v in VEHICLES if v.get("customer_id") == customer_id]

@app.get('/api/admin/customers/{customer_id}/services')
def get_customer_services(customer_id: int):
    """Return service request history for a given customer based on their vehicles. Placeholder returns all enriched requests."""
    enriched_requests = []
    for r in REQUESTS:
        vehicle = next((v for v in VEHICLES if v["id"] == r["vehicle_id"]), None)
        supplier = next((s for s in SUPPLIERS if s["id"] == r["supplier_id"]), None)
        enriched_requests.append({
            **r,
            "vehicle_plate": vehicle["plate"] if vehicle else "Bilinmeyen",
            "vehicle_brand_model": f"{vehicle['brand']} {vehicle['model']}" if vehicle else "Bilinmeyen",
            "supplier_name": supplier["name"] if supplier else "Bilinmeyen",
        })
    return enriched_requests
