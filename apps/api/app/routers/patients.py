from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.clinical import Patient
from app.models.core import Facility
from app.schemas.clinical import PatientDetailOut

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}", response_model=PatientDetailOut)
def get_patient(patient_id: UUID, db: Session = Depends(get_db)) -> PatientDetailOut:
    row = db.execute(
        select(Patient, Facility)
        .outerjoin(Facility, Patient.facility_id == Facility.facility_id)
        .where(Patient.patient_id == patient_id)
    ).one_or_none()

    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Patient not found")

    patient_db, facility_row = row[0], row[1]
    facility_name = facility_row.facility_name if facility_row is not None else None

    return PatientDetailOut.from_patient_and_facility(
        patient=patient_db,
        facility_name=facility_name,
    )
