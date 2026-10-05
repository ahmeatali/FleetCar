import re
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, List, Literal

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
    color: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    monthly_rent: Optional[float] = None
    monthly_km_limit: Optional[int] = None
    version: Optional[str] = None
    engine_no: Optional[str] = None
    horsepower: Optional[int] = None
    cylinder_count: Optional[int] = None
    transmission: Optional[str] = None
    seat_count: Optional[int] = None
    trunk_volume_l: Optional[int] = None
    tire_size: Optional[str] = None
    registration_date: Optional[str] = None
    traffic_insurance_policy_no: Optional[str] = None
    traffic_insurance_expiry_date: Optional[str] = None
    casco_policy_no: Optional[str] = None
    casco_insurance_expiry_date: Optional[str] = None
    hgs_no: Optional[str] = None
    hgs_balance: Optional[float] = None
    hgs_last_reload_date: Optional[str] = None
    hgs_active: Optional[bool] = None
    delivery_date: Optional[str] = None
    delivered_by: Optional[str] = None
    received_by: Optional[str] = None
    delivery_location: Optional[str] = None
    delivery_notes: Optional[str] = None
    contract_no: Optional[str] = None
    contract_duration_months: Optional[int] = None
    contract_committed_km: Optional[int] = None
    contract_signed_at: Optional[str] = None
    erp_id: Optional[str] = None
    assignment_user: Optional[str] = None
    operating_company: Optional[str] = None
    vehicle_group: Optional[str] = None
    current_month_km: Optional[int] = None
    next_service_due_date: Optional[str] = None
    next_service_due_km: Optional[int] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_location_label: Optional[str] = None
    gps_last_seen_at: Optional[str] = None
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
    color: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    monthly_rent: Optional[float] = None
    monthly_km_limit: Optional[int] = None
    version: Optional[str] = None
    engine_no: Optional[str] = None
    horsepower: Optional[int] = None
    cylinder_count: Optional[int] = None
    transmission: Optional[str] = None
    seat_count: Optional[int] = None
    trunk_volume_l: Optional[int] = None
    tire_size: Optional[str] = None
    registration_date: Optional[str] = None
    traffic_insurance_policy_no: Optional[str] = None
    traffic_insurance_expiry_date: Optional[str] = None
    casco_policy_no: Optional[str] = None
    casco_insurance_expiry_date: Optional[str] = None
    hgs_no: Optional[str] = None
    hgs_balance: Optional[float] = None
    hgs_last_reload_date: Optional[str] = None
    hgs_active: Optional[bool] = None
    delivery_date: Optional[str] = None
    delivered_by: Optional[str] = None
    received_by: Optional[str] = None
    delivery_location: Optional[str] = None
    delivery_notes: Optional[str] = None
    contract_no: Optional[str] = None
    contract_duration_months: Optional[int] = None
    contract_committed_km: Optional[int] = None
    contract_signed_at: Optional[str] = None
    erp_id: Optional[str] = None
    assignment_user: Optional[str] = None
    operating_company: Optional[str] = None
    vehicle_group: Optional[str] = None
    current_month_km: Optional[int] = None
    next_service_due_date: Optional[str] = None
    next_service_due_km: Optional[int] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_location_label: Optional[str] = None
    gps_last_seen_at: Optional[str] = None
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
    color: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    monthly_rent: Optional[float] = None
    monthly_km_limit: Optional[int] = None
    version: Optional[str] = None
    engine_no: Optional[str] = None
    horsepower: Optional[int] = None
    cylinder_count: Optional[int] = None
    transmission: Optional[str] = None
    seat_count: Optional[int] = None
    trunk_volume_l: Optional[int] = None
    tire_size: Optional[str] = None
    registration_date: Optional[str] = None
    traffic_insurance_policy_no: Optional[str] = None
    traffic_insurance_expiry_date: Optional[str] = None
    casco_policy_no: Optional[str] = None
    casco_insurance_expiry_date: Optional[str] = None
    hgs_no: Optional[str] = None
    hgs_balance: Optional[float] = None
    hgs_last_reload_date: Optional[str] = None
    hgs_active: Optional[bool] = None
    delivery_date: Optional[str] = None
    delivered_by: Optional[str] = None
    received_by: Optional[str] = None
    delivery_location: Optional[str] = None
    delivery_notes: Optional[str] = None
    contract_no: Optional[str] = None
    contract_duration_months: Optional[int] = None
    contract_committed_km: Optional[int] = None
    contract_signed_at: Optional[str] = None
    erp_id: Optional[str] = None
    assignment_user: Optional[str] = None
    operating_company: Optional[str] = None
    vehicle_group: Optional[str] = None
    current_month_km: Optional[int] = None
    next_service_due_date: Optional[str] = None
    next_service_due_km: Optional[int] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_location_label: Optional[str] = None
    gps_last_seen_at: Optional[str] = None
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

class VehicleExpenseCreate(BaseModel):
    vehicle_id: str
    kind: str
    amount: float
    date: str
    liters: Optional[float] = None
    mileage: int
    note: Optional[str] = None

