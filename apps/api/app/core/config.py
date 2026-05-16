from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve `apps/api/.env` regardless of process cwd (run uvicorn from `apps/api`).
_API_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _API_ROOT / ".env"

load_dotenv(_ENV_FILE)


class Settings(BaseSettings):
    """Application settings: `apps/api/.env` plus process environment variables."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    app_env: str = Field(default="dev", alias="APP_ENV")


@lru_cache
def get_settings() -> Settings:
    return Settings()
