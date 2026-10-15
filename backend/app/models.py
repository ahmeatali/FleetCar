from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
    select,
)
from sqlalchemy import text as sql_text

from .database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(String)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(String, nullable=True)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # servis / lastik / yol_yardim / ikame_arac
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String)
    location = Column(String)  # "İlçe, İl" computed
    city = Column(String)
    district = Column(String)
    services = Column(JSON, default=list)  # ["Periyodik Bakım", ...]
    contract_type = Column(String)  # Yetkili / Anlaşmalı
    password_hash = Column(String, nullable=True)
    invitation_token = Column(String, nullable=True)
    invitation_status = Column(
        String, default="Davet Edilmedi"
    )  # Davet Edilmedi / Davet Gönderildi / Aktif
    is_email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(String, nullable=True)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    legal_title = Column(String)
    email = Column(String)
    phone = Column(String)
    registered_vehicles_count = Column(Integer, default=0)  # Sözleşmedeki araç sayısı
    status = Column(String, default="Aktif")
    address = Column(String)
    contract_amount = Column(Float)
    signed_at = Column(String)
    password_hash = Column(String, nullable=True)
    invitation_token = Column(String, nullable=True)
    invitation_status = Column(
        String, default="Davet Edilmedi"
    )  # Davet Edilmedi / Davet Gönderildi / Aktif
    documents_uploaded = Column(Boolean, default=False)
    documents = Column(
        JSON, default=dict
    )  # {"tax_plate": "...", "signature_circular": "...", "activity_certificate": "..."}
    is_email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(String, nullable=True)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String, primary_key=True, index=True)  # chassis_no as PK
    chassis_no = Column(String, nullable=False, unique=True)
    plate = Column(String, nullable=False)
    brand = Column(String)
    model = Column(String)
    year = Column(Integer)
    fuel = Column(String)
    color = Column(String, nullable=True)
    contract_start_date = Column(String, nullable=True)
    contract_end_date = Column(String, nullable=True)
    monthly_rent = Column(Float, nullable=True)
    monthly_km_limit = Column(Integer, nullable=True)
    version = Column(String, nullable=True)
    engine_no = Column(String, nullable=True)
    horsepower = Column(Integer, nullable=True)
    cylinder_count = Column(Integer, nullable=True)
    transmission = Column(String, nullable=True)
    seat_count = Column(Integer, nullable=True)
    trunk_volume_l = Column(Integer, nullable=True)
    tire_size = Column(String, nullable=True)
    registration_date = Column(String, nullable=True)
    traffic_insurance_policy_no = Column(String, nullable=True)
    traffic_insurance_expiry_date = Column(String, nullable=True)
    casco_policy_no = Column(String, nullable=True)
    casco_insurance_expiry_date = Column(String, nullable=True)
    hgs_no = Column(String, nullable=True)
    hgs_balance = Column(Float, nullable=True)
    hgs_last_reload_date = Column(String, nullable=True)
    hgs_active = Column(Boolean, default=False)
    delivery_date = Column(String, nullable=True)
    delivered_by = Column(String, nullable=True)
    received_by = Column(String, nullable=True)
    delivery_location = Column(String, nullable=True)
    delivery_notes = Column(Text, nullable=True)
    contract_no = Column(String, nullable=True)
    contract_duration_months = Column(Integer, nullable=True)
    contract_committed_km = Column(Integer, nullable=True)
    contract_signed_at = Column(String, nullable=True)
    erp_id = Column(String, nullable=True)
    assignment_user = Column(String, nullable=True)
    operating_company = Column(String, nullable=True)
    vehicle_group = Column(String, nullable=True)
    current_month_km = Column(Integer, nullable=True)
    next_service_due_date = Column(String, nullable=True)
    next_service_due_km = Column(Integer, nullable=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    gps_location_label = Column(String, nullable=True)
    gps_last_seen_at = Column(String, nullable=True)
    status = Column(String, default="Aktif")
    mileage = Column(Integer, default=0)
    license_serial_no = Column(String)
    inspection_date = Column(String)
    vehicle_segment = Column(String)
    vehicle_type = Column(String)
    tire_change_date = Column(String)
    last_service_date = Column(String)
    last_service_mileage = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    removal_reason = Column(String, nullable=True)
    removed_at = Column(String, nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    gps_device_id = Column(String, nullable=True)
    utts_code = Column(String, nullable=True)


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    company_name = Column(String)
    email = Column(String)
    phone = Column(String)
    vehicle_count = Column(Integer)
    duration_months = Column(Integer)
    vehicle_segment = Column(String)
    vehicle_type = Column(String)
    estimated_annual_mileage = Column(Integer)
    monthly_price_try = Column(Integer)
    status = Column(String, default="Teklif Verildi")
    contract_amount = Column(Float, nullable=True)
    created_at = Column(String)
    items = Column(JSON, default=list, nullable=True)
    details = Column(JSON, default=dict, nullable=True)


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    type = Column(String)  # servis / lastik / yol_yardim / ikame_arac
    status = Column(String, default="Beklemede")
    description = Column(Text)
    created_at = Column(String)
    completed_at = Column(String, nullable=True)
    details = Column(JSON, default=dict)


class SupplierBid(Base):
    __tablename__ = "supplier_bids"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    supplier_name = Column(String)  # denormalized for query speed
    monthly_price_try = Column(Integer)
    notes = Column(Text)
    created_at = Column(String)
    status = Column(String, default="Beklemede")


class VehicleRemoval(Base):
    __tablename__ = "vehicle_removals"

    id = Column(Integer, primary_key=True, index=True)
    registry_no = Column(String)
    reason = Column(Text)
    removed_at = Column(String)


class VehicleExpense(Base):
    __tablename__ = "vehicle_expenses"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False)
    kind = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(String, nullable=False)
    liters = Column(Float, nullable=True)
    mileage = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
    fuel_type = Column(String, nullable=True)
    station = Column(String, nullable=True)
    receipt_no = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    full_tank = Column(Boolean, nullable=False, default=False)


class VehicleFile(Base):
    __tablename__ = "vehicle_files"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    category = Column(String, nullable=False)  # photo / document
    document_type = Column(String, nullable=True)
    original_name = Column(String, nullable=False)
    stored_name = Column(String, nullable=False, unique=True)
    content_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(String, nullable=False)
    expiry_date = Column(String, nullable=True)


class HgsTransaction(Base):
    __tablename__ = "hgs_transactions"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(String, nullable=False)
    description = Column(String, nullable=True)
    balance = Column(Float, nullable=False)


class VehicleLocation(Base):
    __tablename__ = "vehicle_locations"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    label = Column(String, nullable=True)
    source = Column(String, nullable=False, default="manual")
    recorded_at = Column(String, nullable=False)


class TireRecord(Base):
    __tablename__ = "tire_records"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    brand = Column(String, nullable=False)
    size = Column(String, nullable=False)
    set_no = Column(String, nullable=True)
    season = Column(String, nullable=False, default="Dört Mevsim")
    production_date = Column(String, nullable=True)
    installed_at = Column(String, nullable=True)
    changed_at = Column(String, nullable=True)
    inspected_at = Column(String, nullable=True)
    tread_depth_mm = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="İyi")
    remaining_km = Column(Integer, nullable=True)
    position = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)


