from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.clinical import Patient
from app.models.core import Facility
from app.schemas.clinical import PatientDetailOut
from app.schemas.core import FacilitySummary

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}", response_model=PatientDetailOut)
def get_patient(patient_id: UUID, db: Session = Depends(get_db)) -> PatientDetailOut:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Patient not found")

    facility_summary: FacilitySummary | None = None
    if patient.facility_id is not None:
        facility = db.get(Facility, patient.facility_id)
        if facility is not None:
            facility_summary = FacilitySummary.model_validate(facility)

    return PatientDetailOut(
        patient_id=patient.id,
        tenant_id=patient.tenant_id,
        mrn=patient.mrn,
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        facility=facility_summary,
    )
