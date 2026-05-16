from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import tenant_query
from app.models.clinical import Patient
from app.models.core import Facility
from app.schemas.clinical import FacilitySummary, PatientDetailOut

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}", response_model=PatientDetailOut)
def get_patient(
    patient_id: UUID,
    tenant_id: UUID = Depends(tenant_query),
    db: Session = Depends(get_db),
) -> PatientDetailOut:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Patient not found")

    facility_summary: FacilitySummary | None = None
    if patient.facility_id is not None:
        facility = db.get(Facility, patient.facility_id)
        if facility is not None and facility.tenant_id == tenant_id:
            facility_summary = FacilitySummary.model_validate(facility)

    return PatientDetailOut(
        patient_id=patient.id,
        tenant_id=patient.tenant_id,
        external_id=patient.external_id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        birth_date=patient.birth_date,
        gender=patient.gender,
        active=patient.active,
        facility=facility_summary,
    )
