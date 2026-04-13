from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DEFAULT_SQLITE_URL = f"sqlite:///{(BACKEND_DIR / 'spaceiq.db').resolve().as_posix()}"



def _normalize_database_url(value: str) -> str:
    if not value.startswith("sqlite:///"):
        return value

    raw_path = value.replace("sqlite:///", "", 1)
    path = Path(raw_path)
    if path.is_absolute():
        return value
    return f"sqlite:///{(BACKEND_DIR / path).resolve().as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = DEFAULT_SQLITE_URL
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    groq_api_key: str = ""
    backend_url: str = "http://localhost:8000"

    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_email: str = ""
    smtp_password: str = ""
    owner_email: str = "kumarsoniravi705@gmail.com"
    owner_whatsapp_number: str = "9608710567"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""

    booking_mode: str = "request"
    real_payments_enabled: bool = False
    launch_min_verified_venues: int = 10
    launch_max_verified_venues: int = 25


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.database_url = _normalize_database_url(settings.database_url)
    return settings


settings = get_settings()
