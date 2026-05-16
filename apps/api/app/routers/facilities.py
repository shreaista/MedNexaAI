from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.db.database import get_db
from app.models.core import Facility, Tenant
from app.schemas.core import FacilityWithTenantOut, TenantSummary

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=list[FacilityWithTenantOut])
def list_facilities(db: Session = Depends(get_db)) -> list[FacilityWithTenantOut]:
    stmt = (
        select(Facility, Tenant)
        .join(Tenant, Facility.tenant_id == Tenant.id)
        .where(Facility.status == "ACTIVE")
        .order_by(Facility.name)
    )
    rows = db.execute(stmt).all()
    result: list[FacilityWithTenantOut] = []
    for facility, tenant in rows:
        result.append(
            FacilityWithTenantOut(
                id=facility.id,
                tenant_id=facility.tenant_id,
                code=facility.code,
                name=facility.name,
                status=facility.status,
                created_at=facility.created_at,
                updated_at=facility.updated_at,
                tenant=TenantSummary.model_validate(tenant),
            )
        )
    return result
