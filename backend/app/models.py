from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, JSON, Text
)
from .database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id                  = Column(Integer, primary_key=True, index=True)
    email               = Column(String, unique=True, index=True, nullable=False)
    password_hash       = Column(String, nullable=False)
    created_at          = Column(String)
    reset_token         = Column(String, nullable=True)
    reset_token_expires = Column(String, nullable=True)


class Supplier(Base):
    __tablename__ = "suppliers"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String, nullable=False)
    type                = Column(String, nullable=False)          # servis / lastik / yol_yardim / ikame_arac
    email               = Column(String, unique=True, index=True, nullable=True)
    phone               = Column(String)
    location            = Column(String)                           # "İlçe, İl" computed
    city                = Column(String)
    district            = Column(String)
    services            = Column(JSON, default=list)               # ["Periyodik Bakım", ...]
    contract_type       = Column(String)                           # Yetkili / Anlaşmalı
    password_hash       = Column(String, nullable=True)
    invitation_token    = Column(String, nullable=True)
    invitation_status   = Column(String, default="Davet Edilmedi") # Davet Edilmedi / Davet Gönderildi / Aktif
    is_email_verified   = Column(Boolean, default=False)
    verification_token  = Column(String, nullable=True)
    reset_token         = Column(String, nullable=True)
    reset_token_expires = Column(String, nullable=True)


class Customer(Base):
    __tablename__ = "customers"

    id                        = Column(Integer, primary_key=True, index=True)
    company_name              = Column(String, nullable=False)
    legal_title               = Column(String)
    email                     = Column(String)
    phone                     = Column(String)
    registered_vehicles_count = Column(Integer, default=0)   # Sözleşmedeki araç sayısı
    status                    = Column(String, default="Aktif")
    address                   = Column(String)
    contract_amount           = Column(Float)
    signed_at                 = Column(String)
    password_hash             = Column(String, nullable=True)
    invitation_token          = Column(String, nullable=True)
    invitation_status         = Column(String, default="Davet Edilmedi") # Davet Edilmedi / Davet Gönderildi / Aktif
    documents_uploaded        = Column(Boolean, default=False)
    documents                 = Column(JSON, default=dict) # {"tax_plate": "...", "signature_circular": "...", "activity_certificate": "..."}
    is_email_verified         = Column(Boolean, default=False)
    verification_token        = Column(String, nullable=True)
    reset_token               = Column(String, nullable=True)
    reset_token_expires       = Column(String, nullable=True)



class Vehicle(Base):
    __tablename__ = "vehicles"

    id                   = Column(String, primary_key=True, index=True)  # chassis_no as PK
    chassis_no           = Column(String, nullable=False, unique=True)
    plate                = Column(String, nullable=False)
    brand                = Column(String)
    model                = Column(String)
    year                 = Column(Integer)
    fuel                 = Column(String)
    color                = Column(String, nullable=True)
    contract_start_date  = Column(String, nullable=True)
    contract_end_date    = Column(String, nullable=True)
    monthly_rent         = Column(Float, nullable=True)
    monthly_km_limit     = Column(Integer, nullable=True)
    version              = Column(String, nullable=True)
    engine_no            = Column(String, nullable=True)
    horsepower           = Column(Integer, nullable=True)
    cylinder_count       = Column(Integer, nullable=True)
    transmission         = Column(String, nullable=True)
    seat_count           = Column(Integer, nullable=True)
    trunk_volume_l       = Column(Integer, nullable=True)
    tire_size            = Column(String, nullable=True)
    registration_date    = Column(String, nullable=True)
    traffic_insurance_policy_no = Column(String, nullable=True)
    traffic_insurance_expiry_date = Column(String, nullable=True)
    casco_policy_no      = Column(String, nullable=True)
    casco_insurance_expiry_date = Column(String, nullable=True)
    hgs_no               = Column(String, nullable=True)
    hgs_balance          = Column(Float, nullable=True)
    hgs_last_reload_date = Column(String, nullable=True)
    hgs_active           = Column(Boolean, default=False)
    delivery_date        = Column(String, nullable=True)
    delivered_by         = Column(String, nullable=True)
    received_by          = Column(String, nullable=True)
    delivery_location    = Column(String, nullable=True)
    delivery_notes       = Column(Text, nullable=True)
    contract_no          = Column(String, nullable=True)
    contract_duration_months = Column(Integer, nullable=True)
    contract_committed_km = Column(Integer, nullable=True)
    contract_signed_at   = Column(String, nullable=True)
    erp_id               = Column(String, nullable=True)
    assignment_user      = Column(String, nullable=True)
    operating_company    = Column(String, nullable=True)
    vehicle_group        = Column(String, nullable=True)
    current_month_km     = Column(Integer, nullable=True)
    next_service_due_date = Column(String, nullable=True)
    next_service_due_km  = Column(Integer, nullable=True)
    gps_latitude         = Column(Float, nullable=True)
    gps_longitude        = Column(Float, nullable=True)
    gps_location_label   = Column(String, nullable=True)
    gps_last_seen_at     = Column(String, nullable=True)
    status               = Column(String, default="Aktif")
    mileage              = Column(Integer, default=0)
    license_serial_no    = Column(String)
    inspection_date      = Column(String)
    vehicle_segment      = Column(String)
    vehicle_type         = Column(String)
    tire_change_date     = Column(String)
    last_service_date    = Column(String)
    last_service_mileage = Column(Integer, default=0)
    is_active            = Column(Boolean, default=True)
    removal_reason       = Column(String, nullable=True)
    removed_at           = Column(String, nullable=True)
    supplier_id          = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    customer_id          = Column(Integer, ForeignKey("customers.id"), nullable=True)
    gps_device_id        = Column(String, nullable=True)
    utts_code            = Column(String, nullable=True)


