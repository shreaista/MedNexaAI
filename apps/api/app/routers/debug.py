"""Temporary diagnostics for database connectivity (remove when no longer needed)."""

from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db

router = APIRouter(tags=["debug"])


def _mask_database_url(url: str) -> str:
    """Return a copy of DATABASE_URL with password replaced by `***`."""
    try:
        p = urlparse(url)
        if not p.password and not p.username:
            return url
        host = p.hostname or ""
        port = f":{p.port}" if p.port else ""
        user = p.username or ""
        netloc = f"{user}:***@{host}{port}" if user else f"***@{host}{port}"
        return urlunparse(
            (
                p.scheme,
                netloc,
                p.path or "",
                p.params,
                p.query,
                p.fragment,
            )
        )
    except Exception:
        return "<redacted>"


@router.get("/db-info")
def debug_db_info(db: Session = Depends(get_db)) -> dict:
    """Inspect live DB connection — same engine/session as the rest of the API."""
    db_name = db.execute(text("SELECT current_database()")).scalar()
    schema = db.execute(text("SELECT current_schema()")).scalar()
    rows = db.execute(
        text(
            "SELECT tablename FROM pg_catalog.pg_tables "
            "WHERE schemaname = 'public' ORDER BY tablename"
        )
    ).fetchall()
    tables = [r[0] for r in rows]
    settings = get_settings()

    return {
        "current_database": db_name,
        "current_schema": schema,
        "public_tables": tables,
        "public_table_count": len(tables),
        "database_url_masked": _mask_database_url(settings.database_url),
        "app_env": settings.app_env,
    }
