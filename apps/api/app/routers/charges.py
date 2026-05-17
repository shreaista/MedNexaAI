from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.billing import BillingQueue, Charge, ClaimReadiness
from app.models.clinical import ClinicalVisit, VisitDiagnosis, VisitNote, VisitProcedure
from app.schemas.billing import ChargeWorkflowResult
from app.services.readiness_service import ClaimReadinessEvaluation, evaluate_charge_workflow

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


def _evaluate_visit_for_charge(
    db: Session,
    visit_id: UUID,
) -> tuple[VisitDiagnosis | None, VisitProcedure | None, float | None, ClaimReadinessEvaluation]:
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
    total_u = float(first_px.units) if first_px is not None else None
    has_any_note = _count_any_notes(db, visit_id) > 0
    has_signed_note = _count_signed_notes(db, visit_id) > 0
    ev = evaluate_charge_workflow(
        has_signed_note=has_signed_note,
        has_any_note=has_any_note,
        has_diagnosis=first_dx is not None,
        has_procedure=first_px is not None,
    )
    return first_dx, first_px, total_u, ev


def _safe_db_detail(step: str, exc: Exception) -> str:
    orig = getattr(exc, "orig", None)
    raw = str(orig) if orig is not None else str(exc)
    raw = raw.strip() or repr(exc)
    return f"{step}: {raw[:480]}"


def _flush_step(db: Session, step: str) -> None:
    """Flush with rollback on failure; detail names the failing insert step."""
    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=_safe_db_detail(step, e),
        ) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_safe_db_detail(step, e),
        ) from e


def _claim_readiness_row(tenant_id: UUID, charge_id: UUID, ev: ClaimReadinessEvaluation) -> ClaimReadiness:
    return ClaimReadiness(
        tenant_id=tenant_id,
        charge_id=charge_id,
        readiness_score=Decimal(str(ev.readiness_score)),
        readiness_status=ev.readiness_status,
        missing_note_flag=ev.missing_note_flag,
        missing_diagnosis_flag=ev.missing_diagnosis_flag,
        missing_cpt_flag=ev.missing_cpt_flag,
        missing_authorization_flag=False,
        payer_rule_issue_flag=False,
        recommendation=ev.recommendation,
    )


def _billing_queue_row(tenant_id: UUID, charge_id: UUID) -> BillingQueue:
    return BillingQueue(
        tenant_id=tenant_id,
        charge_id=charge_id,
        queue_status="NEW",
        priority="NORMAL",
    )


def _mark_visit_charge_complete(db: Session, visit_id: UUID) -> ClinicalVisit:
    """Set clinical_visits.visit_status = COMPLETED after successful charge workflow (idempotent)."""
    visit_row = db.get(ClinicalVisit, visit_id)
    if visit_row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")
    if (visit_row.visit_status or "").strip().upper() != "COMPLETED":
        visit_row.visit_status = "COMPLETED"
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_safe_db_detail("update_visit_status_completed", e),
            ) from e
        db.refresh(visit_row)
    return visit_row


def _charge_workflow_result(
    *,
    visit: ClinicalVisit,
    charge: Charge,
    queue: BillingQueue,
    readiness: ClaimReadiness,
    total_units: float | None,
    ev: ClaimReadinessEvaluation,
    message: str | None = None,
) -> ChargeWorkflowResult:
    return ChargeWorkflowResult(
        visit_id=visit.visit_id,
        visit_status=visit.visit_status or "COMPLETED",
        charge_id=charge.charge_id,
        queue_id=queue.queue_id,
        readiness_score=float(readiness.readiness_score),
        readiness_status=readiness.readiness_status,
        recommendation=(readiness.recommendation or ev.recommendation or ""),
        total_units=total_units,
        documentation_support_status=ev.documentation_support_status,
        message=message,
    )


def _ensure_queue_and_readiness(
    db: Session,
    visit: ClinicalVisit,
    existing_charge: Charge,
    ev: ClaimReadinessEvaluation,
) -> tuple[BillingQueue, ClaimReadiness, bool]:
    """
    Ensure billing_queue and claim_readiness exist for an existing charge.
    Returns (queue, readiness, repaired_anything).
    """
    queue_row = db.scalar(select(BillingQueue).where(BillingQueue.charge_id == existing_charge.charge_id))
    readiness_row = db.scalar(
        select(ClaimReadiness).where(ClaimReadiness.charge_id == existing_charge.charge_id)
    )

    if queue_row is not None and readiness_row is not None:
        return queue_row, readiness_row, False

    repaired = False
    try:
        if queue_row is None:
            db.add(_billing_queue_row(visit.tenant_id, existing_charge.charge_id))
            _flush_step(db, "insert_billing_queue")
            repaired = True
        if readiness_row is None:
            db.add(_claim_readiness_row(existing_charge.tenant_id, existing_charge.charge_id, ev))
            _flush_step(db, "insert_claim_readiness")
            repaired = True
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail=_safe_db_detail("commit_ensure_billing_queue_claim_readiness", e),
            ) from e
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_safe_db_detail("commit_ensure_billing_queue_claim_readiness", e),
            ) from e
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_safe_db_detail("ensure_billing_queue_claim_readiness", e),
        ) from e

    queue_row = db.scalar(select(BillingQueue).where(BillingQueue.charge_id == existing_charge.charge_id))
    readiness_row = db.scalar(
        select(ClaimReadiness).where(ClaimReadiness.charge_id == existing_charge.charge_id)
    )
    if queue_row is None or readiness_row is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="persist_queue_readiness: rows still missing after repair attempt.",
        )
    return queue_row, readiness_row, repaired


