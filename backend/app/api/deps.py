from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.context import RequestContext
from app.core.exceptions import consent_required, forbidden, unauthenticated
from app.core.redis import deny_jti_key, get_redis_client, revoked_sid_key
from app.core.security import AccessClaims, decode_access_token
from app.db.session import get_session
from app.models import User
from app.repositories.identity import UserRepo
from app.services.consent import ConsentService

bearer = HTTPBearer(auto_error=False, description="Access token from /auth/login")


def get_redis() -> Redis:
    return get_redis_client()


def request_context(request: Request, user_id=None) -> RequestContext:
    return RequestContext(
        user_id=user_id, ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_id=getattr(request.state, "request_id", None))


def get_anon_ctx(request: Request) -> RequestContext:
    return request_context(request)


@dataclass
class AuthContext:
    user: User
    claims: AccessClaims
    ctx: RequestContext


async def get_auth(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> AuthContext:
    if creds is None or creds.scheme.lower() != "bearer":
        raise unauthenticated()
    claims = decode_access_token(settings, creds.credentials)
    if await redis.exists(deny_jti_key(claims.jti)) or await redis.exists(
            revoked_sid_key(claims.session_id)):
        raise unauthenticated("Session has ended.")
    user = await UserRepo(session).get(claims.user_id)
    if user is None or not user.is_active:
        raise unauthenticated()
    return AuthContext(user, claims, request_context(request, user.id))


def require_role(*roles: str) -> Callable[..., Awaitable[AuthContext]]:
    async def dep(auth: AuthContext = Depends(get_auth)) -> AuthContext:
        if auth.user.role not in roles:
            raise forbidden("Your role does not allow this action.")
        return auth
    return dep


def require_consent(purpose: str) -> Callable[..., Awaitable[AuthContext]]:
    async def dep(auth: AuthContext = Depends(get_auth),
                  session: AsyncSession = Depends(get_session)) -> AuthContext:
        if not await ConsentService(session).is_granted(auth.user.id, purpose):
            raise consent_required(purpose)
        return auth
    return dep
