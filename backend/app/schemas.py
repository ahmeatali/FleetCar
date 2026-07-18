from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List

class QuoteCreate(BaseModel):
    company_name: str
    email: str
    phone: str
    vehicle_count: int
    duration_months: int
    vehicle_segment: str
    vehicle_type: str
    estimated_annual_mileage: int

class QuoteResponse(BaseModel):
    id: int
    company_name: str
    email: str
    phone: str
    vehicle_count: int
    duration_months: int
    vehicle_segment: str
    vehicle_type: str
    estimated_annual_mileage: int
    monthly_price_try: int
    status: str
    created_at: str
    contract_amount: Optional[float] = None

class QuoteUpdate(BaseModel):
    company_name: str
    email: str
    phone: str
    vehicle_count: int
    duration_months: int
    vehicle_segment: str
    vehicle_type: str
    estimated_annual_mileage: int
    monthly_price_try: int
    status: str

class VehicleCreate(BaseModel):
    plate: str
    brand: str
    model: str
    year: int
    fuel: str
    mileage: int
    chassis_no: str
    license_serial_no: str
    inspection_date: str
    vehicle_segment: str
    vehicle_type: str
    tire_change_date: str
    last_service_date: str
    last_service_mileage: int
    supplier_id: Optional[int] = None

class VehicleResponse(BaseModel):
    id: str
    plate: str
    brand: str
    model: str
    year: int
    fuel: str
    status: str
    mileage: int
    chassis_no: str
    license_serial_no: str
    inspection_date: str
    vehicle_segment: str
    vehicle_type: str
    tire_change_date: str
    last_service_date: str
    last_service_mileage: int
    is_active: bool
    removal_reason: Optional[str] = None
    supplier_id: Optional[int] = None
    removed_at: Optional[str] = None

class VehicleRemoval(BaseModel):
    reason: str

class RequestCreate(BaseModel):
    vehicle_id: str
    supplier_id: int
    type: str
    description: str
    details: Dict[str, Any]

class RequestResponse(BaseModel):
    id: int
    vehicle_id: str
    supplier_id: int
    type: str
    status: str
    description: str
    created_at: str
    details: Dict[str, Any]

class SupplierResponse(BaseModel):
    id: int
    name: str
    type: str
    phone: str
    location: str
    city: str
    district: str
    services: List[str]
    contract_type: str

class StatusUpdate(BaseModel):
    status: str
    contract_amount: Optional[float] = None

class CustomerUpdate(BaseModel):
    company_name: str
    legal_title: str
    email: str
    phone: str
    address: str
    registered_vehicles_count: int
    contract_amount: float

class BidCreate(BaseModel):
    monthly_price_try: int
    notes: str

class BidResponse(BaseModel):
    id: int
    quote_id: int
    supplier_id: int
    supplier_name: str
    monthly_price_try: int
    notes: str
    created_at: str
    status: str
