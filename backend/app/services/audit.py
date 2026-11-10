"""Audit trail. Uses its OWN session/transaction so failures (e.g. rejected logins) are recorded
even when the request transaction rolls back. The table is append-only (DB trigger)."""
import logging
import uuid
from typing import Any

from app.core.context import RequestContext
from app.db.session import get_sessionmaker
from app.models import AuditLog
from app.repositories.identity import AuditRepo

log = logging.getLogger("app.audit")


class AuditService:
    async def record(self, action: str, ctx: RequestContext | None = None, *,
                     user_id: uuid.UUID | None = None, resource: str | None = None,
                     resource_id: str | None = None, outcome: str = "success",
                     details: dict[str, Any] | None = None) -> None:
        uid = user_id if user_id is not None else (ctx.user_id if ctx else None)
        row = AuditLog(
            user_id=uid, action=action, resource=resource, resource_id=resource_id,
            outcome=outcome, ip=ctx.ip if ctx else None,
            user_agent=(ctx.user_agent or "")[:255] if ctx else None,
            request_id=ctx.request_id if ctx else None, details=details)
        try:
            async with get_sessionmaker()() as s:
                await AuditRepo(s).add(row)
                await s.commit()
        except Exception:  # auditing must never break the request, but the failure must be loud
            log.exception("AUDIT WRITE FAILED action=%s", action)
