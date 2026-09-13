from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List

class QuoteItemCreate(BaseModel):
    vehicle_segment: str
    vehicle_type: str
    vehicle_count: int
    duration_months: int
    estimated_annual_mileage: int
    monthly_price_try: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

class QuoteCreate(BaseModel):
    company_name: str
    email: str
    phone: str
    vehicle_count: Optional[int] = 1
    duration_months: Optional[int] = 12
    vehicle_segment: Optional[str] = "C"
    vehicle_type: Optional[str] = "Sedan"
    estimated_annual_mileage: Optional[int] = 20000
    items: Optional[List[QuoteItemCreate]] = None
    details: Optional[Dict[str, Any]] = None

class QuoteResponse(BaseModel):
    id: int
    customer_id: Optional[int] = None
    customer_info: Optional[Dict[str, Any]] = None
    company_name: str
    email: str
    phone: str
    vehicle_count: int
    duration_months: Optional[int] = None
    vehicle_segment: Optional[str] = None
    vehicle_type: Optional[str] = None
    estimated_annual_mileage: Optional[int] = None
    monthly_price_try: Optional[int] = None
    status: str
    created_at: str
    contract_amount: Optional[float] = None
    items: Optional[List[Dict[str, Any]]] = None
    bids: Optional[List[Dict[str, Any]]] = None
    details: Optional[Dict[str, Any]] = None

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
    customer_id: Optional[int] = None
    gps_device_id: Optional[str] = None
    utts_code: Optional[str] = None

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
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    supplier_name: Optional[str] = None
    removed_at: Optional[str] = None
    gps_device_id: Optional[str] = None
    utts_code: Optional[str] = None

class VehicleRemoval(BaseModel):
    reason: str

class VehicleUpdate(BaseModel):
    plate: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    fuel: Optional[str] = None
    mileage: Optional[int] = None
    chassis_no: Optional[str] = None
    license_serial_no: Optional[str] = None
    inspection_date: Optional[str] = None
    vehicle_segment: Optional[str] = None
    vehicle_type: Optional[str] = None
    tire_change_date: Optional[str] = None
    last_service_date: Optional[str] = None
    last_service_mileage: Optional[int] = None
    gps_device_id: Optional[str] = None
    utts_code: Optional[str] = None

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

class SupplierCreate(BaseModel):
    name: str
    type: str
    phone: str
    city: str
    district: str
    services: List[str]
    contract_type: str
    email: Optional[str] = None
    send_invite: Optional[bool] = False

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
    email: Optional[str] = None
    invitation_status: Optional[str] = "Davet Edilmedi"

class SetPasswordRequest(BaseModel):
    token: str
    password: str

class StatusUpdate(BaseModel):
    status: str
    contract_amount: Optional[float] = None

class CustomerCreate(BaseModel):
    company_name: str
    legal_title: str
    email: str
    phone: str
    address: str
    registered_vehicles_count: int
    contract_amount: float
    send_invite: Optional[bool] = False

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

class AdminLoginRequest(BaseModel):
    email: str
    password: str

class ServiceCheckIn(BaseModel):
    entry_mileage: int
    fuel_level: str
    driver_name: str
    driver_phone: Optional[str] = None
    entry_notes: Optional[str] = None

class ServiceWorkOrder(BaseModel):
    diagnosis_notes: Optional[str] = None
    parts_list: Optional[List[Dict[str, Any]]] = None
    labor_cost: Optional[float] = None
    total_estimated_cost: Optional[float] = None

class ServiceInvoice(BaseModel):
    invoice_no: str
    invoice_date: str
    invoice_amount: float
    invoice_notes: Optional[str] = None
    file_name: Optional[str] = None


class CustomerRegisterRequest(BaseModel):
    email: str
    password: str
    company_name: Optional[str] = None
    phone: Optional[str] = None


class CustomerDocumentUpload(BaseModel):
    customer_id: Optional[int] = None
    tax_plate: Optional[str] = None
    signature_circular: Optional[str] = None
    activity_certificate: Optional[str] = None
    trade_registry: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class ResendVerificationRequest(BaseModel):
    email: str


