from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import tenant_query
from app.models.clinical import Patient
from app.models.core import Facility
from app.schemas.core import CensusPatientOut

router = APIRouter(prefix="/facilities", tags=["census"])


@router.get("/{facility_id}/census", response_model=list[CensusPatientOut])
def get_facility_census(
    facility_id: UUID,
    tenant_id: UUID = Depends(tenant_query),
    db: Session = Depends(get_db),
) -> list[Patient]:
    facility = db.get(Facility, facility_id)
    if facility is None or facility.tenant_id != tenant_id or not facility.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Facility not found")

    stmt = (
        select(Patient)
        .where(Patient.facility_id == facility_id)
        .where(Patient.active.is_(True))
        .order_by(Patient.last_name, Patient.first_name)
    )
    return list(db.scalars(stmt))
