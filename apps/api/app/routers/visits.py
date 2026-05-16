from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.clinical import Patient, Visit, VisitDiagnosis, VisitNote, VisitProcedure
from app.models.core import Facility, User
from app.schemas.clinical import (
    DiagnosisCreate,
    ProcedureCreate,
    VisitCreate,
    VisitDetailOut,
    VisitDiagnosisOut,
    VisitNoteOut,
    VisitOut,
    VisitProcedureOut,
)

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=VisitOut, status_code=status.HTTP_201_CREATED)
def create_visit(
    body: VisitCreate,
    db: Session = Depends(get_db),
) -> Visit:
    facility = db.get(Facility, body.facility_id)
    patient = db.get(Patient, body.patient_id)
    provider = db.get(User, body.provider_id)

    if facility is None or facility.tenant_id != body.tenant_id or not facility.active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid facility")

    if patient is None or patient.tenant_id != body.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid patient")

    if provider is None or provider.tenant_id != body.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid provider")

    if patient.facility_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Patient must be attributed to a facility before creating a visit.",
        )

    if patient.facility_id != body.facility_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Patient is not attributed to this facility.",
        )

    visit = Visit(
        tenant_id=body.tenant_id,
        facility_id=body.facility_id,
        patient_id=body.patient_id,
        provider_id=body.provider_id,
        visit_type=body.visit_type,
        specialty=body.specialty,
        chief_complaint=body.chief_complaint,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


@router.get("/{visit_id}", response_model=VisitDetailOut)
def get_visit(visit_id: UUID, db: Session = Depends(get_db)) -> VisitDetailOut:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    diagnoses = list(
        db.scalars(
            select(VisitDiagnosis)
            .where(VisitDiagnosis.visit_id == visit_id)
            .order_by(VisitDiagnosis.created_at)
        )
    )
    procedures = list(
        db.scalars(
            select(VisitProcedure)
            .where(VisitProcedure.visit_id == visit_id)
            .order_by(VisitProcedure.created_at)
        )
    )
    notes = list(
        db.scalars(
            select(VisitNote).where(VisitNote.visit_id == visit_id).order_by(VisitNote.created_at)
        )
    )

    core = VisitOut.model_validate(visit)
    return VisitDetailOut(
        **core.model_dump(),
        diagnoses=[VisitDiagnosisOut.model_validate(d) for d in diagnoses],
        procedures=[VisitProcedureOut.model_validate(p) for p in procedures],
        notes=[VisitNoteOut.model_validate(n) for n in notes],
    )


@router.post(
    "/{visit_id}/diagnoses",
    response_model=VisitDiagnosisOut,
    status_code=status.HTTP_201_CREATED,
)
def add_visit_diagnosis(
    visit_id: UUID,
    body: DiagnosisCreate,
    db: Session = Depends(get_db),
) -> VisitDiagnosis:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    row = VisitDiagnosis(
        visit_id=visit_id,
        icd10_code=body.icd10_code.strip(),
        description=body.description.strip(),
        is_primary=body.is_primary,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post(
    "/{visit_id}/procedures",
    response_model=VisitProcedureOut,
    status_code=status.HTTP_201_CREATED,
)
def add_visit_procedure(
    visit_id: UUID,
    body: ProcedureCreate,
    db: Session = Depends(get_db),
) -> VisitProcedure:
    visit = db.get(Visit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    row = VisitProcedure(
        visit_id=visit_id,
        cpt_code=body.cpt_code.strip(),
        description=body.description.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
