"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    upload_dir: Path = Field(default=Path("uploads"), validation_alias="UPLOAD_DIR")
    max_upload_mb: int = Field(default=50, validation_alias="MAX_UPLOAD_MB")
    database_url: str = Field(
        default="sqlite:///./geo_measure.db", validation_alias="DATABASE_URL"
    )
    cors_origins: str = Field(default="", validation_alias="CORS_ORIGINS")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def max_upload_bytes(self) -> int:
        """Return the configured upload size limit in bytes."""

        return self.max_upload_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        """Return configured CORS origins as a list."""

        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()

