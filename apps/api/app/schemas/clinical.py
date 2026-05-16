from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.core import FacilitySummary


class PatientDetailOut(BaseModel):
    patient_id: UUID
    tenant_id: UUID
    mrn: str | None
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    gender: str | None
    facility: FacilitySummary | None


class VisitCreate(BaseModel):
    tenant_id: UUID
    facility_id: UUID
    patient_id: UUID
    provider_id: UUID
    visit_type: str = Field(min_length=1, max_length=64)
    specialty: str = Field(min_length=1, max_length=128)
    chief_complaint: str | None = Field(default=None, max_length=4000)


class ProviderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(validation_alias="provider_id")
    full_name: str


class PatientSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(validation_alias="patient_id")
    mrn: str | None
    first_name: str | None
    last_name: str | None


class VisitSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(validation_alias="visit_id")
    tenant_id: UUID
    facility_id: UUID
    patient_id: UUID
    provider_id: UUID
    visit_type: str
    specialty: str
    chief_complaint: str | None
    status: str | None
    created_at: datetime
    updated_at: datetime


class VisitNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(validation_alias="note_id")
    visit_id: UUID
    tenant_id: UUID
    patient_id: UUID
    provider_id: UUID
    subjective: str | None
    objective: str | None
    assessment: str | None
    plan: str | None
    full_note: str | None
    ai_generated: bool
    note_status: str
    signed_at: datetime | None
    signed_by: UUID | None
    ai_review_status: str | None
    created_at: datetime
    updated_at: datetime


class VisitDiagnosisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(validation_alias="diagnosis_id")
    visit_id: UUID
    tenant_id: UUID
    icd10_code: str
    description: str | None
    is_ai_suggested: bool
    confidence_score: Decimal | None
    created_at: datetime


class VisitProcedureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(validation_alias="procedure_id")
    visit_id: UUID
    tenant_id: UUID
    cpt_code: str
    description: str | None
    modifier: str | None
    units: Decimal
    is_ai_suggested: bool
    confidence_score: Decimal | None
    created_at: datetime


class ChargeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(validation_alias="charge_id")
    charge_status: str
    primary_icd10: str | None
    primary_cpt: str | None
    amount_cents: int


class VisitDetailOut(BaseModel):
    visit: VisitSummary
    patient: PatientSummary
    provider: ProviderSummary
    note: VisitNoteOut | None
    diagnoses: list[VisitDiagnosisOut]
    procedures: list[VisitProcedureOut]
    charge: ChargeSummary | None


class VisitNoteCreate(BaseModel):
    tenant_id: UUID
    patient_id: UUID
    provider_id: UUID
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    full_note: str | None = Field(default=None, max_length=20000)
    ai_generated: bool = False


class NoteSignBody(BaseModel):
    signed_by: UUID


class DiagnosisCreate(BaseModel):
    tenant_id: UUID
    icd10_code: str = Field(min_length=1, max_length=16)
    description: str | None = Field(default=None, max_length=512)
    is_ai_suggested: bool = False
    confidence_score: Decimal | None = Field(default=None, ge=0, le=100)


class ProcedureCreate(BaseModel):
    tenant_id: UUID
    cpt_code: str = Field(min_length=1, max_length=16)
    description: str | None = Field(default=None, max_length=512)
    modifier: str | None = Field(default=None, max_length=16)
    units: Decimal = Field(default=Decimal("1"), gt=0)
    is_ai_suggested: bool = False
    confidence_score: Decimal | None = Field(default=None, ge=0, le=100)
