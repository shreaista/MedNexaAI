from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TenantSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str | None


class FacilityWithTenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    tenant: TenantSummary


class FacilitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
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
