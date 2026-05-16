from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.db.database import get_db
from app.models.core import Facility, Tenant
from app.schemas.core import FacilityWithTenantOut

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=list[FacilityWithTenantOut])
def list_facilities(db: Session = Depends(get_db)) -> list[FacilityWithTenantOut]:
    stmt = (
        select(Facility, Tenant)
        .join(Tenant, Facility.tenant_id == Tenant.tenant_id)
        .where(Facility.status == "ACTIVE")
        .order_by(Facility.facility_name)
    )
    rows = db.execute(stmt).all()
    result: list[FacilityWithTenantOut] = []
    for facility, tenant in rows:
        result.append(
            FacilityWithTenantOut(
                facility_id=facility.facility_id,
                tenant_id=facility.tenant_id,
                tenant_name=tenant.tenant_name,
                facility_name=facility.facility_name,
                facility_type=facility.facility_type,
                address_line1=facility.address_line1,
                city=facility.city,
                state=facility.state,
                zip_code=facility.zip_code,
                status=facility.status,
            )
        )
    return result
