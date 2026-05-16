from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment and optional `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Pydantic Settings maps env var DATABASE_URL -> database_url by default.
    database_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
