from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


def _normalize_database_url(value: str) -> str:
    if value.startswith("sqlite:///"):
        return value.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return value


def _looks_configured(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return False
    return not any(
        marker in normalized
        for marker in (
            "replace",
            "changeme",
            "example",
            "your_",
            "your-",
            "your ",
            "test_your",
        )
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "SpaceBook API"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api"

    database_url: str = Field(default="sqlite:///./spaceiq.db")
    secret_key: str = Field(
        default="replace-with-a-strong-secret",
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"),
    )
    algorithm: str = Field(default="HS256", validation_alias=AliasChoices("ALGORITHM", "JWT_ALGORITHM"))
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 14

    frontend_url: str = "http://localhost:3000"
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    google_places_api_key: str = ""
    google_oauth_client_id: str = ""
    next_public_google_maps_key: str = ""

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    next_public_razorpay_key_id: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    redis_url: str = ""
    hold_duration_seconds: int = 300
    slot_sweep_interval_seconds: int = 60

    chat_rate_limit: str = "15/minute"
    payment_rate_limit: str = "10/minute"

    log_level: str = "INFO"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return ["http://localhost:3000"]
        return [item.strip() for item in str(value).split(",") if item.strip()]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        return str(value).strip().lower() in {"1", "true", "yes", "on", "debug"}

    @property
    def sync_database_url(self) -> str:
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("sqlite+aiosqlite:///"):
            return self.database_url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
        return self.database_url

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def razorpay_enabled(self) -> bool:
        return _looks_configured(self.razorpay_key_id) and _looks_configured(self.razorpay_key_secret)

    @property
    def google_places_enabled(self) -> bool:
        return _looks_configured(self.google_places_api_key)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.database_url = _normalize_database_url(settings.database_url)
    return settings


settings = get_settings()
