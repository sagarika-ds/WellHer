import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CONTEXT_KEYS = ("cycle_summary", "symptom_summary", "lifestyle_summary", "mood_summary",
                "patterns", "deviations", "preferences")


class AISettingsOut(BaseModel):
    personalization_enabled: bool
    external_llm_allowed: bool
    context_allowlist: list[str]
    chat_retention_days: int


class AISettingsIn(BaseModel):
    personalization_enabled: bool
    external_llm_allowed: bool
    context_allowlist: list[Literal[CONTEXT_KEYS]] = Field(default_factory=list)  # type: ignore[valid-type]
    chat_retention_days: int = Field(ge=0, le=365)


class AccessHistoryItem(BaseModel):
    timestamp: datetime
    action: str
    resource: str | None
    outcome: str
    ip: str | None


class ExportOut(BaseModel):
    job_id: uuid.UUID
    status: Literal["ready"] = "ready"
    download_url: str | None = None
    data: dict


class DeleteAccountIn(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    confirm: Literal["DELETE"]