@router.post(
    "/{visit_id}/charges",
    response_model=ChargeWorkflowResult,
    status_code=status.HTTP_201_CREATED,
)
def create_charge_from_visit(
    visit_id: UUID,
    response: Response,
    db: Session = Depends(get_db),
) -> ChargeWorkflowResult:
    visit = db.get(ClinicalVisit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    first_dx, first_px, total_u, ev = _evaluate_visit_for_charge(db, visit_id)
    tu_dec = Decimal(str(total_u)) if total_u is not None else None

    existing_charge = db.scalar(
        select(Charge)
        .where(Charge.visit_id == visit_id)
        .order_by(Charge.created_at.desc())
        .limit(1)
    )

    if existing_charge is not None:
        queue_row, readiness_row, repaired = _ensure_queue_and_readiness(
            db, visit, existing_charge, ev
        )
        visit_completed = _mark_visit_charge_complete(db, visit_id)
        msg = (
            "Charge workflow already exists for this visit. Returning existing workflow."
            if not repaired
            else "Charge workflow already exists; created missing billing_queue or claim_readiness rows."
        )
        response.status_code = status.HTTP_200_OK
        return _charge_workflow_result(
            visit=visit_completed,
            charge=existing_charge,
            queue=queue_row,
            readiness=readiness_row,
            total_units=total_u,
            ev=ev,
            message=msg,
        )

    try:
        charge = Charge(
            tenant_id=visit.tenant_id,
            visit_id=visit_id,
            patient_id=visit.patient_id,
            provider_id=visit.provider_id,
            primary_icd10=first_dx.icd10_code if first_dx else None,
            primary_cpt=first_px.cpt_code if first_px else None,
            charge_status="SUBMITTED",
            total_units=tu_dec,
            charge_amount=Decimal("0"),
            ai_charge_suggested=False,
            documentation_support_status=ev.documentation_support_status,
        )
        db.add(charge)
        _flush_step(db, "insert_charge")

        db.add(_billing_queue_row(visit.tenant_id, charge.charge_id))
        _flush_step(db, "insert_billing_queue")

        db.add(_claim_readiness_row(visit.tenant_id, charge.charge_id, ev))
        _flush_step(db, "insert_claim_readiness")

        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            concurrent = db.scalar(
                select(Charge)
                .where(Charge.visit_id == visit_id)
                .order_by(Charge.created_at.desc())
                .limit(1)
            )
            if concurrent is not None:
                _, _, total_u2, ev2 = _evaluate_visit_for_charge(db, visit_id)
                queue_row, readiness_row, repaired = _ensure_queue_and_readiness(
                    db, visit, concurrent, ev2
                )
                visit_completed = _mark_visit_charge_complete(db, visit_id)
                msg = "Charge workflow already exists for this visit. Returning existing workflow."
                if repaired:
                    msg += " Repaired missing billing rows if needed."
                response.status_code = status.HTTP_200_OK
                return _charge_workflow_result(
                    visit=visit_completed,
                    charge=concurrent,
                    queue=queue_row,
                    readiness=readiness_row,
                    total_units=total_u2,
                    ev=ev2,
                    message=msg,
                )
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail=_safe_db_detail("commit_charge_workflow", e),
            ) from e
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=_safe_db_detail("commit_charge_workflow", e),
            ) from e
    except HTTPException:
        raise

    persisted = db.scalar(
        select(Charge).where(Charge.visit_id == visit_id).order_by(Charge.created_at.desc()).limit(1)
    )
    if persisted is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="insert_charge_workflow: charge not found.")

    queue_row = db.scalar(select(BillingQueue).where(BillingQueue.charge_id == persisted.charge_id))
    readiness_row = db.scalar(select(ClaimReadiness).where(ClaimReadiness.charge_id == persisted.charge_id))
    if queue_row is None or readiness_row is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="insert_charge_workflow: billing_queue or claim_readiness missing after commit.",
        )

    visit_completed = _mark_visit_charge_complete(db, visit_id)

    response.status_code = status.HTTP_201_CREATED
    return _charge_workflow_result(
        visit=visit_completed,
        charge=persisted,
        queue=queue_row,
        readiness=readiness_row,
        total_units=total_u,
        ev=ev,
        message=None,
    )
