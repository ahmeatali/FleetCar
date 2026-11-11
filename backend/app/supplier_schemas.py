"""Supplier workflow request contracts; no router or persistence dependencies."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.approval_rules import validate_matrix


class OperationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    customer_id: Optional[int] = Field(None, gt=0)
    vehicle_id: Optional[str] = None
    parent_id: Optional[int] = Field(None, gt=0)
    date: date
    end_date: Optional[date] = None
    amount: float = Field(0, ge=0, allow_inf_nan=False, multiple_of=0.01)
    details: dict = Field(default_factory=dict)
    version: Optional[int] = Field(None, gt=0)

    @field_validator("details")
    @classmethod
    def finite_json(cls, value):
        import json

        try:
            encoded = json.dumps(value, allow_nan=False)
        except (ValueError, TypeError, RecursionError):
            raise ValueError("Bilgi alanları geçerli JSON ve sonlu sayılar içermeli.")
        if len(encoded) > 250000:
            raise ValueError("Bilgi alanları çok büyük.")
        return value

    @field_validator("title")
    @classmethod
    def clean_title(cls, value):
        if not value.strip():
            raise ValueError("Başlık boş olamaz.")
        return value.strip()


class TransitionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    version: int = Field(gt=0)


class ConvertInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vehicle_id: Optional[str] = None
    vehicle_ids: Optional[list[str]] = Field(None, min_length=1, max_length=10000)
    kind: Literal["contract", "delivery", "invoice"]
    version: int = Field(gt=0)


class CustomerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: Optional[int] = Field(None, gt=0)
    company_name: str = Field(min_length=1, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    details: dict = Field(default_factory=dict)


class PasswordChangeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=10, max_length=200)


class DealerStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    at_dealer: bool


class MemberInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=200)
    password: Optional[str] = Field(None, min_length=10)
    role: Literal["fleet_manager", "operations", "finance", "sales", "delivery", "viewer"] = (
        "viewer"
    )
    is_active: bool = True


class SettingsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approval_threshold: float = Field(100000, ge=0, allow_inf_nan=False)
    approval_matrix: Optional[dict] = None
    low_balance: float = Field(200, ge=0, allow_inf_nan=False)
    renewal_days: int = Field(30, ge=1, le=365)
    low_usage_km: int = Field(500, ge=0)
    fuel_l100_threshold: float = Field(12, gt=0, allow_inf_nan=False)
    company_name: str = Field("", max_length=200)
    currency: Literal["TRY"] = "TRY"
    company_mode: Literal["EXTERNAL_INTEGRATION", "FLEETRENT_PANEL"] = "FLEETRENT_PANEL"


    @field_validator("approval_matrix")
    @classmethod
    def check_matrix(cls, value):
        return None if value is None else validate_matrix(value)


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "reject"]
    note: str = Field("", max_length=1000)
    version: int = Field(gt=0)


class SharedInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vehicle_id: str
    date: date
    amount: float = Field(0, ge=0, allow_inf_nan=False, multiple_of=0.01)
    title: str = Field(min_length=1, max_length=200)
    details: dict = Field(default_factory=dict)
