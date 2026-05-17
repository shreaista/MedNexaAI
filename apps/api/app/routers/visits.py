from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.billing import Charge, ClaimReadiness
from app.models.clinical import (
    ClinicalVisit,
    Patient,
    VisitDiagnosis,
    VisitNote,
    VisitProcedure,
)
from app.models.core import Facility, Provider
from app.schemas.clinical import (
    ChargeDetailOut,
    ClaimReadinessBlockOut,
    DiagnosisCreate,
    DiagnosisCreatedOut,
    PatientBlockOut,
    ProcedureCreate,
    ProcedureCreatedOut,
    ProviderBlockOut,
    VisitBlockOut,
    VisitCreatedOut,
    VisitCreate,
    VisitDetailOut,
    VisitDiagnosisOut,
    VisitNoteOut,
    VisitProcedureOut,
)
from app.services.readiness_service import evaluate_charge_workflow

router = APIRouter(prefix="/visits", tags=["visits"])


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


@router.post("", response_model=VisitCreatedOut, status_code=status.HTTP_201_CREATED)
def create_visit(body: VisitCreate, db: Session = Depends(get_db)) -> VisitCreatedOut:
    facility = db.get(Facility, body.facility_id)
    patient = db.get(Patient, body.patient_id)
    provider = db.get(Provider, body.provider_id)

    if facility is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown facility_id for this request.")
    if facility.tenant_id != body.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Facility is not part of the specified tenant.")

    if facility.status != "ACTIVE":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Facility is not active.")

    if patient is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown patient_id.")
    if patient.tenant_id != body.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Patient is not part of the specified tenant.")

    if provider is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unknown provider_id.")
    if provider.tenant_id != body.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Provider is not part of the specified tenant.")

    if patient.facility_id is not None and patient.facility_id != body.facility_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Patient is not attributed to the selected facility.",
        )

    visit = ClinicalVisit(
        tenant_id=body.tenant_id,
        facility_id=body.facility_id,
        patient_id=body.patient_id,
        provider_id=body.provider_id,
        visit_type=body.visit_type,
        specialty=body.specialty,
        chief_complaint=body.chief_complaint,
        status="DRAFT",
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)

    return VisitCreatedOut(
        visit_id=visit.visit_id,
        visit_status=visit.status or "DRAFT",
        patient_id=visit.patient_id,
        provider_id=visit.provider_id,
    )


