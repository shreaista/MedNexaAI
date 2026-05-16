from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.clinical import Patient, PatientCensus
from app.models.core import Facility
from app.schemas.core import CensusRowOut

router = APIRouter(prefix="/facilities", tags=["census"])


def _compose_patient_name(first: str | None, last: str | None) -> str | None:
    fn = (first or "").strip()
    ln = (last or "").strip()
    if not fn and not ln:
        return None
    return f"{fn} {ln}".strip()


@router.get("/{facility_id}/census", response_model=list[CensusRowOut])
def get_facility_census(
    facility_id: UUID,
    db: Session = Depends(get_db),
) -> list[CensusRowOut]:
    facility = db.get(Facility, facility_id)
    if facility is None or facility.status != "ACTIVE":
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Facility not found")

    stmt = (
        select(PatientCensus, Patient)
        .join(Patient, PatientCensus.patient_id == Patient.patient_id)
        .where(PatientCensus.facility_id == facility_id)
        .order_by(Patient.last_name, Patient.first_name)
    )
    rows = db.execute(stmt).all()

    return [
        CensusRowOut(
            census_id=census.census_id,
            facility_id=census.facility_id,
            patient_id=patient.patient_id,
            mrn=patient.mrn,
            patient_name=_compose_patient_name(patient.first_name, patient.last_name),
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            gender=patient.gender,
            payer_name=patient.payer_name,
            insurance_member_id=patient.insurance_member_id,
            room_number=census.room_number,
            bed_number=census.bed_number,
            care_level=census.care_level,
            visit_due_flag=census.visit_due_flag,
            unsigned_note_flag=census.unsigned_note_flag,
            missing_charge_flag=census.missing_charge_flag,
            status=census.status,
        )
        for census, patient in rows
    ]