class Quote(Base):
    __tablename__ = "quotes"

    id                       = Column(Integer, primary_key=True, index=True)
    customer_id              = Column(Integer, ForeignKey("customers.id"), nullable=True)
    company_name             = Column(String)
    email                    = Column(String)
    phone                    = Column(String)
    vehicle_count            = Column(Integer)
    duration_months          = Column(Integer)
    vehicle_segment          = Column(String)
    vehicle_type             = Column(String)
    estimated_annual_mileage = Column(Integer)
    monthly_price_try        = Column(Integer)
    status                   = Column(String, default="Teklif Verildi")
    contract_amount          = Column(Float, nullable=True)
    created_at               = Column(String)
    items                    = Column(JSON, default=list, nullable=True)
    details                  = Column(JSON, default=dict, nullable=True)


class Request(Base):
    __tablename__ = "requests"

    id          = Column(Integer, primary_key=True, index=True)
    vehicle_id  = Column(String, ForeignKey("vehicles.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    type        = Column(String)                              # servis / lastik / yol_yardim / ikame_arac
    status      = Column(String, default="Beklemede")
    description = Column(Text)
    created_at  = Column(String)
    completed_at = Column(String, nullable=True)
    details     = Column(JSON, default=dict)


class SupplierBid(Base):
    __tablename__ = "supplier_bids"

    id                = Column(Integer, primary_key=True, index=True)
    quote_id          = Column(Integer, ForeignKey("quotes.id"))
    supplier_id       = Column(Integer, ForeignKey("suppliers.id"))
    supplier_name     = Column(String)                        # denormalized for query speed
    monthly_price_try = Column(Integer)
    notes             = Column(Text)
    created_at        = Column(String)
    status            = Column(String, default="Beklemede")


class VehicleRemoval(Base):
    __tablename__ = "vehicle_removals"

    id          = Column(Integer, primary_key=True, index=True)
    registry_no = Column(String)
    reason      = Column(Text)
    removed_at  = Column(String)


class VehicleExpense(Base):
    __tablename__ = "vehicle_expenses"

    id         = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False)
    kind       = Column(String, nullable=False)
    amount     = Column(Float, nullable=False)
    date       = Column(String, nullable=False)
    liters     = Column(Float, nullable=True)
    mileage    = Column(Integer, nullable=False)
    note       = Column(Text, nullable=True)


class VehicleFile(Base):
    __tablename__ = "vehicle_files"

    id            = Column(Integer, primary_key=True, index=True)
    vehicle_id    = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    category      = Column(String, nullable=False)  # photo / document
    document_type = Column(String, nullable=True)
    original_name = Column(String, nullable=False)
    stored_name   = Column(String, nullable=False, unique=True)
    content_type  = Column(String, nullable=False)
    file_size     = Column(Integer, nullable=False)
    uploaded_at   = Column(String, nullable=False)
    expiry_date   = Column(String, nullable=True)


class HgsTransaction(Base):
    __tablename__ = "hgs_transactions"

    id          = Column(Integer, primary_key=True, index=True)
    vehicle_id  = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    type        = Column(String, nullable=False)
    amount      = Column(Float, nullable=False)
    date        = Column(String, nullable=False)
    description = Column(String, nullable=True)
    balance     = Column(Float, nullable=False)


class VehicleLocation(Base):
    __tablename__ = "vehicle_locations"

    id          = Column(Integer, primary_key=True, index=True)
    vehicle_id  = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    latitude    = Column(Float, nullable=False)
    longitude   = Column(Float, nullable=False)
    label       = Column(String, nullable=True)
    source      = Column(String, nullable=False, default="manual")
    recorded_at = Column(String, nullable=False)


class TireRecord(Base):
    __tablename__ = "tire_records"

    id              = Column(Integer, primary_key=True, index=True)
    vehicle_id      = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    brand           = Column(String, nullable=False)
    size            = Column(String, nullable=False)
    set_no          = Column(String, nullable=True)
    season          = Column(String, nullable=False, default="Dört Mevsim")
    production_date = Column(String, nullable=True)
    installed_at    = Column(String, nullable=True)
    changed_at      = Column(String, nullable=True)
    inspected_at    = Column(String, nullable=True)
    tread_depth_mm  = Column(Float, nullable=True)
    status          = Column(String, nullable=False, default="İyi")
    remaining_km    = Column(Integer, nullable=True)
    position        = Column(String, nullable=True)
    notes           = Column(Text, nullable=True)
    created_at      = Column(String, nullable=False)
    updated_at      = Column(String, nullable=False)


class TireOperation(Base):
    __tablename__ = "tire_operations"

    id          = Column(Integer, primary_key=True, index=True)
    vehicle_id  = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    tire_id     = Column(Integer, ForeignKey("tire_records.id"), nullable=True)
    type        = Column(String, nullable=False)
    date        = Column(String, nullable=False)
    mileage     = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    status      = Column(String, nullable=False, default="Tamamlandı")


class RoadsideCase(Base):
    __tablename__ = "roadside_cases"

    id           = Column(Integer, primary_key=True, index=True)
    request_id   = Column(Integer, ForeignKey("requests.id"), nullable=True, unique=True, index=True)
    vehicle_id   = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    case_no      = Column(String, nullable=False, unique=True, index=True)
    incident     = Column(String, nullable=False)
    location     = Column(String, nullable=True)
    latitude     = Column(Float, nullable=True)
    longitude    = Column(Float, nullable=True)
    description  = Column(Text, nullable=True)
    status       = Column(String, nullable=False, default="Beklemede")
    progress     = Column(Integer, nullable=False, default=0)
    team_name    = Column(String, nullable=True)
    team_phone   = Column(String, nullable=True)
    dispatched_at = Column(String, nullable=True)
    eta_minutes  = Column(Integer, nullable=True)
    distance_km  = Column(Float, nullable=True)
    arrived_at   = Column(String, nullable=True)
    resolved_at  = Column(String, nullable=True)
    response_minutes = Column(Integer, nullable=True)
    photos       = Column(JSON, default=list, nullable=True)
    created_at   = Column(String, nullable=False)
    updated_at   = Column(String, nullable=False)


class RoadsideEvent(Base):
    __tablename__ = "roadside_events"

    id          = Column(Integer, primary_key=True, index=True)
    case_id     = Column(Integer, ForeignKey("roadside_cases.id"), nullable=False, index=True)
    status      = Column(String, nullable=False)
    title       = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    eta_minutes = Column(Integer, nullable=True)
    distance_km = Column(Float, nullable=True)
    created_at  = Column(String, nullable=False)


class CustomerSetting(Base):
    __tablename__ = "customer_settings"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False, default=dict)


class CustomerPortalUser(Base):
    __tablename__ = "customer_portal_users"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(String, nullable=False, default="Sürücü")
    assigned_plate = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(String, nullable=False)


class DeliveryForm(Base):
    __tablename__ = "delivery_forms"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False)
    receiver = Column(String, nullable=False)
    issuer = Column(String, nullable=True)
    date = Column(String, nullable=False)
    mileage = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)


class VehicleUsageRecord(Base):
    __tablename__ = "vehicle_usage_records"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    started_at = Column(String, nullable=False)
    ended_at = Column(String, nullable=False)
    source = Column(String, nullable=False, default="manual")


class VehicleMileageRecord(Base):
    __tablename__ = "vehicle_mileage_records"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    mileage = Column(Integer, nullable=False)
    recorded_at = Column(String, nullable=False)
    source = Column(String, nullable=False, default="manual")
