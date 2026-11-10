import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import EncryptedText
from app.db.base import Base, CIText, IdMixin, TimestampMixin

CONSENT_PURPOSES = ("health_tracking", "ml_processing", "llm_external", "analytics")


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(CIText(), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    __table_args__ = (CheckConstraint("role in ('user','admin')", name="role_valid"),)


class HealthProfile(Base, TimestampMixin):
    __tablename__ = "health_profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    typical_cycle_length: Mapped[int | None] = mapped_column(SmallInteger)
    contraceptive_use: Mapped[bool | None] = mapped_column(Boolean)
    conditions_self_reported: Mapped[str | None] = mapped_column(EncryptedText())  # JSON list, encrypted
    activity_level: Mapped[str | None] = mapped_column(String(20))
    dietary_prefs: Mapped[list | None] = mapped_column(JSONB)
    goals: Mapped[list | None] = mapped_column(JSONB)
    __table_args__ = (
        CheckConstraint("height_cm is null or height_cm between 50 and 250", name="height_range"),
        CheckConstraint("weight_kg is null or weight_kg between 20 and 400", name="weight_range"),
        CheckConstraint("typical_cycle_length is null or typical_cycle_length between 15 and 90",
                        name="cycle_len_range"),
    )


class RefreshToken(Base, IdMixin):
    """Opaque rotating refresh tokens, stored as SHA-256 hashes. family_id == access-token `sid`."""
    __tablename__ = "refresh_tokens"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    device: Mapped[str | None] = mapped_column(String(100))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (Index("ix_refresh_tokens_user_id_family_id", "user_id", "family_id"),)


class PasswordResetToken(Base, IdMixin):
    __tablename__ = "password_reset_tokens"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserConsent(Base, IdMixin, TimestampMixin):
    """Current consent state per purpose. History of changes lives in audit_logs."""
    __tablename__ = "user_consents"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("user_id", "purpose"),
        CheckConstraint("purpose in " + str(CONSENT_PURPOSES), name="purpose_valid"),
    )


class AuditLog(Base, IdMixin):
    """Append-only (enforced by a database trigger). user_id is nulled, not deleted, on account erasure."""
    __tablename__ = "audit_logs"
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(60))
    resource_id: Mapped[str | None] = mapped_column(String(64))
    outcome: Mapped[str] = mapped_column(String(10), nullable=False, server_default="success")
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    request_id: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict | None] = mapped_column(JSONB)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (Index("ix_audit_logs_user_id_occurred_at", "user_id", text("occurred_at DESC")),)


class AISettings(Base, TimestampMixin):
    __tablename__ = "ai_settings"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    personalization_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"))
    external_llm_allowed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"))
    context_allowlist: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'"))
    chat_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    __table_args__ = (CheckConstraint("chat_retention_days between 0 and 365", name="retention_range"),)
