import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CycleRecord, LifestyleRecord, MoodRecord, SymptomLog, TimelineEvent
from app.repositories.base import UserOwnedRepo


class CycleRepo(UserOwnedRepo[CycleRecord]):
    model = CycleRecord
    order_by = CycleRecord.start_date.desc()

    async def overlapping(self, user_id: uuid.UUID, start: date, end: date | None,
                          exclude_id: uuid.UUID | None = None) -> CycleRecord | None:
        """A period overlaps another if their [start, end] ranges intersect (open end = start day)."""
        new_end = end or start
        other_end = func.coalesce(CycleRecord.end_date, CycleRecord.start_date)
        stmt = select(CycleRecord).where(
            CycleRecord.user_id == user_id, CycleRecord.start_date <= new_end, other_end >= start)
        if exclude_id:
            stmt = stmt.where(CycleRecord.id != exclude_id)
        return (await self.s.execute(stmt.limit(1))).scalar_one_or_none()

    async def start_dates(self, user_id: uuid.UUID) -> list[date]:
        stmt = select(CycleRecord.start_date).where(CycleRecord.user_id == user_id).order_by(
            CycleRecord.start_date)
        return list((await self.s.execute(stmt)).scalars())

    async def next_start_after(self, user_id: uuid.UUID, d: date) -> date | None:
        stmt = select(func.min(CycleRecord.start_date)).where(
            CycleRecord.user_id == user_id, CycleRecord.start_date > d)
        return (await self.s.execute(stmt)).scalar_one()


class SymptomRepo(UserOwnedRepo[SymptomLog]):
    model = SymptomLog
    order_by = SymptomLog.logged_at.desc()


class LifestyleRepo(UserOwnedRepo[LifestyleRecord]):
    model = LifestyleRecord
    order_by = LifestyleRecord.date.desc()

    async def by_date(self, user_id: uuid.UUID, d: date) -> LifestyleRecord | None:
        stmt = select(LifestyleRecord).where(
            LifestyleRecord.user_id == user_id, LifestyleRecord.date == d)
        return (await self.s.execute(stmt)).scalar_one_or_none()

    async def summary(self, user_id: uuid.UUID, since: date) -> dict[str, Any]:
        stmt = select(
            func.count(), func.avg(LifestyleRecord.sleep_hours),
            func.avg(LifestyleRecord.activity_minutes), func.avg(LifestyleRecord.stress_level),
        ).where(LifestyleRecord.user_id == user_id, LifestyleRecord.date >= since)
        n, sleep, act, stress = (await self.s.execute(stmt)).one()
        return {"n": n, "sleep": sleep, "activity": act, "stress": stress}


class MoodRepo(UserOwnedRepo[MoodRecord]):
    model = MoodRecord
    order_by = MoodRecord.logged_at.desc()


class TimelineRepo:
    def __init__(self, s: AsyncSession) -> None:
        self.s = s

    async def upsert(self, user_id: uuid.UUID, kind: str, source_table: str, source_id: uuid.UUID,
                     occurred_at: datetime, payload: dict) -> None:
        stmt = pg_insert(TimelineEvent).values(
            user_id=user_id, kind=kind, source_table=source_table, source_id=source_id,
            occurred_at=occurred_at, payload=payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_table", "source_id"],
            set_={"occurred_at": occurred_at, "payload": payload})
        await self.s.execute(stmt)

    async def delete_for_source(self, source_table: str, source_id: uuid.UUID) -> None:
        await self.s.execute(delete(TimelineEvent).where(
            TimelineEvent.source_table == source_table, TimelineEvent.source_id == source_id))

    async def count(self, user_id: uuid.UUID) -> int:
        return (await self.s.execute(select(func.count()).select_from(TimelineEvent).where(
            TimelineEvent.user_id == user_id))).scalar_one()


def midnight_utc(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=UTC)
