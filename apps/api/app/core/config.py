from functools import lru_cache
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://mednexa:mednexa_local_dev@localhost:5432/mednexa"
    api_env: str = "development"
    log_level: str = "info"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Stable demo tenant from seed data (core.tenants.slug = 'demo-org')
DEMO_TENANT_ID: UUID = UUID("11111111-1111-1111-1111-111111111111")
