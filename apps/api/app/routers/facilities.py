from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import tenant_query
from app.models.core import Facility
from app.schemas.core import FacilityOut

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=list[FacilityOut])
def list_facilities(
    tenant_id: UUID = Depends(tenant_query),
    db: Session = Depends(get_db),
) -> list[Facility]:
    stmt = (
        select(Facility)
        .where(Facility.tenant_id == tenant_id)
        .where(Facility.active.is_(True))
        .order_by(Facility.name)
    )
    return list(db.scalars(stmt))
