import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models import HealthProfile
from app.repositories.identity import ProfileRepo
from app.schemas.profile import ProfileIn
from app.services.audit import AuditService


class ProfileService:
    def __init__(self, session: AsyncSession, audit: AuditService | None = None) -> None:
        self.s, self.repo, self.audit = session, ProfileRepo(session), audit or AuditService()

    async def get(self, user_id: uuid.UUID, ctx: RequestContext) -> HealthProfile:
        p = await self.repo.get(user_id) or await self.repo.add(HealthProfile(user_id=user_id))
        await self.audit.record("read", ctx, resource="health_profile")
        return p

    async def update(self, user_id: uuid.UUID, data: ProfileIn, ctx: RequestContext) -> HealthProfile:
        p = await self.repo.get(user_id) or await self.repo.add(HealthProfile(user_id=user_id))
        d = data.model_dump()
        p.conditions_self_reported = json.dumps(d.pop("conditions_self_reported"))
        for k, v in d.items():
            setattr(p, k, v)
        await self.s.commit()
        await self.audit.record("update", ctx, resource="health_profile")
        return p
