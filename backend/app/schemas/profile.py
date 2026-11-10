import json
import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ActivityLevel = Literal["sedentary", "light", "moderate", "active"]


class ProfileIn(BaseModel):
    date_of_birth: date | None = None
    height_cm: float | None = Field(default=None, ge=50, le=250)
    weight_kg: float | None = Field(default=None, ge=20, le=400)
    typical_cycle_length: int | None = Field(default=None, ge=15, le=90)
    contraceptive_use: bool | None = None
    conditions_self_reported: list[str] = Field(default_factory=list, max_length=30)
    activity_level: ActivityLevel | None = None
    dietary_prefs: list[str] = Field(default_factory=list, max_length=30)
    goals: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("date_of_birth")
    @classmethod
    def _dob(cls, v: date | None) -> date | None:
        if v is not None and not (date(1900, 1, 1) <= v <= date.today()):
            raise ValueError("date_of_birth out of range")
        return v

    @field_validator("conditions_self_reported", "dietary_prefs", "goals")
    @classmethod
    def _items(cls, v: list[str]) -> list[str]:
        out = [s.strip() for s in v if s.strip()]
        if any(len(s) > 80 for s in out):
            raise ValueError("items must be at most 80 characters")
        return out


class ProfileOut(BaseModel):
    user_id: uuid.UUID
    date_of_birth: date | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    typical_cycle_length: int | None = None
    contraceptive_use: bool | None = None
    conditions_self_reported: list[str] = []
    activity_level: str | None = None
    dietary_prefs: list[str] = []
    goals: list[str] = []

    @classmethod
    def from_model(cls, p) -> "ProfileOut":
        return cls(
            user_id=p.user_id, date_of_birth=p.date_of_birth,
            height_cm=float(p.height_cm) if p.height_cm is not None else None,
            weight_kg=float(p.weight_kg) if p.weight_kg is not None else None,
            typical_cycle_length=p.typical_cycle_length, contraceptive_use=p.contraceptive_use,
            conditions_self_reported=json.loads(p.conditions_self_reported or "[]"),
            activity_level=p.activity_level, dietary_prefs=p.dietary_prefs or [], goals=p.goals or [],
        )
