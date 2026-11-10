import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, get_redis, require_consent
from app.db.session import get_session
from app.schemas.records import (
    CycleIn,
    CycleOut,
    CycleStats,
    LifestyleIn,
    LifestyleOut,
    LifestyleSummary,
    MoodIn,
    MoodOut,
    SymptomIn,
    SymptomOut,
)
from app.services.records import CycleService, LifestyleService, MoodService, SymptomService

consent = require_consent("health_tracking")
Limit = Query(50, ge=1, le=200)
Offset = Query(0, ge=0)

cycles = APIRouter(prefix="/cycles", tags=["Cycles"])
symptoms = APIRouter(prefix="/symptoms", tags=["Symptoms"])
lifestyle = APIRouter(prefix="/lifestyle", tags=["Lifestyle"])
mood = APIRouter(prefix="/mood", tags=["Mood"])


# ---- cycles ----
@cycles.get("", response_model=list[CycleOut])
async def list_cycles(date_from: date | None = None, date_to: date | None = None,
                      limit: int = Limit, offset: int = Offset, auth: AuthContext = Depends(consent),
                      s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    return await CycleService(s, r).list(auth.user.id, auth.ctx, date_from=date_from,
                                         date_to=date_to, limit=limit, offset=offset)


@cycles.post("", response_model=CycleOut, status_code=status.HTTP_201_CREATED)
async def create_cycle(body: CycleIn, auth: AuthContext = Depends(consent),
                       s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    return await CycleService(s, r).create(auth.user.id, body, auth.ctx)


@cycles.get("/stats", response_model=CycleStats)
async def cycle_stats(auth: AuthContext = Depends(consent), s: AsyncSession = Depends(get_session),
                      r: Redis = Depends(get_redis)):
    return await CycleService(s, r).stats(auth.user.id, auth.ctx)


@cycles.put("/{item_id}", response_model=CycleOut)
async def update_cycle(item_id: uuid.UUID, body: CycleIn, auth: AuthContext = Depends(consent),
                       s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    return await CycleService(s, r).update(auth.user.id, item_id, body, auth.ctx)


@cycles.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cycle(item_id: uuid.UUID, auth: AuthContext = Depends(consent),
                       s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    await CycleService(s, r).delete(auth.user.id, item_id, auth.ctx)
    return Response(status_code=204)


# ---- symptoms ----
@symptoms.get("", response_model=list[SymptomOut])
async def list_symptoms(date_from: datetime | None = None, date_to: datetime | None = None,
                        symptom_code: str | None = None, limit: int = Limit, offset: int = Offset,
                        auth: AuthContext = Depends(consent), s: AsyncSession = Depends(get_session),
                        r: Redis = Depends(get_redis)):
    return await SymptomService(s, r).list(auth.user.id, auth.ctx, date_from=date_from,
                                           date_to=date_to, symptom_code=symptom_code,
                                           limit=limit, offset=offset)


@symptoms.post("", response_model=SymptomOut, status_code=status.HTTP_201_CREATED)
async def create_symptom(body: SymptomIn, auth: AuthContext = Depends(consent),
                         s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    return await SymptomService(s, r).create(auth.user.id, body, auth.ctx)


@symptoms.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_symptom(item_id: uuid.UUID, auth: AuthContext = Depends(consent),
                         s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    await SymptomService(s, r).delete(auth.user.id, item_id, auth.ctx)
    return Response(status_code=204)


# ---- lifestyle ----
@lifestyle.get("", response_model=list[LifestyleOut])
async def list_lifestyle(date_from: date | None = None, date_to: date | None = None,
                         limit: int = Limit, offset: int = Offset,
                         auth: AuthContext = Depends(consent), s: AsyncSession = Depends(get_session),
                         r: Redis = Depends(get_redis)):
    rows = await LifestyleService(s, r).list(auth.user.id, auth.ctx, date_from=date_from,
                                             date_to=date_to, limit=limit, offset=offset)
    return [_life_out(x) for x in rows]


def _life_out(x) -> LifestyleOut:
    return LifestyleOut(id=x.id, date=x.date,
                        sleep_hours=float(x.sleep_hours) if x.sleep_hours is not None else None,
                        sleep_quality=x.sleep_quality, activity_minutes=x.activity_minutes,
                        water_ml=x.water_ml, stress_level=x.stress_level)


@lifestyle.post("", response_model=LifestyleOut, status_code=status.HTTP_201_CREATED)
async def create_lifestyle(body: LifestyleIn, auth: AuthContext = Depends(consent),
                           s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    return _life_out(await LifestyleService(s, r).create(auth.user.id, body, auth.ctx))


@lifestyle.get("/summary", response_model=LifestyleSummary)
async def lifestyle_summary(days: int = Query(30, ge=1, le=365), auth: AuthContext = Depends(consent),
                            s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    return await LifestyleService(s, r).summary(auth.user.id, days, auth.ctx)


@lifestyle.put("/{item_id}", response_model=LifestyleOut)
async def update_lifestyle(item_id: uuid.UUID, body: LifestyleIn,
                           auth: AuthContext = Depends(consent),
                           s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    return _life_out(await LifestyleService(s, r).update(auth.user.id, item_id, body, auth.ctx))


# ---- mood ----
@mood.get("", response_model=list[MoodOut])
async def list_mood(date_from: datetime | None = None, date_to: datetime | None = None,
                    limit: int = Limit, offset: int = Offset, auth: AuthContext = Depends(consent),
                    s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    return await MoodService(s, r).list(auth.user.id, auth.ctx, date_from=date_from,
                                        date_to=date_to, limit=limit, offset=offset)


@mood.post("", response_model=MoodOut, status_code=status.HTTP_201_CREATED)
async def create_mood(body: MoodIn, auth: AuthContext = Depends(consent),
                      s: AsyncSession = Depends(get_session), r: Redis = Depends(get_redis)):
    return await MoodService(s, r).create(auth.user.id, body, auth.ctx)