class TireOperation(Base):
    __tablename__ = "tire_operations"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    tire_id = Column(Integer, ForeignKey("tire_records.id"), nullable=True)
    type = Column(String, nullable=False)
    date = Column(String, nullable=False)
    mileage = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="Tamamlandı")


class RoadsideCase(Base):
    __tablename__ = "roadside_cases"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=True, unique=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    case_no = Column(String, nullable=False, unique=True, index=True)
    incident = Column(String, nullable=False)
    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="Beklemede")
    progress = Column(Integer, nullable=False, default=0)
    team_name = Column(String, nullable=True)
    team_phone = Column(String, nullable=True)
    dispatched_at = Column(String, nullable=True)
    eta_minutes = Column(Integer, nullable=True)
    distance_km = Column(Float, nullable=True)
    arrived_at = Column(String, nullable=True)
    resolved_at = Column(String, nullable=True)
    response_minutes = Column(Integer, nullable=True)
    photos = Column(JSON, default=list, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)


class RoadsideEvent(Base):
    __tablename__ = "roadside_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("roadside_cases.id"), nullable=False, index=True)
    status = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    eta_minutes = Column(Integer, nullable=True)
    distance_km = Column(Float, nullable=True)
    created_at = Column(String, nullable=False)


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
    is_email_verified = Column(Boolean, nullable=False, default=False)
    verification_token = Column(String, nullable=True)
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


# Supplier workspace: append-only business history alongside the shared customer fleet.
class SupplierCustomerLink(Base):
    __tablename__ = "supplier_customer_links"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(String, nullable=False)


