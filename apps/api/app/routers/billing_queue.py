from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import tenant_query
from app.models.billing import BillingQueue, Charge, ClaimReadiness
from app.models.clinical import Patient, Visit
from app.models.core import User
from app.schemas.billing import BillingQueueItemOut

router = APIRouter(prefix="/billing-queue", tags=["billing"])


def _patient_label(patient: Patient) -> str:
    parts = [patient.first_name or "", patient.last_name or ""]
    label = " ".join(p.strip() for p in parts if p.strip())
    return label or (patient.external_id or str(patient.id))


@router.get("", response_model=list[BillingQueueItemOut])
def list_billing_queue(
    tenant_id: UUID = Depends(tenant_query),
    db: Session = Depends(get_db),
) -> list[BillingQueueItemOut]:
    stmt = (
        select(BillingQueue, Charge, Patient, Visit, User, ClaimReadiness)
        .join(Charge, BillingQueue.charge_id == Charge.id)
        .join(Patient, Charge.patient_id == Patient.id)
        .join(Visit, Charge.visit_id == Visit.id)
        .join(User, Visit.provider_id == User.id)
        .outerjoin(ClaimReadiness, ClaimReadiness.charge_id == Charge.id)
        .where(BillingQueue.tenant_id == tenant_id)
        .order_by(BillingQueue.created_at.desc())
    )

    rows = db.execute(stmt).all()
    result: list[BillingQueueItemOut] = []
    for queue, charge, patient, visit, provider, readiness in rows:
        score = float(readiness.readiness_score) if readiness is not None else 0.0
        rstatus = readiness.status if readiness is not None else "UNKNOWN"
        result.append(
            BillingQueueItemOut(
                queue_id=queue.id,
                queue_status=queue.queue_status,
                charge_id=charge.id,
                charge_status=charge.charge_status,
                amount_cents=charge.amount_cents,
                visit_id=visit.id,
                patient_id=patient.id,
                patient_display=_patient_label(patient),
                provider_id=provider.id,
                provider_email=provider.email,
                readiness_score=score,
                readiness_status=rstatus,
            )
        )
    return result
