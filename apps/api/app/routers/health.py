"""Operational health endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health() -> dict[str, str]:
    """Service health check."""
    return {"status": "ok", "service": "mednexa-api"}