class SupplierOperation(Base):
    __tablename__ = "supplier_operations"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    kind = Column(String, nullable=False, index=True)
    number = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), index=True)
    parent_id = Column(Integer, ForeignKey("supplier_operations.id"), index=True)
    date = Column(String, nullable=False)
    end_date = Column(String)
    amount = Column(Float, nullable=False, default=0)
    status = Column(String, nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)


class SupplierOperationEvent(Base):
    __tablename__ = "supplier_operation_events"
    id = Column(Integer, primary_key=True)
    operation_id = Column(Integer, ForeignKey("supplier_operations.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(String, nullable=False)


class SupplierPortalUser(Base):
    __tablename__ = "supplier_portal_users"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="viewer")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(String, nullable=False)


class SupplierSession(Base):
    __tablename__ = "supplier_sessions"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("supplier_portal_users.id"))
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(String, nullable=False)


class SupplierSetting(Base):
    __tablename__ = "supplier_settings"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, unique=True)
    value = Column(JSON, nullable=False, default=dict)


class IntegrationMapping(Base):
    __tablename__ = "integration_mappings"
    __table_args__ = (
        UniqueConstraint("supplier_id", "provider", "external_id"),
        UniqueConstraint("supplier_id", "provider", "vehicle_id"),
    )
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False)
    created_at = Column(String, nullable=False)


class IntegrationEvent(Base):
    __tablename__ = "integration_events"
    __table_args__ = (UniqueConstraint("supplier_id", "provider", "external_id"),)
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    vehicle_id = Column(String, ForeignKey("vehicles.id"))
    status = Column(String, nullable=False)
    reason = Column(String)
    occurred_at = Column(String, nullable=False)
    received_at = Column(String, nullable=False)
    processed_at = Column(String)


class PortalSession(Base):
    __tablename__ = "portal_sessions"
    id = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False)
    subject_id = Column(Integer, nullable=False)
    user_id = Column(Integer)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(String, nullable=False)


class AccessAudit(Base):
    __tablename__ = "access_audits"
    id = Column(Integer, primary_key=True)
    principal_kind = Column(String, nullable=False)
    subject_id = Column(Integer, nullable=False, index=True)
    method = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    created_at = Column(String, nullable=False)


