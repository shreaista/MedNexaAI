from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.billing import BillingQueue, Charge, ClaimReadiness
from app.models.clinical import Visit, VisitDiagnosis, VisitProcedure
from app.schemas.billing import ChargeCreate, ChargeOut, ChargeWithWorkflowOut

router = APIRouter(prefix="/visits", tags=["charges"])


def _readiness_score(diagnosis_id: UUID | None, procedure_id: UUID | None) -> Decimal:
    """Heuristic readiness score placeholder until payer rules integrate."""
    if diagnosis_id is not None and procedure_id is not None:
        return Decimal("92.50")
    if diagnosis_id is not None or procedure_id is not None:
        return Decimal("68.00")
    return Decimal("45.00")


@router.post(
    "/{visit_id}/charges",
    response_model=ChargeWithWorkflowOut,
    status_code=status.HTTP_201_CREATED,
)
def create_visit_charge(
    visit_id: UUID,
    body: ChargeCreate,
    db: Session = Depends(get_db),
) -> ChargeWithWorkflowOut:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    diagnosis = db.get(VisitDiagnosis, body.diagnosis_id)
    if diagnosis is None or diagnosis.visit_id != visit_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Diagnosis does not belong to this visit",
        )

    procedure = db.get(VisitProcedure, body.procedure_id)
    if procedure is None or procedure.visit_id != visit_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Procedure does not belong to this visit",
        )

    score = _readiness_score(body.diagnosis_id, body.procedure_id)

    charge = Charge(
        tenant_id=visit.tenant_id,
        visit_id=visit_id,
        facility_id=visit.facility_id,
        patient_id=visit.patient_id,
        diagnosis_id=body.diagnosis_id,
        procedure_id=body.procedure_id,
        amount_cents=body.amount_cents,
        charge_status="SUBMITTED",
    )

    try:
        db.add(charge)
        db.flush()

        billing_queue_row = BillingQueue(
            tenant_id=visit.tenant_id,
            charge_id=charge.id,
            queue_status="NEW",
        )
        readiness = ClaimReadiness(
            charge_id=charge.id,
            readiness_score=score,
            status="EVALUATED",
        )
        db.add(billing_queue_row)
        db.add(readiness)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Charge workflow record could not be created",
        )

    db.refresh(charge)
    db.refresh(billing_queue_row)
    db.refresh(readiness)

    return ChargeWithWorkflowOut(
        charge=ChargeOut.model_validate(charge),
        billing_queue_id=billing_queue_row.id,
        queue_status=billing_queue_row.queue_status,
        claim_readiness_id=readiness.id,
        readiness_score=float(readiness.readiness_score),
        readiness_status=readiness.status,
    )