@router.get("/{visit_id}", response_model=VisitDetailOut)
def get_visit(visit_id: UUID, db: Session = Depends(get_db)) -> VisitDetailOut:
    visit = db.get(ClinicalVisit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    patient = db.get(Patient, visit.patient_id)
    provider = db.get(Provider, visit.provider_id)
    if patient is None or provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Related patient or provider missing")

    note = db.scalar(
        select(VisitNote)
        .where(VisitNote.visit_id == visit_id)
        .order_by(VisitNote.created_at.desc())
        .limit(1)
    )

    diagnoses = list(
        db.scalars(
            select(VisitDiagnosis)
            .where(VisitDiagnosis.visit_id == visit_id)
            .order_by(VisitDiagnosis.created_at.asc())
        )
    )
    procedures = list(
        db.scalars(
            select(VisitProcedure)
            .where(VisitProcedure.visit_id == visit_id)
            .order_by(VisitProcedure.created_at.asc())
        )
    )

    charge = db.scalar(
        select(Charge).where(Charge.visit_id == visit_id).order_by(Charge.created_at.desc()).limit(1)
    )
    readiness_row: ClaimReadiness | None = None
    if charge is not None:
        readiness_row = db.scalar(select(ClaimReadiness).where(ClaimReadiness.charge_id == charge.charge_id))

    has_signed = _count_signed_notes(db, visit_id) > 0
    has_any = _count_any_notes(db, visit_id) > 0
    has_dx = len(diagnoses) > 0
    has_px = len(procedures) > 0
    first_px = procedures[0] if procedures else None
    total_u = float(first_px.units) if first_px is not None else None
    doc_status = "SUPPORTED" if has_signed else "NEEDS_REVIEW"

    ev = evaluate_charge_workflow(
        has_signed_note=has_signed,
        has_any_note=has_any,
        has_diagnosis=has_dx,
        has_procedure=has_px,
    )

    charge_out: ChargeDetailOut | None = None
    if charge is not None:
        charge_out = ChargeDetailOut(
            charge_id=charge.charge_id,
            tenant_id=charge.tenant_id,
            visit_id=charge.visit_id,
            patient_id=charge.patient_id,
            facility_id=charge.facility_id,
            provider_id=charge.provider_id,
            charge_status=charge.charge_status,
            primary_icd10=charge.primary_icd10,
            primary_cpt=charge.primary_cpt,
            amount_cents=charge.amount_cents,
            total_units=total_u,
            documentation_support_status=doc_status,
        )

    cr_out: ClaimReadinessBlockOut | None = None
    if readiness_row is not None:
        cr_out = ClaimReadinessBlockOut(
            readiness_id=readiness_row.readiness_id,
            charge_id=readiness_row.charge_id,
            readiness_score=float(readiness_row.readiness_score),
            readiness_status=readiness_row.readiness_status,
            missing_note_flag=readiness_row.missing_note_flag,
            missing_diagnosis_flag=readiness_row.missing_diagnosis_flag,
            missing_cpt_flag=readiness_row.missing_cpt_flag,
            recommendation=ev.recommendation,
        )

    return VisitDetailOut(
        visit=VisitBlockOut.from_orm_visit(visit),
        patient=PatientBlockOut.from_patient(patient),
        provider=ProviderBlockOut(
            provider_id=provider.provider_id,
            tenant_id=provider.tenant_id,
            full_name=provider.full_name,
            user_id=provider.user_id,
        ),
        note=VisitNoteOut.model_validate(note) if note else None,
        diagnoses=[VisitDiagnosisOut.model_validate(d) for d in diagnoses],
        procedures=[VisitProcedureOut.model_validate(p) for p in procedures],
        charge=charge_out,
        claim_readiness=cr_out,
    )


@router.post(
    "/{visit_id}/diagnoses",
    response_model=DiagnosisCreatedOut,
    status_code=status.HTTP_201_CREATED,
)
def add_visit_diagnosis(
    visit_id: UUID,
    body: DiagnosisCreate,
    db: Session = Depends(get_db),
) -> DiagnosisCreatedOut:
    visit = db.get(ClinicalVisit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    if body.tenant_id != visit.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Tenant mismatch for visit")

    conf = float(body.confidence_score) if body.confidence_score is not None else None

    row = VisitDiagnosis(
        visit_id=visit_id,
        tenant_id=body.tenant_id,
        icd10_code=body.icd10_code.strip(),
        description=body.description.strip() if body.description else None,
        is_ai_suggested=body.is_ai_suggested,
        confidence_score=conf,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return DiagnosisCreatedOut(diagnosis_id=row.diagnosis_id)


@router.post(
    "/{visit_id}/procedures",
    response_model=ProcedureCreatedOut,
    status_code=status.HTTP_201_CREATED,
)
def add_visit_procedure(
    visit_id: UUID,
    body: ProcedureCreate,
    db: Session = Depends(get_db),
) -> ProcedureCreatedOut:
    visit = db.get(ClinicalVisit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    if body.tenant_id != visit.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Tenant mismatch for visit")

    conf = float(body.confidence_score) if body.confidence_score is not None else None

    row = VisitProcedure(
        visit_id=visit_id,
        tenant_id=body.tenant_id,
        cpt_code=body.cpt_code.strip(),
        description=body.description.strip() if body.description else None,
        modifier=body.modifier.strip() if body.modifier else None,
        units=float(body.units),
        is_ai_suggested=body.is_ai_suggested,
        confidence_score=conf,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ProcedureCreatedOut(procedure_id=row.procedure_id)
