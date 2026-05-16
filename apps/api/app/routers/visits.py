from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.billing import Charge
from app.models.clinical import (
    ClinicalVisit,
    Patient,
    VisitDiagnosis,
    VisitNote,
    VisitProcedure,
)
from app.models.core import Facility, Provider
from app.schemas.clinical import (
    ChargeSummary,
    DiagnosisCreate,
    PatientSummary,
    ProcedureCreate,
    ProviderSummary,
    VisitCreate,
    VisitDetailOut,
    VisitDiagnosisOut,
    VisitNoteOut,
    VisitProcedureOut,
    VisitSummary,
)

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=VisitSummary, status_code=status.HTTP_201_CREATED)
def create_visit(body: VisitCreate, db: Session = Depends(get_db)) -> ClinicalVisit:
    facility = db.get(Facility, body.facility_id)
    patient = db.get(Patient, body.patient_id)
    provider = db.get(Provider, body.provider_id)

    if facility is None or facility.tenant_id != body.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid facility for tenant")

    if facility.status != "ACTIVE":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Facility is not active")

    if patient is None or patient.tenant_id != body.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid patient for tenant")

    if provider is None or provider.tenant_id != body.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid provider for tenant")

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
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


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

    return VisitDetailOut(
        visit=VisitSummary.model_validate(visit),
        patient=PatientSummary.model_validate(patient),
        provider=ProviderSummary.model_validate(provider),
        note=VisitNoteOut.model_validate(note) if note else None,
        diagnoses=[VisitDiagnosisOut.model_validate(d) for d in diagnoses],
        procedures=[VisitProcedureOut.model_validate(p) for p in procedures],
        charge=ChargeSummary.model_validate(charge) if charge else None,
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
    visit = db.get(ClinicalVisit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    if body.tenant_id != visit.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Tenant mismatch for visit")

    row = VisitDiagnosis(
        visit_id=visit_id,
        tenant_id=body.tenant_id,
        icd10_code=body.icd10_code.strip(),
        description=body.description.strip() if body.description else None,
        is_ai_suggested=body.is_ai_suggested,
        confidence_score=body.confidence_score,
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
    visit = db.get(ClinicalVisit, visit_id)
    if visit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Visit not found")

    if body.tenant_id != visit.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Tenant mismatch for visit")

    row = VisitProcedure(
        visit_id=visit_id,
        tenant_id=body.tenant_id,
        cpt_code=body.cpt_code.strip(),
        description=body.description.strip() if body.description else None,
        modifier=body.modifier.strip() if body.modifier else None,
        units=float(body.units),
        is_ai_suggested=body.is_ai_suggested,
        confidence_score=body.confidence_score,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
