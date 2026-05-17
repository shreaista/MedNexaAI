from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
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
    cors_allow_origins: str = Field(
        default=(
            "http://localhost:3000,"
            "http://127.0.0.1:3000,"
            "https://mednexa-web-dev.salmoncoast-083126b7.centralus.azurecontainerapps.io"
        ),
        validation_alias=AliasChoices("CORS_ORIGINS", "CORS_ALLOW_ORIGINS"),
        description=(
            "Comma-separated allowed browser origins. "
            "Set CORS_ORIGINS (or legacy CORS_ALLOW_ORIGINS) to override the default list."
        ),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
