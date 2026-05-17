from datetime import date, datetime
from decimal import Decimal
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def _patient_display_name(
    first: str | None,
    last: str | None,
    mrn: str | None,
    patient_id: UUID,
) -> str:
    label = " ".join(p for p in [first or "", last or ""] if p).strip()
    return label or (mrn or str(patient_id))


# --- GET /patients/{patient_id} -------------------------------------------------


class PatientDetailOut(BaseModel):
    patient_id: UUID
    tenant_id: UUID
    facility_id: UUID | None = None
    facility_name: str | None = None
    mrn: str | None
    first_name: str | None
    last_name: str | None
    patient_name: str
    date_of_birth: date | None
    gender: str | None
    payer_name: str | None = None
    insurance_member_id: str | None = None
    status: str | None = None
    admission_date: date | None = None
    discharge_date: date | None = None

    @classmethod
    def from_patient_and_facility(
        cls,
        *,
        patient: Any,
        facility_name: str | None,
    ) -> Self:
        return cls(
            patient_id=patient.patient_id,
            tenant_id=patient.tenant_id,
            facility_id=patient.facility_id,
            facility_name=facility_name,
            mrn=patient.mrn,
            first_name=patient.first_name,
            last_name=patient.last_name,
            patient_name=_patient_display_name(
                patient.first_name,
                patient.last_name,
                patient.mrn,
                patient.patient_id,
            ),
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            payer_name=patient.payer_name,
            insurance_member_id=patient.insurance_member_id,
            status=patient.status,
            admission_date=patient.admission_date,
            discharge_date=patient.discharge_date,
        )


# --- POST /visits ---------------------------------------------------------------


class VisitCreate(BaseModel):
    tenant_id: UUID
    facility_id: UUID
    patient_id: UUID
    provider_id: UUID
    visit_type: str = Field(min_length=1, max_length=64)
    specialty: str = Field(min_length=1, max_length=128)
    chief_complaint: str | None = Field(default=None, max_length=4000)
    visit_date: date | None = Field(
        default=None,
        description="Encounters visit_date column; defaults to today on the server when omitted.",
    )


class VisitCreatedOut(BaseModel):
    visit_id: UUID
    visit_status: str
    patient_id: UUID
    provider_id: UUID


# --- GET /visits/{visit_id} -----------------------------------------------------


class VisitBlockOut(BaseModel):
    visit_id: UUID
    tenant_id: UUID
    facility_id: UUID
    patient_id: UUID
    provider_id: UUID
    visit_type: str
    specialty: str
    chief_complaint: str | None
    visit_status: str
    visit_date: date
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_visit(cls, v: Any) -> Self:
        vd = v.visit_date if getattr(v, "visit_date", None) is not None else (
            v.created_at.date() if getattr(v, "created_at", None) else date.today()
        )
        return cls(
            visit_id=v.visit_id,
            tenant_id=v.tenant_id,
            facility_id=v.facility_id,
            patient_id=v.patient_id,
            provider_id=v.provider_id,
            visit_type=v.visit_type,
            specialty=v.specialty,
            chief_complaint=v.chief_complaint,
            visit_status=(v.visit_status or "UNKNOWN").strip(),
            visit_date=vd,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )


VisitSummary = VisitBlockOut


class PatientBlockOut(BaseModel):
    patient_id: UUID
    tenant_id: UUID
    mrn: str | None
    first_name: str | None
    last_name: str | None
    patient_name: str
    date_of_birth: date | None
    gender: str | None

    @classmethod
    def from_patient(cls, p: Any) -> Self:
        return cls(
            patient_id=p.patient_id,
            tenant_id=p.tenant_id,
            mrn=p.mrn,
            first_name=p.first_name,
            last_name=p.last_name,
            patient_name=_patient_display_name(p.first_name, p.last_name, p.mrn, p.patient_id),
            date_of_birth=p.date_of_birth,
            gender=p.gender,
        )


class ProviderBlockOut(BaseModel):
    provider_id: UUID
    tenant_id: UUID
    full_name: str
    user_id: UUID | None = None


class ProviderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider_id: UUID
    full_name: str


class PatientSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: UUID
    mrn: str | None
    first_name: str | None
    last_name: str | None


class VisitNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_id: UUID
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
    model_config = ConfigDict(from_attributes=True)

    diagnosis_id: UUID
    visit_id: UUID
    tenant_id: UUID
    icd10_code: str
    description: str | None
    is_ai_suggested: bool
    confidence_score: Decimal | None
    created_at: datetime


class VisitProcedureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    procedure_id: UUID
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
    model_config = ConfigDict(from_attributes=True)

    charge_id: UUID
    charge_status: str
    primary_icd10: str | None
    primary_cpt: str | None
    charge_amount: float


class ChargeDetailOut(BaseModel):
    charge_id: UUID
    tenant_id: UUID
    visit_id: UUID
    patient_id: UUID
    facility_id: UUID | None
    provider_id: UUID | None
    charge_status: str
    primary_icd10: str | None
    primary_cpt: str | None
    charge_amount: float
    total_units: float | None = None
    documentation_support_status: str


class ClaimReadinessBlockOut(BaseModel):
    readiness_id: UUID
    charge_id: UUID
    readiness_score: float
    readiness_status: str
    missing_note_flag: bool
    missing_diagnosis_flag: bool
    missing_cpt_flag: bool
    recommendation: str


class VisitDetailOut(BaseModel):
    visit: VisitBlockOut
    patient: PatientBlockOut
    provider: ProviderBlockOut
    note: VisitNoteOut | None
    diagnoses: list[VisitDiagnosisOut]
    procedures: list[VisitProcedureOut]
    charge: ChargeDetailOut | None
    claim_readiness: ClaimReadinessBlockOut | None


# --- POST /visits/{visit_id}/notes ---------------------------------------------


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


class NoteCreatedOut(BaseModel):
    note_id: UUID
    note_status: str


# --- PUT /notes/{note_id}/sign -------------------------------------------------


class NoteSignBody(BaseModel):
    signed_by: UUID


class NoteSignedOut(BaseModel):
    note_id: UUID
    note_status: str
    signed_at: datetime


# --- POST diagnoses / procedures ----------------------------------------------


class DiagnosisCreate(BaseModel):
    tenant_id: UUID
    icd10_code: str = Field(min_length=1, max_length=16)
    description: str | None = Field(default=None, max_length=512)
    is_ai_suggested: bool = False
    confidence_score: Decimal | None = Field(default=None, ge=0, le=100)


class DiagnosisCreatedOut(BaseModel):
    diagnosis_id: UUID


class ProcedureCreate(BaseModel):
    tenant_id: UUID
    cpt_code: str = Field(min_length=1, max_length=16)
    description: str | None = Field(default=None, max_length=512)
    modifier: str | None = Field(default=None, max_length=16)
    units: Decimal = Field(default=Decimal("1"), gt=0)
    is_ai_suggested: bool = False
    confidence_score: Decimal | None = Field(default=None, ge=0, le=100)


class ProcedureCreatedOut(BaseModel):
    procedure_id: UUID
