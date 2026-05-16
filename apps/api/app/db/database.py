"""Engine, session factory, and declarative Base."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy ORM base for existing `public` schema tables."""


_settings = get_settings()
engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
