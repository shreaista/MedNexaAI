from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FacilitySummary(BaseModel):
    """Nested facility snippet for patient context."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    active: bool


class PatientDetailOut(BaseModel):
    patient_id: UUID
    tenant_id: UUID
    external_id: str | None
    first_name: str | None
    last_name: str | None
    birth_date: date | None
    gender: str | None
    active: bool
    facility: FacilitySummary | None


class VisitCreate(BaseModel):
    tenant_id: UUID = Field(description="Must match an existing tenant (demo seed UUID supported).")
    facility_id: UUID
    patient_id: UUID
    provider_id: UUID
    visit_type: str = Field(min_length=1, max_length=64)
    specialty: str = Field(min_length=1, max_length=128)
    chief_complaint: str | None = Field(default=None, max_length=4000)


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    facility_id: UUID
    patient_id: UUID
    provider_id: UUID
    visit_type: str
    specialty: str
    chief_complaint: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class VisitDiagnosisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    visit_id: UUID
    icd10_code: str
    description: str
    is_primary: bool
    created_at: datetime


class VisitProcedureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    visit_id: UUID
    cpt_code: str
    description: str
    created_at: datetime


class VisitNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    visit_id: UUID
    subjective: str | None
    objective: str | None
    assessment: str | None
    plan: str | None
    full_note: str
    ai_generated: bool
    note_status: str
    signed_at: datetime | None
    signed_by: UUID | None
    created_at: datetime
    updated_at: datetime


class VisitDetailOut(VisitOut):
    diagnoses: list[VisitDiagnosisOut]
    procedures: list[VisitProcedureOut]
    notes: list[VisitNoteOut]


class VisitNoteCreate(BaseModel):
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    full_note: str = Field(default="", max_length=20000)
    ai_generated: bool = False


class NoteSignRequest(BaseModel):
    signed_by: UUID | None = Field(
        default=None,
        description="Optional provider user id; stored when signing without full auth.",
    )


class DiagnosisCreate(BaseModel):
    icd10_code: str = Field(min_length=1, max_length=16)
    description: str = Field(default="", max_length=512)
    is_primary: bool = False


class ProcedureCreate(BaseModel):
    cpt_code: str = Field(min_length=1, max_length=16)
    description: str = Field(default="", max_length=512)
