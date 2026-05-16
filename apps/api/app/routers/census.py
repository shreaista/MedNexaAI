from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.clinical import PatientCensus
from app.models.core import Facility
from app.schemas.core import CensusRowOut

router = APIRouter(prefix="/facilities", tags=["census"])


@router.get("/{facility_id}/census", response_model=list[CensusRowOut])
def get_facility_census(
    facility_id: UUID,
    db: Session = Depends(get_db),
) -> list[CensusRowOut]:
    facility = db.get(Facility, facility_id)
    if facility is None or facility.status != "ACTIVE":
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Facility not found")

    stmt = (
        select(PatientCensus)
        .where(PatientCensus.facility_id == facility_id)
        .order_by(PatientCensus.patient_name)
    )
    rows = list(db.scalars(stmt))

    return [
        CensusRowOut(
            census_id=row.id,
            patient_id=row.patient_id,
            mrn=row.mrn,
            patient_name=row.patient_name,
            date_of_birth=row.date_of_birth.isoformat() if row.date_of_birth else None,
            gender=row.gender,
            payer_name=row.payer_name,
            room_number=row.room_number,
            bed_number=row.bed_number,
            care_level=row.care_level,
            visit_due_flag=row.visit_due_flag,
            unsigned_note_flag=row.unsigned_note_flag,
            missing_charge_flag=row.missing_charge_flag,
        )
        for row in rows
    ]
