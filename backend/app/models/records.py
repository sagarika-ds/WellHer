import uuid
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
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
from app.db.base import Base, IdMixin, TimestampMixin


def _user_fk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class CycleRecord(Base, IdMixin, TimestampMixin):
    __tablename__ = "cycle_records"
    user_id: Mapped[uuid.UUID] = _user_fk()
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    flow_intensity: Mapped[int | None] = mapped_column(SmallInteger)
    notes: Mapped[str | None] = mapped_column(EncryptedText())
    __table_args__ = (
        UniqueConstraint("user_id", "start_date"),
        CheckConstraint("end_date is null or end_date >= start_date", name="end_after_start"),
        CheckConstraint("flow_intensity is null or flow_intensity between 1 and 5", name="flow_range"),
        Index("ix_cycle_records_user_id_start_date_desc", "user_id", text("start_date DESC")),
    )


class SymptomLog(Base, IdMixin, TimestampMixin):
    __tablename__ = "symptom_logs"
    user_id: Mapped[uuid.UUID] = _user_fk()
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    symptom_code: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cycle_records.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(String(15), nullable=False, server_default="manual")
    __table_args__ = (
        CheckConstraint("severity between 1 and 5", name="severity_range"),
        CheckConstraint("source in ('manual','conversation','import')", name="source_valid"),
        Index("ix_symptom_logs_user_id_logged_at_desc", "user_id", text("logged_at DESC")),
    )


class LifestyleRecord(Base, IdMixin, TimestampMixin):
    __tablename__ = "lifestyle_records"
    user_id: Mapped[uuid.UUID] = _user_fk()
    date: Mapped[date] = mapped_column(Date, nullable=False)
    sleep_hours: Mapped[float | None] = mapped_column(Numeric(4, 2))
    sleep_quality: Mapped[int | None] = mapped_column(SmallInteger)
    activity_minutes: Mapped[int | None] = mapped_column(Integer)
    water_ml: Mapped[int | None] = mapped_column(Integer)
    stress_level: Mapped[int | None] = mapped_column(SmallInteger)
    nutrition_notes: Mapped[str | None] = mapped_column(EncryptedText())
    __table_args__ = (
        UniqueConstraint("user_id", "date"),
        CheckConstraint("sleep_hours is null or sleep_hours between 0 and 24", name="sleep_range"),
        CheckConstraint("sleep_quality is null or sleep_quality between 1 and 5", name="sleepq_range"),
        CheckConstraint("stress_level is null or stress_level between 1 and 5", name="stress_range"),
        CheckConstraint("activity_minutes is null or activity_minutes between 0 and 1440",
                        name="activity_range"),
        CheckConstraint("water_ml is null or water_ml between 0 and 20000", name="water_range"),
        Index("ix_lifestyle_records_user_id_date_desc", "user_id", text("date DESC")),
    )


class MoodRecord(Base, IdMixin, TimestampMixin):
    __tablename__ = "mood_records"
    user_id: Mapped[uuid.UUID] = _user_fk()
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mood_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"))
    __table_args__ = (
        CheckConstraint("mood_score between 1 and 5", name="mood_range"),
        Index("ix_mood_records_user_id_logged_at_desc", "user_id", text("logged_at DESC")),
    )


class TimelineEvent(Base, IdMixin):
    """Derived read model written in the same transaction as the source record."""
    __tablename__ = "timeline_events"
    user_id: Mapped[uuid.UUID] = _user_fk()
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    source_table: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("source_table", "source_id"),
        Index("ix_timeline_events_user_id_occurred_at_desc", "user_id", text("occurred_at DESC")),
    )


class PipelineRun(Base, IdMixin):
    """One row per (event, handler): makes the event pipeline idempotent and observable."""
    __tablename__ = "pipeline_runs"
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    user_id: Mapped[uuid.UUID] = _user_fk()
    handler: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("event_id", "handler"),
        CheckConstraint("status in ('running','done','failed')", name="status_valid"),
    )


_ = (JSONB,)  # keep import used if columns change
