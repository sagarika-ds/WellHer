import asyncio
import hashlib
import uuid
from datetime import date, datetime
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.context import RequestContext
from app.core.exceptions import AppError, consent_required
from app.core.security import verify_password
from app.events.handlers import dashboard_cache_key
from app.models import AISettings, AuditLog, User
from app.repositories.identity import AISettingsRepo, AuditRepo, ConsentRepo, ProfileRepo
from app.repositories.records import CycleRepo, LifestyleRepo, MoodRepo, SymptomRepo
from app.schemas.privacy import AISettingsIn
from app.schemas.profile import ProfileOut
from app.services.audit import AuditService
from app.services.auth import AuthService
from app.services.consent import ConsentService

EXPORT_LIMIT = 100_000


def _iso(v: Any) -> Any:
    return v.isoformat() if isinstance(v, date | datetime) else v


class PrivacyService:
    def __init__(self, session: AsyncSession, redis: Redis, settings: Settings,
                 audit: AuditService | None = None) -> None:
        self.s, self.redis, self.cfg = session, redis, settings
        self.audit = audit or AuditService()

    # ---- AI settings ----
    async def get_ai_settings(self, user_id: uuid.UUID) -> AISettings:
        repo = AISettingsRepo(self.s)
        a = await repo.get(user_id)
        if a is None:
            a = await repo.add(AISettings(user_id=user_id, context_allowlist=[]))
            await self.s.commit()
        return a

    async def update_ai_settings(self, user_id: uuid.UUID, data: AISettingsIn,
                                 ctx: RequestContext) -> AISettings:
        if data.external_llm_allowed and not await ConsentService(self.s).is_granted(
                user_id, "llm_external"):
            raise consent_required("llm_external")
        a = await self.get_ai_settings(user_id)
        a.personalization_enabled = data.personalization_enabled
        a.external_llm_allowed = data.external_llm_allowed
        a.context_allowlist = sorted(set(data.context_allowlist))
        a.chat_retention_days = data.chat_retention_days
        await self.s.commit()
        await self.audit.record("ai_settings_update", ctx, resource="ai_settings", details={
            "external_llm_allowed": a.external_llm_allowed, "allowlist": a.context_allowlist})
        return a

    # ---- history / export ----
    async def access_history(self, user_id: uuid.UUID, limit: int, offset: int) -> list[AuditLog]:
        return await AuditRepo(self.s).for_user(user_id, limit, offset)

    async def export(self, user: User, ctx: RequestContext) -> dict[str, Any]:
        uid = user.id
        profile = await ProfileRepo(self.s).get(uid)
        cycles = await CycleRepo(self.s).list(uid, limit=EXPORT_LIMIT)
        symptoms = await SymptomRepo(self.s).list(uid, limit=EXPORT_LIMIT)
        lifestyle = await LifestyleRepo(self.s).list(uid, limit=EXPORT_LIMIT)
        moods = await MoodRepo(self.s).list(uid, limit=EXPORT_LIMIT)
        consents = await ConsentRepo(self.s).list(uid)
        ai = await AISettingsRepo(self.s).get(uid)
        audit = await AuditRepo(self.s).for_user(uid, 1000, 0)

        def row(o, *fields):
            return {f: _iso(getattr(o, f)) for f in fields}

        data = {
            "exported_at": datetime.now().astimezone().isoformat(),
            "user": {"id": str(uid), "email": str(user.email), "display_name": user.display_name,
                     "created_at": user.created_at.isoformat()},
            "profile": ProfileOut.from_model(profile).model_dump(mode="json") if profile else None,
            "consents": [row(c, "purpose", "granted", "version", "granted_at", "revoked_at")
                         for c in consents],
            "ai_settings": row(ai, "personalization_enabled", "external_llm_allowed",
                               "context_allowlist", "chat_retention_days") if ai else None,
            "cycles": [row(c, "id", "start_date", "end_date", "flow_intensity", "notes")
                       for c in cycles],
            "symptoms": [row(x, "id", "logged_at", "symptom_code", "severity", "source")
                         for x in symptoms],
            "lifestyle": [{**row(r, "id", "date", "sleep_quality", "activity_minutes", "water_ml",
                                 "stress_level", "nutrition_notes"),
                           "sleep_hours": float(r.sleep_hours) if r.sleep_hours is not None else None}
                          for r in lifestyle],
            "mood": [row(m, "id", "logged_at", "mood_score", "tags") for m in moods],
            "audit_log_recent": [row(a, "occurred_at", "action", "resource", "outcome")
                                 for a in audit],
        }
        for coll in ("cycles", "symptoms", "lifestyle", "mood"):
            for item in data[coll]:
                item["id"] = str(item["id"])
        await self.audit.record("export", ctx, resource="account")
        return data

    # ---- erasure ----
    async def delete_account(self, user: User, password: str, ctx: RequestContext) -> None:
        if not await asyncio.to_thread(verify_password, user.password_hash, password):
            await self.audit.record("account_delete", ctx, resource="account", outcome="failure",
                                    details={"reason": "bad_password"})
            raise AppError(403, "forbidden", "Password is incorrect.")
        uid = user.id
        # Anonymised trail entry: no user_id, only a one-way reference.
        await self.audit.record("account_deleted", None, user_id=None, resource="account",
                                details={"ref": hashlib.sha256(str(uid).encode()).hexdigest()[:16]})
        await AuthService(self.s, self.redis, self.cfg, self.audit).revoke_all_sessions(uid)
        await self.redis.delete(dashboard_cache_key(uid))
        # Core DELETE so the database cascades every user-owned row (audit rows keep, user_id -> NULL).
        await self.s.execute(delete(User).where(User.id == uid))
        await self.s.commit()
