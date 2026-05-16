from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TenantSummary(BaseModel):
    """Maps `tenants` row for nested responses."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    tenant_name: str
    tenant_code: str
    status: str


class FacilityWithTenantOut(BaseModel):
    """One row from `facilities` joined to `tenants` (tenant name as `tenant_name`)."""

    facility_id: UUID
    tenant_id: UUID
    tenant_name: str
    facility_name: str
    facility_type: str | None
    address_line1: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    status: str


class FacilitySummary(BaseModel):
    """Nested facility snippet for patient detail (matches `facilities` columns)."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    facility_id: UUID
    tenant_id: UUID
    facility_name: str
    facility_type: str | None
    address_line1: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    status: str


class CensusRowOut(BaseModel):
    census_id: UUID
    patient_id: UUID
    mrn: str | None
    patient_name: str | None
    date_of_birth: str | None
    gender: str | None
    payer_name: str | None
    room_number: str | None
    bed_number: str | None
    care_level: str | None
    visit_due_flag: bool
    unsigned_note_flag: bool
    missing_charge_flag: bool
