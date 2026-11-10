"""Repositories are the only layer that talks SQL. User-owned repos ALWAYS filter by user_id."""
import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class UserOwnedRepo(Generic[T]):
    model: type[T]
    order_by: Any  # column expression, newest first

    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, user_id: uuid.UUID, item_id: uuid.UUID) -> T | None:
        stmt = select(self.model).where(self.model.id == item_id, self.model.user_id == user_id)
        return (await self.s.execute(stmt)).scalar_one_or_none()

    async def list(self, user_id: uuid.UUID, *filters, limit: int = 50, offset: int = 0) -> list[T]:
        stmt = (select(self.model).where(self.model.user_id == user_id, *filters)
                .order_by(self.order_by, self.model.id).limit(limit).offset(offset))
        return list((await self.s.execute(stmt)).scalars())

    async def add(self, obj: T) -> T:
        self.s.add(obj)
        await self.s.flush()
        return obj

    async def delete(self, user_id: uuid.UUID, item_id: uuid.UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == item_id, self.model.user_id == user_id)
        return (await self.s.execute(stmt)).rowcount > 0
