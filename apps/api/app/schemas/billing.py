from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChargeWorkflowResult(BaseModel):
    charge_id: UUID
    queue_id: UUID
    readiness_score: float
    readiness_status: str
    recommendation: str
    total_units: float | None = None
    documentation_support_status: str
    message: str | None = None


class BillingQueueListItem(BaseModel):
    queue_id: UUID
    queue_status: str
    priority: str
    queue_reason: str
    charge_id: UUID
    charge_status: str
    patient_id: UUID
    patient_name: str
    mrn: str | None
    provider_name: str
    primary_icd10: str | None
    primary_cpt: str | None
    readiness_score: Decimal
    readiness_status: str
    created_at: datetime


class ClaimReadinessFlagsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    missing_note_flag: bool
    missing_diagnosis_flag: bool
    missing_cpt_flag: bool
