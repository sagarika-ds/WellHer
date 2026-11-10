from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, get_anon_ctx, get_auth, get_redis
from app.core.config import Settings, get_settings
from app.core.context import RequestContext
from app.db.session import get_session
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
    UserOut,
)
from app.schemas.common import Ok
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def _svc(session: AsyncSession, redis: Redis, settings: Settings) -> AuthService:
    return AuthService(session, redis, settings)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session),
                   redis: Redis = Depends(get_redis), settings: Settings = Depends(get_settings),
                   ctx: RequestContext = Depends(get_anon_ctx)):
    return await _svc(session, redis, settings).register(
        str(body.email), body.password, body.display_name, body.consents, ctx)


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session),
                redis: Redis = Depends(get_redis), settings: Settings = Depends(get_settings),
                ctx: RequestContext = Depends(get_anon_ctx)):
    return await _svc(session, redis, settings).login(str(body.email), body.password, body.device, ctx)


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, session: AsyncSession = Depends(get_session),
                  redis: Redis = Depends(get_redis), settings: Settings = Depends(get_settings),
                  ctx: RequestContext = Depends(get_anon_ctx)):
    return await _svc(session, redis, settings).refresh(body.refresh_token, ctx)


@router.post("/logout", response_model=Ok)
async def logout(auth: AuthContext = Depends(get_auth), session: AsyncSession = Depends(get_session),
                 redis: Redis = Depends(get_redis), settings: Settings = Depends(get_settings)):
    await _svc(session, redis, settings).logout(auth.claims, auth.ctx)
    return Ok()


@router.post("/forgot-password", response_model=Ok, status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(body: ForgotPasswordRequest, session: AsyncSession = Depends(get_session),
                          redis: Redis = Depends(get_redis),
                          settings: Settings = Depends(get_settings),
                          ctx: RequestContext = Depends(get_anon_ctx)):
    await _svc(session, redis, settings).forgot_password(str(body.email), ctx)
    return Ok()


@router.post("/reset-password", response_model=Ok)
async def reset_password(body: ResetPasswordRequest, session: AsyncSession = Depends(get_session),
                         redis: Redis = Depends(get_redis),
                         settings: Settings = Depends(get_settings),
                         ctx: RequestContext = Depends(get_anon_ctx)):
    await _svc(session, redis, settings).reset_password(body.token, body.new_password, ctx)
    return Ok()


@router.get("/me", response_model=UserOut)
async def me(auth: AuthContext = Depends(get_auth)):
    return auth.user
