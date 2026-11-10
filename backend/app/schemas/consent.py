from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ConsentSet(BaseModel):
    granted: bool


class ConsentOut(ORMModel):
    purpose: str
    granted: bool
    version: str
    granted_at: datetime | None = None
    revoked_at: datetime | None = None