class OfferVersion(Base):
    __tablename__ = "offer_versions"
    __table_args__ = (UniqueConstraint("offer_id", "version"),)
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, ForeignKey("supplier_operations.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    content_hash = Column(String, nullable=False)
    created_at = Column(String, nullable=False)


class MarketplaceOfferLink(Base):
    __tablename__ = "marketplace_offer_links"
    __table_args__ = (UniqueConstraint("supplier_id", "quote_id"),)
    bid_id = Column(Integer, ForeignKey("supplier_bids.id"), primary_key=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    offer_id = Column(Integer, ForeignKey("supplier_operations.id"), nullable=False, unique=True)


class CustomerOfferDecision(Base):
    __tablename__ = "customer_offer_decisions"
    __table_args__ = (UniqueConstraint("offer_id", "offer_version"),)
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, ForeignKey("supplier_operations.id"), nullable=False)
    offer_version = Column(Integer, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    decision = Column(String, nullable=False)
    note = Column(Text)
    actor = Column(String, nullable=False)
    created_at = Column(String, nullable=False)


class ContractVehicle(Base):
    __tablename__ = "contract_vehicles"
    __table_args__ = (UniqueConstraint("contract_id", "vehicle_id"),)
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    contract_id = Column(Integer, ForeignKey("supplier_operations.id"), nullable=False, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    monthly_rent = Column(Float, nullable=False)


class ContractOfferLink(Base):
    __tablename__ = "contract_offer_links"
    offer_id = Column(Integer, ForeignKey("supplier_operations.id"), primary_key=True)
    contract_id = Column(Integer, ForeignKey("supplier_operations.id"), nullable=False, unique=True)


class Rental(Base):
    __tablename__ = "rentals"
    __table_args__ = (UniqueConstraint("contract_id", "vehicle_id"),)
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    contract_id = Column(Integer, ForeignKey("supplier_operations.id"), nullable=False, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    delivery_id = Column(Integer, ForeignKey("supplier_operations.id"))
    return_id = Column(Integer, ForeignKey("supplier_operations.id"))
    status = Column(String, nullable=False)
    starts_at = Column(String, nullable=False)
    ends_at = Column(String, nullable=False)
    delivered_at = Column(String)
    returned_at = Column(String)
    version = Column(Integer, nullable=False, default=1)


class VehicleAssignment(Base):
    __tablename__ = "vehicle_assignments"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    rental_id = Column(Integer, ForeignKey("rentals.id"), nullable=True)
    driver_name = Column(String)
    starts_at = Column(String, nullable=False)
    ends_at = Column(String)


class VehicleSale(Base):
    __tablename__ = "vehicle_sales"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False, index=True)
    operation_id = Column(
        Integer, ForeignKey("supplier_operations.id"), nullable=False, unique=True
    )
    previous_group = Column(String)
    buyer_id = Column(Integer, ForeignKey("customers.id"))
    sold_at = Column(String)


class SignedDocument(Base):
    __tablename__ = "signed_documents"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    operation_id = Column(Integer, ForeignKey("supplier_operations.id"), nullable=False, index=True)
    stored_name = Column(String, nullable=False, unique=True)
    original_name = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    snapshot = Column(JSON, nullable=False)
    created_at = Column(String, nullable=False)


class SignatureEnvelope(Base):
    __tablename__ = "signature_envelopes"
    __table_args__ = (UniqueConstraint("operation_id", "operation_version"),)
    id = Column(Integer, primary_key=True)
    operation_id = Column(Integer, ForeignKey("supplier_operations.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("signed_documents.id"), nullable=False, unique=True)
    operation_version = Column(Integer, nullable=False)
    source = Column(String, nullable=False)
    status = Column(String, nullable=False)
    required_parties = Column(JSON, nullable=False)
    attestations = Column(JSON, nullable=False, default=dict)
    signed_date = Column(String, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False)
    completed_at = Column(String)


class AutomationRun(Base):
    __tablename__ = "automation_runs"
    __table_args__ = (UniqueConstraint("supplier_id", "vehicle_id", "rule", "rule_key"),)
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False)
    integration_event_id = Column(Integer, ForeignKey("integration_events.id"))
    rule = Column(String, nullable=False)
    rule_key = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    result = Column(String, nullable=False)
    operation_id = Column(Integer, ForeignKey("supplier_operations.id"))
    created_at = Column(String, nullable=False)


class EventResponsibility(Base):
    __tablename__ = "event_responsibilities"
    __table_args__ = (UniqueConstraint("supplier_id", "source_kind", "source_id"),)
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False)
    source_kind = Column(String, nullable=False)
    source_id = Column(Integer, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    reason = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)


class InvoiceIdentity(Base):
    __tablename__ = "invoice_identities"
    __table_args__ = (UniqueConstraint("supplier_id", "invoice_no"),)
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    invoice_no = Column(String, nullable=False)
    operation_id = Column(
        Integer, ForeignKey("supplier_operations.id"), nullable=False, unique=True
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True)
    principal_kind = Column(String, nullable=False)
    subject_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer)
    role = Column(String)
    target_supplier_id = Column(Integer, index=True)
    method = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    elapsed_ms = Column(Integer, nullable=False)
    created_at = Column(String, nullable=False)


class VehicleFileScope(Base):
    __tablename__ = "vehicle_file_scopes"
    file_id = Column(Integer, ForeignKey("vehicle_files.id"), primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    visibility = Column(String, nullable=False)


class IdentitySequence(Base):
    __tablename__ = "identity_sequences"
    name = Column(String, primary_key=True)
    last_value = Column(Integer, nullable=False)


# SQLite rowids can otherwise be reused after deletion, reviving old session subjects.
# This also covers existing databases whose original tables lack AUTOINCREMENT.


def _reserve_identity(mapper, connection, target):
    if connection.dialect.name != "sqlite":
        return
    name = target.__tablename__
    if target.id is None:
        minimum = (connection.execute(select(func.max(target.__table__.c.id))).scalar() or 0) + 1
        target.id = connection.execute(
            sql_text(
                "INSERT INTO identity_sequences (name,last_value) VALUES (:name,:minimum) ON CONFLICT(name) DO UPDATE SET last_value=MAX(identity_sequences.last_value+1,:minimum) RETURNING last_value"
            ),
            {"name": name, "minimum": minimum},
        ).scalar_one()
    else:
        connection.execute(
            sql_text(
                "INSERT INTO identity_sequences (name,last_value) VALUES (:name,:minimum) ON CONFLICT(name) DO UPDATE SET last_value=MAX(identity_sequences.last_value,:minimum)"
            ),
            {"name": name, "minimum": target.id},
        )


for _identity_class in (Supplier, Customer, AdminUser, SupplierPortalUser, CustomerPortalUser):
    event.listen(_identity_class, "before_insert", _reserve_identity)
    event.listen(_identity_class, "before_delete", _reserve_identity)
