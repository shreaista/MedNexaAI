from uuid import UUID

from fastapi import Query

from app.core.config import DEMO_TENANT_ID


def tenant_query(
    tenant_id: UUID | None = Query(
        None,
        description=(
            "Tenant scope for read APIs. Omit to use the seeded demo tenant "
            f"({DEMO_TENANT_ID})."
        ),
    ),
) -> UUID:
    """Resolve tenant scope for endpoints that still run without JWT auth."""
    return tenant_id or DEMO_TENANT_ID
