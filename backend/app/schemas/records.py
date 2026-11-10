import uuid
from datetime import UTC, date, datetime, timedelta

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.ontology import SYMPTOM_CODES
from app.schemas.common import ORMModel, Score5


def _aware(v: datetime) -> datetime:
    if v.tzinfo is None:
        raise ValueError("timestamp must include a timezone offset")
    if v > datetime.now(UTC) + timedelta(minutes=5):
        raise ValueError("timestamp must not be in the future")
    return v


class CycleIn(BaseModel):
    start_date: date
    end_date: date | None = None
    flow_intensity: Score5 | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _dates(self) -> "CycleIn":
        if self.start_date > date.today() + timedelta(days=1):
            raise ValueError("start_date must not be in the future")
        if self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("end_date must not be before start_date")
            if (self.end_date - self.start_date).days > 21:
                raise ValueError("a period longer than 21 days looks like a data-entry error")
        return self


class CycleOut(BaseModel):
    id: uuid.UUID
    start_date: date
    end_date: date | None
    cycle_length_days: int | None
    flow_intensity: int | None
    notes: str | None


class CycleStats(BaseModel):
    n_cycles: int
    mean_length: float | None
    std_length: float | None
    min: int | None
    max: int | None


class SymptomIn(BaseModel):
    logged_at: datetime
    symptom_code: str
    severity: Score5
    cycle_id: uuid.UUID | None = None

    _t = field_validator("logged_at")(_aware)

    @field_validator("symptom_code")
    @classmethod
    def _code(cls, v: str) -> str:
        if v not in SYMPTOM_CODES:
            raise ValueError(f"unknown symptom_code; allowed: {sorted(SYMPTOM_CODES)}")
        return v


class SymptomOut(ORMModel):
    id: uuid.UUID
    logged_at: datetime
    symptom_code: str
    severity: int
    cycle_id: uuid.UUID | None


class LifestyleIn(BaseModel):
    date: date
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    sleep_quality: Score5 | None = None
    activity_minutes: int | None = Field(default=None, ge=0, le=1440)
    water_ml: int | None = Field(default=None, ge=0, le=20000)
    stress_level: Score5 | None = None
    nutrition_notes: str | None = Field(default=None, max_length=2000)

    @field_validator("date")
    @classmethod
    def _d(cls, v: date) -> date:
        if v > date.today() + timedelta(days=1):
            raise ValueError("date must not be in the future")
        return v


class LifestyleOut(BaseModel):
    id: uuid.UUID
    date: date
    sleep_hours: float | None
    sleep_quality: int | None
    activity_minutes: int | None
    water_ml: int | None
    stress_level: int | None


class LifestyleSummary(BaseModel):
    period_days: int
    n_entries: int
    avg_sleep_hours: float | None
    avg_activity_minutes: float | None
    avg_stress: float | None


class MoodIn(BaseModel):
    logged_at: datetime
    mood_score: Score5
    tags: list[str] = Field(default_factory=list, max_length=10)

    _t = field_validator("logged_at")(_aware)

    @field_validator("tags")
    @classmethod
    def _tags(cls, v: list[str]) -> list[str]:
        out = [t.strip().lower() for t in v if t.strip()]
        if any(len(t) > 30 for t in out):
            raise ValueError("tags must be at most 30 characters")
        return out


class MoodOut(ORMModel):
    id: uuid.UUID
    logged_at: datetime
    mood_score: int
    tags: list[str]
