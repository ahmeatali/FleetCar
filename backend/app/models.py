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
    is_email_verified   = Column(Boolean, default=True)
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
