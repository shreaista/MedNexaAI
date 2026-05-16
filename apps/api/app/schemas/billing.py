from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChargeWorkflowResult(BaseModel):
    charge_id: UUID
    queue_id: UUID
    readiness_score: float
    readiness_status: str


class BillingQueueListItem(BaseModel):
    queue_id: UUID
    queue_status: str
    priority: str
    charge_id: UUID
    charge_status: str
    patient_name: str
    mrn: str | None
    provider_name: str
    primary_icd10: str | None
    primary_cpt: str | None
    readiness_score: Decimal
    readiness_status: str


class ClaimReadinessFlagsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    missing_note_flag: bool
    missing_diagnosis_flag: bool
    missing_cpt_flag: bool