class VehicleExpenseResponse(VehicleExpenseCreate):
    id: int

class HgsTransactionCreate(BaseModel):
    type: str
    amount: float
    date: str
    description: Optional[str] = None

class HgsTransactionResponse(HgsTransactionCreate):
    id: int
    vehicle_id: str
    balance: float

class VehicleLocationCreate(BaseModel):
    latitude: float
    longitude: float
    label: Optional[str] = None

class VehicleLocationResponse(VehicleLocationCreate):
    id: int
    vehicle_id: str
    source: str
    recorded_at: str

class VehicleFileResponse(BaseModel):
    id: int
    vehicle_id: str
    category: str
    document_type: Optional[str] = None
    original_name: str
    content_type: str
    file_size: int
    uploaded_at: str
    expiry_date: Optional[str] = None
    url: str


class TireRecordCreate(BaseModel):
    vehicle_id: str
    brand: str
    size: str
    set_no: Optional[str] = None
    season: str = "Dört Mevsim"
    production_date: Optional[str] = None
    installed_at: Optional[str] = None
    changed_at: Optional[str] = None
    inspected_at: Optional[str] = None
    tread_depth_mm: Optional[float] = None
    status: str = "İyi"
    remaining_km: Optional[int] = None
    position: Optional[str] = None
    notes: Optional[str] = None


class TireRecordUpdate(BaseModel):
    vehicle_id: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    set_no: Optional[str] = None
    season: Optional[str] = None
    production_date: Optional[str] = None
    installed_at: Optional[str] = None
    changed_at: Optional[str] = None
    inspected_at: Optional[str] = None
    tread_depth_mm: Optional[float] = None
    status: Optional[str] = None
    remaining_km: Optional[int] = None
    position: Optional[str] = None
    notes: Optional[str] = None


class TireRecordResponse(TireRecordCreate):
    id: int
    plate: Optional[str] = None
    vehicle_brand: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_mileage: Optional[int] = None
    updated_at: str


class TireOperationCreate(BaseModel):
    vehicle_id: str
    tire_id: Optional[int] = None
    type: str
    date: Optional[str] = None
    mileage: Optional[int] = None
    description: Optional[str] = None
    status: str = "Tamamlandı"


class TireOperationResponse(TireOperationCreate):
    id: int
    plate: Optional[str] = None

class RequestCreate(BaseModel):
    vehicle_id: str
    supplier_id: Optional[int] = None
    type: str
    description: str
    details: Dict[str, Any]

class RequestResponse(BaseModel):
    id: int
    vehicle_id: str
    supplier_id: Optional[int] = None
    type: str
    status: str
    description: str
    created_at: str
    completed_at: Optional[str] = None
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
    team_name: Optional[str] = None
    team_phone: Optional[str] = None
    eta_minutes: Optional[int] = None
    distance_km: Optional[float] = None

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
    service_type: Optional[str] = None
    appointment_date: Optional[str] = None
    work_order_no: Optional[str] = None
    diagnosis_notes: Optional[str] = None
    parts_list: Optional[List[Dict[str, Any]]] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    total_estimated_cost: Optional[float] = None
    notes: Optional[str] = None

class ServiceInvoice(BaseModel):
    invoice_no: str
    invoice_date: str
    invoice_amount: float
    invoice_notes: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None


class EmailRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Geçerli bir e-posta adresi girin.")
        return value


class CustomerRegisterRequest(EmailRequest):
    password: str
    company_name: Optional[str] = None
    phone: Optional[str] = None


class SupplierRegisterRequest(EmailRequest):
    account_type: Literal["service", "supplier"]
    name: str
    password: str
    phone: Optional[str] = None
    service_type: Optional[Literal["servis", "lastik", "yol_yardim"]] = None


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


class ResendVerificationRequest(EmailRequest):
    account_type: Optional[Literal["customer", "customer_user", "service", "supplier"]] = None


class RoadsideCaseCreate(BaseModel):
    vehicle_id: str
    incident: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    photos: Optional[List[str]] = None


class RoadsideCaseUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    team_name: Optional[str] = None
    team_phone: Optional[str] = None
    eta_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    description: Optional[str] = None


class RoadsideEventCreate(BaseModel):
    status: str
    title: str
    description: Optional[str] = None
    eta_minutes: Optional[int] = None
    distance_km: Optional[float] = None


class RoadsideEventResponse(RoadsideEventCreate):
    id: int
    case_id: int
    created_at: str


class RoadsideCaseResponse(RoadsideCaseCreate):
    id: int
    request_id: Optional[int] = None
    case_no: str
    plate: str
    vehicle_brand: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    chassis_no: Optional[str] = None
    engine_no: Optional[str] = None
    color: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    status: str
    progress: int
    team_name: Optional[str] = None
    team_phone: Optional[str] = None
    dispatched_at: Optional[str] = None
    eta_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    arrived_at: Optional[str] = None
    resolved_at: Optional[str] = None
    response_minutes: Optional[int] = None
    photos: Optional[List[str]] = None
    created_at: str
    updated_at: str
