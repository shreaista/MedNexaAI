from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.clinical import Patient
from app.models.core import Facility
from app.schemas.clinical import PatientDetailOut

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}", response_model=PatientDetailOut)
def get_patient(patient_id: UUID, db: Session = Depends(get_db)) -> PatientDetailOut:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Patient not found")

    facility_name: str | None = None
    if patient.facility_id is not None:
        facility = db.get(Facility, patient.facility_id)
        if facility is not None:
            facility_name = facility.facility_name

    return PatientDetailOut.from_patient_and_facility(
        patient=patient,
        facility_name=facility_name,
    )
