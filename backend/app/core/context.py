import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestContext:
    user_id: uuid.UUID | None
    ip: str | None
    user_agent: str | None
    request_id: str | None
