from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FacilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    active: bool
    created_at: datetime
    updated_at: datetime


class CensusPatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    facility_id: UUID | None
    external_id: str | None
    first_name: str | None
    last_name: str | None
    birth_date: date | None
    gender: str | None
    active: bool
