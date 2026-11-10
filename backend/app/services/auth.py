import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.context import RequestContext
from app.core.exceptions import AppError, conflict, unauthenticated
from app.core.ratelimit import LoginLimiter
from app.core.redis import deny_jti_key, revoked_sid_key
from app.core.security import (
    AccessClaims,
    create_access_token,
    hash_password,
    hash_token,
    new_opaque_token,
    password_needs_rehash,
    verify_password,
)
from app.models import AISettings, HealthProfile, PasswordResetToken, RefreshToken, User
from app.repositories.identity import AISettingsRepo, ProfileRepo, TokenRepo, UserRepo
from app.schemas.auth import ConsentChoice, TokenPair
from app.services.audit import AuditService
from app.services.consent import ConsentService
from app.services.email import send_password_reset

GENERIC_LOGIN_ERROR = "Invalid email or password."


class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis, settings: Settings,
                 audit: AuditService | None = None) -> None:
        self.s, self.redis, self.cfg = session, redis, settings
        self.users, self.tokens = UserRepo(session), TokenRepo(session)
        self.audit = audit or AuditService()
        self.limiter = LoginLimiter(redis, settings.login_max_attempts, settings.login_window_seconds)

    # ---- registration ----
    async def register(self, email: str, password: str, display_name: str,
                       consents: list[ConsentChoice], ctx: RequestContext) -> User:
        if await self.users.by_email(email):
            await self.audit.record("register", ctx, outcome="failure", details={"reason": "duplicate"})
            raise conflict("An account with this email already exists.")
        pw_hash = await asyncio.to_thread(hash_password, password)
        try:
            user = await self.users.add(User(email=email, password_hash=pw_hash,
                                             display_name=display_name))
            await ProfileRepo(self.s).add(HealthProfile(user_id=user.id))
            await AISettingsRepo(self.s).add(AISettings(user_id=user.id))
            await ConsentService(self.s, self.audit).ensure_defaults(
                user.id, {c.purpose: c.granted for c in consents})
            await self.s.commit()
        except IntegrityError as exc:  # concurrent duplicate registration
            await self.s.rollback()
            raise conflict("An account with this email already exists.") from exc
        await self.audit.record("register", ctx, user_id=user.id, resource="user",
                                resource_id=str(user.id))
        return user

    # ---- sessions ----
    async def _issue(self, user: User, family_id: uuid.UUID,
                     device: str | None) -> tuple[TokenPair, RefreshToken]:
        access, claims = create_access_token(self.cfg, user_id=user.id, role=user.role,
                                             session_id=family_id)
        refresh = new_opaque_token()
        row = await self.tokens.add_refresh(RefreshToken(
            user_id=user.id, family_id=family_id, token_hash=hash_token(refresh), device=device,
            expires_at=datetime.now(UTC) + timedelta(days=self.cfg.jwt_refresh_ttl_days)))
        ttl = int((claims.expires_at - datetime.now(UTC)).total_seconds())
        return TokenPair(access_token=access, refresh_token=refresh, expires_in=ttl), row

    async def login(self, email: str, password: str, device: str | None,
                    ctx: RequestContext) -> TokenPair:
        await self.limiter.check(email, ctx.ip)
        user = await self.users.by_email(email)
        ok = await asyncio.to_thread(verify_password, user.password_hash if user else None, password)
        if not ok or user is None or not user.is_active:
            await self.limiter.failure(email, ctx.ip)
            await self.audit.record("login", ctx, user_id=user.id if user else None,
                                    outcome="failure", details={"reason": "bad_credentials"})
            raise unauthenticated(GENERIC_LOGIN_ERROR)
        if password_needs_rehash(user.password_hash):
            user.password_hash = await asyncio.to_thread(hash_password, password)
        pair, _ = await self._issue(user, uuid.uuid4(), device)
        await self.s.commit()
        await self.limiter.reset(email, ctx.ip)
        await self.audit.record("login", ctx, user_id=user.id, resource="session")
        return pair

    async def refresh(self, refresh_token: str, ctx: RequestContext) -> TokenPair:
        row = await self.tokens.get_refresh_for_update(hash_token(refresh_token))
        if row is None:
            raise unauthenticated("Invalid refresh token.")
        if row.revoked_at is not None:
            # A rotated/revoked token was replayed: assume theft and kill the whole session family.
            await self.tokens.revoke_family(row.family_id)
            await self.s.commit()
            await self._deny_session(row.family_id)
            await self.audit.record("refresh_reuse_detected", ctx, user_id=row.user_id,
                                    resource="session", resource_id=str(row.family_id),
                                    outcome="failure")
            raise unauthenticated("Invalid refresh token.")
        if row.expires_at <= datetime.now(UTC):
            raise unauthenticated("Refresh token expired.")
        user = await self.users.get(row.user_id)
        if user is None or not user.is_active:
            raise unauthenticated("Invalid refresh token.")
        pair, new_row = await self._issue(user, row.family_id, row.device)
        row.revoked_at, row.replaced_by = datetime.now(UTC), new_row.id
        await self.s.commit()
        await self.audit.record("refresh", ctx, user_id=user.id, resource="session",
                                resource_id=str(row.family_id))
        return pair

    async def _deny_session(self, sid: uuid.UUID) -> None:
        # Access tokens are stateless; deny the whole session until the longest-lived one expires.
        await self.redis.set(revoked_sid_key(sid), "1", ex=self.cfg.jwt_access_ttl_min * 60 + 60)

    async def logout(self, claims: AccessClaims, ctx: RequestContext) -> None:
        ttl = max(1, int((claims.expires_at - datetime.now(UTC)).total_seconds()))
        await self.redis.set(deny_jti_key(claims.jti), "1", ex=ttl)
        await self.tokens.revoke_family(claims.session_id)
        await self.s.commit()
        await self._deny_session(claims.session_id)
        await self.audit.record("logout", ctx, user_id=claims.user_id, resource="session",
                                resource_id=str(claims.session_id))

    async def revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        for fam in await self.tokens.active_families_for_user(user_id):
            await self._deny_session(fam)
        await self.tokens.revoke_all_for_user(user_id)

    # ---- password reset ----
    async def forgot_password(self, email: str, ctx: RequestContext) -> None:
        """Always succeeds from the caller's view (no account enumeration)."""
        user = await self.users.by_email(email)
        if user is not None and user.is_active:
            token = new_opaque_token()
            await self.tokens.add_reset(PasswordResetToken(
                user_id=user.id, token_hash=hash_token(token),
                expires_at=datetime.now(UTC) + timedelta(minutes=self.cfg.password_reset_ttl_min)))
            await self.s.commit()
            await send_password_reset(str(user.email), token)
        await self.audit.record("password_reset_requested", ctx,
                                user_id=user.id if user else None, resource="user")

    async def reset_password(self, token: str, new_password: str, ctx: RequestContext) -> None:
        row = await self.tokens.get_reset_for_update(hash_token(token))
        now = datetime.now(UTC)
        if row is None or row.used_at is not None or row.expires_at <= now:
            await self.audit.record("password_reset", ctx, outcome="failure",
                                    details={"reason": "invalid_token"})
            raise AppError(400, "invalid_reset_token", "This reset link is invalid or has expired.")
        user = await self.users.get(row.user_id)
        user.password_hash = await asyncio.to_thread(hash_password, new_password)
        row.used_at = now
        await self.revoke_all_sessions(user.id)
        await self.s.commit()
        await self.audit.record("password_reset", ctx, user_id=user.id, resource="user")
