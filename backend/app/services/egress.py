"""Egress gate: the ONLY path by which user-derived text/context may reach an LLM.

Rules (all enforced here, not by callers):
  * hosted/external provider  -> needs consent `llm_external` AND ai_settings.external_llm_allowed
  * any provider              -> health context is included only if consent `ml_processing` is granted
                                 and only for keys in the user's `context_allowlist`
  * every allowed payload is scrubbed of emails, phone numbers and the user's own name tokens
  * every decision (allow or block) is audit-logged WITHOUT the payload content
Nothing calls an LLM yet in this milestone; the gate is built first so that no later code can bypass it.
"""
import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models import User
from app.repositories.identity import AISettingsRepo
from app.services.audit import AuditService
from app.services.consent import ConsentService

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_CANDIDATE_RE = re.compile(r"(?<![\w.])\+?\d[\d\s\-().]{8,}\d(?![\w])")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class EgressDecision:
    allowed: bool
    reason: str
    text: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


def _phone_sub(m: re.Match) -> str:
    raw = m.group(0)
    if ISO_DATE_RE.match(raw.strip()) or sum(c.isdigit() for c in raw) < 10:
        return raw
    return "[phone]"


def _name_tokens(user: User) -> list[str]:
    toks = set(re.findall(r"[^\W\d_]{3,}", user.display_name, flags=re.UNICODE))
    local = str(user.email).split("@")[0]
    toks |= set(re.findall(r"[A-Za-z]{4,}", local))
    return sorted(toks, key=len, reverse=True)


def scrub_text(text: str, user: User) -> str:
    text = EMAIL_RE.sub("[email]", text)
    text = PHONE_CANDIDATE_RE.sub(_phone_sub, text)
    for tok in _name_tokens(user):
        text = re.sub(rf"(?<!\w){re.escape(tok)}(?!\w)", "[name]", text, flags=re.IGNORECASE)
    return text


def _scrub_value(v: Any, user: User) -> Any:
    if isinstance(v, str):
        return scrub_text(v, user)
    if isinstance(v, dict):
        return {k: _scrub_value(x, user) for k, x in v.items()}
    if isinstance(v, list):
        return [_scrub_value(x, user) for x in v]
    return v


class EgressGate:
    PROVIDERS = ("local", "hosted")

    def __init__(self, session: AsyncSession, audit: AuditService | None = None) -> None:
        self.s, self.audit = session, audit or AuditService()

    async def prepare(self, user: User, provider: str, text: str, context: dict[str, Any],
                      ctx: RequestContext) -> EgressDecision:
        async def blocked(reason: str) -> EgressDecision:
            await self.audit.record("egress_blocked", ctx, user_id=user.id, resource="llm",
                                    outcome="blocked", details={"provider": provider, "reason": reason})
            return EgressDecision(False, reason)

        if provider not in self.PROVIDERS:
            return await blocked("unknown_provider")
        settings = await AISettingsRepo(self.s).get(user.id)
        consents = ConsentService(self.s, self.audit)
        if provider == "hosted":
            if not await consents.is_granted(user.id, "llm_external"):
                return await blocked("consent_llm_external_not_granted")
            if settings is None or not settings.external_llm_allowed:
                return await blocked("external_llm_disabled_in_ai_settings")
        allowed_keys: set[str] = set()
        if settings and await consents.is_granted(user.id, "ml_processing"):
            allowed_keys = set(settings.context_allowlist)
        sent = {k: _scrub_value(v, user) for k, v in context.items() if k in allowed_keys}
        dropped = sorted(set(context) - set(sent))
        clean_text = scrub_text(text, user)
        await self.audit.record("egress_allowed", ctx, user_id=user.id, resource="llm", details={
            "provider": provider, "context_keys_sent": sorted(sent), "context_keys_dropped": dropped,
            "text_scrubbed": clean_text != text})
        return EgressDecision(True, "ok", clean_text, sent)
