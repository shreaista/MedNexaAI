"""Provider directory — active providers with user display names."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.core import Provider, User
from app.schemas.core import ProviderListItem

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderListItem])
def list_providers(
    tenant_id: UUID | None = Query(
        default=None,
        description="When set, returns only providers for this tenant.",
    ),
    db: Session = Depends(get_db),
) -> list[ProviderListItem]:
    """List active providers; `full_name` prefers `users.full_name`, else `providers.full_name`."""
    display_name = func.coalesce(User.full_name, Provider.full_name)
    stmt = (
        select(
            Provider.provider_id,
            Provider.tenant_id,
            Provider.user_id,
            display_name.label("full_name"),
            Provider.npi,
            Provider.specialty,
            Provider.provider_type,
            Provider.status,
        )
        .select_from(Provider)
        .outerjoin(User, Provider.user_id == User.user_id)
        .where(func.upper(Provider.status) == "ACTIVE")
        .order_by(display_name.asc())
    )
    if tenant_id is not None:
        stmt = stmt.where(Provider.tenant_id == tenant_id)

    rows = db.execute(stmt).mappings().all()
    return [ProviderListItem.model_validate(dict(r)) for r in rows]
