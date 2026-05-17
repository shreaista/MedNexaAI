from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.billing import BillingQueue, Charge, ClaimReadiness
from app.models.clinical import ClinicalVisit, VisitDiagnosis, VisitNote, VisitProcedure
from app.schemas.billing import ChargeWorkflowResult
from app.services.readiness_service import evaluate_charge_workflow

router = APIRouter(prefix="/visits", tags=["charges"])


def _count_signed_notes(db: Session, visit_id: UUID) -> int:
    n = db.scalar(
        select(func.count())
        .select_from(VisitNote)
        .where(
            VisitNote.visit_id == visit_id,
            func.upper(VisitNote.note_status) == "SIGNED",
        )
    )
    return int(n or 0)


def _count_any_notes(db: Session, visit_id: UUID) -> int:
    n = db.scalar(select(func.count()).select_from(VisitNote).where(VisitNote.visit_id == visit_id))
    return int(n or 0)


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

    has_any_note = _count_any_notes(db, visit_id) > 0
    has_signed_note = _count_signed_notes(db, visit_id) > 0

    evaluation = evaluate_charge_workflow(
        has_signed_note=has_signed_note,
        has_any_note=has_any_note,
        has_diagnosis=first_dx is not None,
        has_procedure=first_px is not None,
    )

    total_units = float(first_px.units) if first_px is not None else None

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
            missing_note_flag=evaluation.missing_note_flag,
            missing_diagnosis_flag=evaluation.missing_diagnosis_flag,
            missing_cpt_flag=evaluation.missing_cpt_flag,
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
            detail="Unable to persist charge workflow (duplicate visit charge or constraint violation).",
        )

    db.refresh(charge)
    db.refresh(queue)
    db.refresh(readiness)

    return ChargeWorkflowResult(
        charge_id=charge.charge_id,
        queue_id=queue.queue_id,
        readiness_score=float(readiness.readiness_score),
        readiness_status=readiness.readiness_status,
        recommendation=evaluation.recommendation,
        total_units=total_units,
        documentation_support_status=evaluation.documentation_support_status,
    )
