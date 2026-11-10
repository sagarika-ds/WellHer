import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, get_auth, get_redis
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.schemas.privacy import (
    AccessHistoryItem,
    AISettingsIn,
    AISettingsOut,
    DeleteAccountIn,
    ExportOut,
)
from app.services.privacy import PrivacyService

router = APIRouter(prefix="/privacy", tags=["Vault"])


def _svc(s: AsyncSession, r: Redis, cfg: Settings) -> PrivacyService:
    return PrivacyService(s, r, cfg)


@router.get("/ai-settings", response_model=AISettingsOut)
async def get_ai_settings(auth: AuthContext = Depends(get_auth), s: AsyncSession = Depends(get_session),
                          r: Redis = Depends(get_redis), cfg: Settings = Depends(get_settings)):
    return await _svc(s, r, cfg).get_ai_settings(auth.user.id)


@router.put("/ai-settings", response_model=AISettingsOut)
async def put_ai_settings(body: AISettingsIn, auth: AuthContext = Depends(get_auth),
                          s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis),
                          cfg: Settings = Depends(get_settings)):
    return await _svc(s, r, cfg).update_ai_settings(auth.user.id, body, auth.ctx)


@router.get("/access-history", response_model=list[AccessHistoryItem])
async def access_history(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                         auth: AuthContext = Depends(get_auth), s: AsyncSession = Depends(get_session),
                         r: Redis = Depends(get_redis), cfg: Settings = Depends(get_settings)):
    rows = await _svc(s, r, cfg).access_history(auth.user.id, limit, offset)
    return [AccessHistoryItem(timestamp=x.occurred_at, action=x.action, resource=x.resource,
                              outcome=x.outcome, ip=x.ip) for x in rows]


@router.post("/export", response_model=ExportOut)
async def export(auth: AuthContext = Depends(get_auth), s: AsyncSession = Depends(get_session),
                 r: Redis = Depends(get_redis), cfg: Settings = Depends(get_settings)):
    data = await _svc(s, r, cfg).export(auth.user, auth.ctx)
    return ExportOut(job_id=uuid.uuid4(), data=data)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(body: DeleteAccountIn, auth: AuthContext = Depends(get_auth),
                         s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis),
                         cfg: Settings = Depends(get_settings)):
    await _svc(s, r, cfg).delete_account(auth.user, body.password, auth.ctx)
    return Response(status_code=204)
