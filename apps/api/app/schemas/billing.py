from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChargeCreate(BaseModel):
    diagnosis_id: UUID
    procedure_id: UUID
    amount_cents: int = Field(default=0, ge=0)


class ChargeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    visit_id: UUID
    facility_id: UUID
    patient_id: UUID
    diagnosis_id: UUID | None
    procedure_id: UUID | None
    amount_cents: int
    charge_status: str
    created_at: datetime
    updated_at: datetime


class ChargeWithWorkflowOut(BaseModel):
    """Charge plus downstream billing workflow records."""

    charge: ChargeOut
    billing_queue_id: UUID
    queue_status: str
    claim_readiness_id: UUID
    readiness_score: float
    readiness_status: str


class BillingQueueItemOut(BaseModel):
    """Flattened billing queue row for list screens."""

    queue_id: UUID
    queue_status: str
    charge_id: UUID
    charge_status: str
    amount_cents: int
    visit_id: UUID
    patient_id: UUID
    patient_display: str
    provider_id: UUID
    provider_email: str
    readiness_score: float
    readiness_status: str
