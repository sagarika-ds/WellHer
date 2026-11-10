from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, get_auth
from app.db.session import get_session
from app.models.identity import CONSENT_PURPOSES
from app.schemas.auth import Purpose
from app.schemas.consent import ConsentOut, ConsentSet
from app.schemas.profile import ProfileIn, ProfileOut
from app.services.consent import ConsentService
from app.services.profile import ProfileService

router = APIRouter()


@router.get("/profile", response_model=ProfileOut, tags=["Profile"])
async def get_profile(auth: AuthContext = Depends(get_auth), s: AsyncSession = Depends(get_session)):
    return ProfileOut.from_model(await ProfileService(s).get(auth.user.id, auth.ctx))


@router.put("/profile", response_model=ProfileOut, tags=["Profile"])
async def put_profile(body: ProfileIn, auth: AuthContext = Depends(get_auth),
                      s: AsyncSession = Depends(get_session)):
    return ProfileOut.from_model(await ProfileService(s).update(auth.user.id, body, auth.ctx))


@router.get("/consents", response_model=list[ConsentOut], tags=["Consent"])
async def list_consents(auth: AuthContext = Depends(get_auth), s: AsyncSession = Depends(get_session)):
    return await ConsentService(s).list(auth.user.id)


@router.put("/consents/{purpose}", response_model=ConsentOut, tags=["Consent"])
async def set_consent(purpose: Purpose, body: ConsentSet, auth: AuthContext = Depends(get_auth),
                      s: AsyncSession = Depends(get_session)):
    assert purpose in CONSENT_PURPOSES
    return await ConsentService(s).set(auth.user.id, purpose, body.granted, auth.ctx)
