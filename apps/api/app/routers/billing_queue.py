from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.billing import BillingQueue, Charge, ClaimReadiness
from app.models.clinical import ClinicalVisit, Patient
from app.models.core import Provider
from app.schemas.billing import BillingQueueListItem

router = APIRouter(prefix="/billing-queue", tags=["billing-queue"])

_queue_reason_constant = "New submitted charge"


def _patient_display(patient: Patient) -> str:
    parts = [patient.first_name or "", patient.last_name or ""]
    label = " ".join(part for part in parts if part).strip()
    return label or (patient.mrn or str(patient.patient_id))


@router.get("", response_model=list[BillingQueueListItem])
def list_billing_queue(db: Session = Depends(get_db)) -> list[BillingQueueListItem]:
    stmt = (
        select(BillingQueue, Charge, Patient, Provider, ClaimReadiness, ClinicalVisit)
        .join(Charge, BillingQueue.charge_id == Charge.charge_id)
        .join(Patient, Charge.patient_id == Patient.patient_id)
        .join(ClinicalVisit, Charge.visit_id == ClinicalVisit.visit_id)
        .outerjoin(Provider, Charge.provider_id == Provider.provider_id)
        .outerjoin(ClaimReadiness, ClaimReadiness.charge_id == Charge.charge_id)
        .order_by(BillingQueue.created_at.desc())
    )

    rows = db.execute(stmt).all()
    items: list[BillingQueueListItem] = []

    for queue, charge, patient, provider, readiness, _visit in rows:
        score = readiness.readiness_score if readiness is not None else Decimal("0")
        rstatus = readiness.readiness_status if readiness is not None else "UNKNOWN"
        pname = provider.full_name if provider is not None else "Unassigned provider"
        items.append(
            BillingQueueListItem(
                queue_id=queue.queue_id,
                queue_status=queue.queue_status,
                priority=queue.priority,
                queue_reason=_queue_reason_constant,
                charge_id=charge.charge_id,
                charge_status=charge.charge_status,
                patient_id=patient.patient_id,
                patient_name=_patient_display(patient),
                mrn=patient.mrn,
                provider_name=pname,
                primary_icd10=charge.primary_icd10,
                primary_cpt=charge.primary_cpt,
                readiness_score=score,
                readiness_status=rstatus,
                created_at=queue.created_at,
            )
        )

    return items
