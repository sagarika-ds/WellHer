import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AISettings,
    AuditLog,
    HealthProfile,
    PasswordResetToken,
    RefreshToken,
    User,
    UserConsent,
)


class UserRepo:
    def __init__(self, s: AsyncSession) -> None:
        self.s = s

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.s.get(User, user_id)

    async def by_email(self, email: str) -> User | None:
        return (await self.s.execute(select(User).where(User.email == email))).scalar_one_or_none()

    async def add(self, user: User) -> User:
        self.s.add(user)
        await self.s.flush()
        return user


class TokenRepo:
    def __init__(self, s: AsyncSession) -> None:
        self.s = s

    async def add_refresh(self, t: RefreshToken) -> RefreshToken:
        self.s.add(t)
        await self.s.flush()
        return t

    async def get_refresh_for_update(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
        return (await self.s.execute(stmt)).scalar_one_or_none()

    async def revoke_family(self, family_id: uuid.UUID) -> None:
        await self.s.execute(update(RefreshToken).where(
            RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None)
        ).values(revoked_at=datetime.now(UTC)))

    async def active_families_for_user(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(RefreshToken.family_id).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)).distinct()
        return list((await self.s.execute(stmt)).scalars())

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        await self.s.execute(update(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        ).values(revoked_at=datetime.now(UTC)))

    async def add_reset(self, t: PasswordResetToken) -> PasswordResetToken:
        self.s.add(t)
        await self.s.flush()
        return t

    async def get_reset_for_update(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash).with_for_update()
        return (await self.s.execute(stmt)).scalar_one_or_none()


class ConsentRepo:
    def __init__(self, s: AsyncSession) -> None:
        self.s = s

    async def list(self, user_id: uuid.UUID) -> list[UserConsent]:
        stmt = select(UserConsent).where(UserConsent.user_id == user_id).order_by(UserConsent.purpose)
        return list((await self.s.execute(stmt)).scalars())

    async def get(self, user_id: uuid.UUID, purpose: str) -> UserConsent | None:
        stmt = select(UserConsent).where(
            UserConsent.user_id == user_id, UserConsent.purpose == purpose)
        return (await self.s.execute(stmt)).scalar_one_or_none()

    async def add(self, c: UserConsent) -> UserConsent:
        self.s.add(c)
        await self.s.flush()
        return c


class ProfileRepo:
    def __init__(self, s: AsyncSession) -> None:
        self.s = s

    async def get(self, user_id: uuid.UUID) -> HealthProfile | None:
        return await self.s.get(HealthProfile, user_id)

    async def add(self, p: HealthProfile) -> HealthProfile:
        self.s.add(p)
        await self.s.flush()
        return p


class AISettingsRepo:
    def __init__(self, s: AsyncSession) -> None:
        self.s = s

    async def get(self, user_id: uuid.UUID) -> AISettings | None:
        return await self.s.get(AISettings, user_id)

    async def add(self, a: AISettings) -> AISettings:
        self.s.add(a)
        await self.s.flush()
        return a


class AuditRepo:
    def __init__(self, s: AsyncSession) -> None:
        self.s = s

    async def add(self, row: AuditLog) -> None:
        self.s.add(row)
        await self.s.flush()

    async def for_user(self, user_id: uuid.UUID, limit: int, offset: int) -> list[AuditLog]:
        stmt = (select(AuditLog).where(AuditLog.user_id == user_id)
                .order_by(AuditLog.occurred_at.desc(), AuditLog.id).limit(limit).offset(offset))
        return list((await self.s.execute(stmt)).scalars())
