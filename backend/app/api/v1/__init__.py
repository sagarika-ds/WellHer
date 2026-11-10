from fastapi import APIRouter

from app.api.v1 import auth, privacy, profile_consent, records

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profile_consent.router)
for r in (records.cycles, records.symptoms, records.lifestyle, records.mood):
    api_router.include_router(r)
api_router.include_router(privacy.router)
