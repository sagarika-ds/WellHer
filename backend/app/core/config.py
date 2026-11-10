"""Application settings. Everything comes from environment variables; nothing is hard-coded."""
import base64
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = Field(default=15, ge=1, le=120)
    jwt_refresh_ttl_days: int = Field(default=30, ge=1, le=90)
    field_encryption_key: str  # base64 of exactly 32 random bytes

    cors_origins: str = ""
    login_max_attempts: int = Field(default=5, ge=1)
    login_window_seconds: int = Field(default=900, ge=1)
    password_reset_ttl_min: int = Field(default=30, ge=5, le=240)
    consent_version: str = "2026-11-v1"

    # Event pipeline: inline=True runs handlers in-process (tests/dev); False enqueues to ARQ.
    events_inline: bool = False
    email_backend: str = "console"  # console | disabled (SMTP is not implemented yet)

    @field_validator("field_encryption_key")
    @classmethod
    def _key_is_32_bytes(cls, v: str) -> str:
        try:
            raw = base64.b64decode(v, validate=True)
        except Exception as exc:
            raise ValueError("FIELD_ENCRYPTION_KEY must be base64") from exc
        if len(raw) != 32:
            raise ValueError("FIELD_ENCRYPTION_KEY must decode to exactly 32 bytes")
        return v

    @model_validator(mode="after")
    def _no_placeholders_in_production(self) -> "Settings":
        if self.app_env == "production":
            if "CHANGE_ME" in self.jwt_secret or "CHANGE_ME" in self.database_url:
                raise ValueError("placeholder secrets are not allowed in production")
            if self.events_inline:
                raise ValueError("EVENTS_INLINE must be false in production")
            if self.email_backend == "console":
                raise ValueError("EMAIL_BACKEND=console is not allowed in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
