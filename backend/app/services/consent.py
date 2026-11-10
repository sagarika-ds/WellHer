import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.context import RequestContext
from app.models import UserConsent
from app.models.identity import CONSENT_PURPOSES
from app.repositories.identity import ConsentRepo
from app.services.audit import AuditService


class ConsentService:
    def __init__(self, session: AsyncSession, audit: AuditService | None = None) -> None:
        self.s, self.repo, self.audit = session, ConsentRepo(session), audit or AuditService()

    async def ensure_defaults(self, user_id: uuid.UUID, choices: dict[str, bool]) -> None:
        """Create one row per purpose (all explicit; default = not granted)."""
        version, now = get_settings().consent_version, datetime.now(UTC)
        for purpose in CONSENT_PURPOSES:
            granted = choices.get(purpose, False)
            await self.repo.add(UserConsent(
                user_id=user_id, purpose=purpose, granted=granted, version=version,
                granted_at=now if granted else None))

    async def list(self, user_id: uuid.UUID) -> list[UserConsent]:
        return await self.repo.list(user_id)

    async def is_granted(self, user_id: uuid.UUID, purpose: str) -> bool:
        c = await self.repo.get(user_id, purpose)
        return bool(c and c.granted)

    async def set(self, user_id: uuid.UUID, purpose: str, granted: bool,
                  ctx: RequestContext) -> UserConsent:
        c = await self.repo.get(user_id, purpose)
        if c is None:  # defensive: should exist from registration
            c = await self.repo.add(UserConsent(
                user_id=user_id, purpose=purpose, granted=False, version=get_settings().consent_version))
        now = datetime.now(UTC)
        changed = c.granted != granted
        c.granted, c.version = granted, get_settings().consent_version
        if granted:
            c.granted_at, c.revoked_at = now, None
        else:
            c.revoked_at = now
        await self.s.commit()
        await self.audit.record("consent_granted" if granted else "consent_revoked", ctx,
                                resource="consent", resource_id=purpose,
                                details={"purpose": purpose, "version": c.version, "changed": changed})
        return c
