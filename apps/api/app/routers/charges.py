from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.billing import BillingQueue, Charge, ClaimReadiness
from app.models.clinical import ClinicalVisit, VisitDiagnosis, VisitNote, VisitProcedure
from app.schemas.billing import ChargeWorkflowResult
from app.services.readiness_service import evaluate_claim_readiness

router = APIRouter(prefix="/visits", tags=["charges"])


@router.post(
    "/{visit_id}/charges",
    response_model=ChargeWorkflowResult,
    status_code=status.HTTP_201_CREATED,
)
def create_charge_from_visit(
    visit_id: UUID,
    db: Session = Depends(get_db),
) -> ChargeWorkflowResult:
    visit = db.get(ClinicalVisit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    first_dx = db.scalar(
        select(VisitDiagnosis)
        .where(VisitDiagnosis.visit_id == visit_id)
        .order_by(VisitDiagnosis.created_at.asc())
        .limit(1)
    )
    first_px = db.scalar(
        select(VisitProcedure)
        .where(VisitProcedure.visit_id == visit_id)
        .order_by(VisitProcedure.created_at.asc())
        .limit(1)
    )

    has_note = (
        db.scalar(
            select(VisitNote.note_id).where(VisitNote.visit_id == visit_id).limit(1)
        )
        is not None
    )
    has_dx = first_dx is not None
    has_px = first_px is not None

    evaluation = evaluate_claim_readiness(
        has_note=has_note,
        has_diagnosis=has_dx,
        has_procedure=has_px,
    )

    charge = Charge(
        tenant_id=visit.tenant_id,
        visit_id=visit_id,
        patient_id=visit.patient_id,
        facility_id=visit.facility_id,
        provider_id=visit.provider_id,
        primary_icd10=first_dx.icd10_code if first_dx else None,
        primary_cpt=first_px.cpt_code if first_px else None,
        charge_status="SUBMITTED",
        amount_cents=0,
    )

    try:
        db.add(charge)
        db.flush()

        readiness = ClaimReadiness(
            charge_id=charge.charge_id,
            readiness_score=Decimal(str(evaluation.readiness_score)),
            readiness_status=evaluation.readiness_status,
            missing_note_flag=evaluation.missing_note,
            missing_diagnosis_flag=evaluation.missing_diagnosis,
            missing_cpt_flag=evaluation.missing_cpt,
        )
        queue = BillingQueue(
            tenant_id=visit.tenant_id,
            charge_id=charge.charge_id,
            queue_status="NEW",
            priority="NORMAL",
        )
        db.add(queue)
        db.add(readiness)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Unable to persist charge workflow (duplicate or constraint violation)",
        )

    db.refresh(charge)
    db.refresh(queue)
    db.refresh(readiness)

    return ChargeWorkflowResult(
        charge_id=charge.charge_id,
        queue_id=queue.queue_id,
        readiness_score=float(readiness.readiness_score),
        readiness_status=readiness.readiness_status,
    )
