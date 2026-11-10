"""Health-record services. Every write: validate -> persist + timeline row (ONE transaction) ->
commit -> audit -> publish `record.confirmed` / `record.deleted`."""
import statistics
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import conflict, not_found, validation
from app.events.bus import DomainEvent, publish
from app.models import CycleRecord, LifestyleRecord, MoodRecord, SymptomLog
from app.repositories.records import (
    CycleRepo,
    LifestyleRepo,
    MoodRepo,
    SymptomRepo,
    TimelineRepo,
    midnight_utc,
)
from app.schemas.records import (
    CycleIn,
    CycleOut,
    CycleStats,
    LifestyleIn,
    LifestyleSummary,
    MoodIn,
    SymptomIn,
)
from app.services.audit import AuditService


def _require(obj, what: str):
    if obj is None:
        raise not_found(what)
    return obj


class _RecordService:
    table: str
    kind: str

    def __init__(self, session: AsyncSession, redis: Redis, audit: AuditService | None = None) -> None:
        self.s, self.redis, self.audit = session, redis, audit or AuditService()
        self.timeline = TimelineRepo(session)

    def _timeline_row(self, obj: Any) -> tuple[datetime, dict[str, Any]]:
        raise NotImplementedError

    async def _stage_timeline(self, obj: Any) -> None:
        occurred, payload = self._timeline_row(obj)
        await self.timeline.upsert(obj.user_id, self.kind, self.table, obj.id, occurred, payload)

    async def _finish_write(self, obj: Any, op: str, ctx: RequestContext) -> None:
        await self.s.commit()
        await self.audit.record(op, ctx, resource=self.table, resource_id=str(obj.id))
        await publish(DomainEvent("record.confirmed", obj.user_id,
                                  {"table": self.table, "id": str(obj.id), "op": op}), self.redis)

    async def _finish_delete(self, user_id: uuid.UUID, item_id: uuid.UUID, ctx: RequestContext) -> None:
        await self.timeline.delete_for_source(self.table, item_id)
        await self.s.commit()
        await self.audit.record("delete", ctx, resource=self.table, resource_id=str(item_id))
        await publish(DomainEvent("record.deleted", user_id,
                                  {"table": self.table, "id": str(item_id)}), self.redis)

    async def _audit_read(self, ctx: RequestContext, count: int) -> None:
        await self.audit.record("read", ctx, resource=self.table, details={"count": count})


class CycleService(_RecordService):
    table, kind = "cycle_records", "cycle"

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self.repo = CycleRepo(self.s)

    def _timeline_row(self, c: CycleRecord):
        return midnight_utc(c.start_date), {
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "flow_intensity": c.flow_intensity}

    @staticmethod
    def to_out(c: CycleRecord, next_start: date | None) -> CycleOut:
        return CycleOut(id=c.id, start_date=c.start_date, end_date=c.end_date,
                        cycle_length_days=(next_start - c.start_date).days if next_start else None,
                        flow_intensity=c.flow_intensity, notes=c.notes)

    async def _check_overlap(self, user_id, data: CycleIn, exclude: uuid.UUID | None = None) -> None:
        other = await self.repo.overlapping(user_id, data.start_date, data.end_date, exclude)
        if other is not None:
            raise conflict(f"This period overlaps an existing record starting {other.start_date}.")

    async def create(self, user_id: uuid.UUID, data: CycleIn, ctx: RequestContext) -> CycleOut:
        await self._check_overlap(user_id, data)
        c = await self.repo.add(CycleRecord(user_id=user_id, **data.model_dump()))
        await self._stage_timeline(c)
        await self._finish_write(c, "create", ctx)
        return self.to_out(c, await self.repo.next_start_after(user_id, c.start_date))

    async def update(self, user_id: uuid.UUID, item_id: uuid.UUID, data: CycleIn,
                     ctx: RequestContext) -> CycleOut:
        c = _require(await self.repo.get(user_id, item_id), "Cycle")
        await self._check_overlap(user_id, data, exclude=item_id)
        for k, v in data.model_dump().items():
            setattr(c, k, v)
        await self._stage_timeline(c)
        await self._finish_write(c, "update", ctx)
        return self.to_out(c, await self.repo.next_start_after(user_id, c.start_date))

    async def delete(self, user_id: uuid.UUID, item_id: uuid.UUID, ctx: RequestContext) -> None:
        if not await self.repo.delete(user_id, item_id):
            raise not_found("Cycle")
        await self._finish_delete(user_id, item_id, ctx)

    async def list(self, user_id: uuid.UUID, ctx: RequestContext, *, date_from: date | None,
                   date_to: date | None, limit: int, offset: int) -> list[CycleOut]:
        filters = []
        if date_from:
            filters.append(CycleRecord.start_date >= date_from)
        if date_to:
            filters.append(CycleRecord.start_date <= date_to)
        rows = await self.repo.list(user_id, *filters, limit=limit, offset=offset)
        starts = await self.repo.start_dates(user_id)
        nxt = {a: b for a, b in zip(starts, starts[1:], strict=False)}
        await self._audit_read(ctx, len(rows))
        return [self.to_out(c, nxt.get(c.start_date)) for c in rows]

    async def stats(self, user_id: uuid.UUID, ctx: RequestContext) -> CycleStats:
        starts = await self.repo.start_dates(user_id)
        lengths = [(b - a).days for a, b in zip(starts, starts[1:], strict=False)]
        await self._audit_read(ctx, len(lengths))
        if not lengths:
            return CycleStats(n_cycles=0, mean_length=None, std_length=None, min=None, max=None)
        return CycleStats(
            n_cycles=len(lengths), mean_length=round(statistics.fmean(lengths), 2),
            std_length=round(statistics.stdev(lengths), 2) if len(lengths) > 1 else None,
            min=min(lengths), max=max(lengths))


class SymptomService(_RecordService):
    table, kind = "symptom_logs", "symptom"

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self.repo = SymptomRepo(self.s)

    def _timeline_row(self, x: SymptomLog):
        return x.logged_at, {"symptom_code": x.symptom_code, "severity": x.severity}

    async def create(self, user_id: uuid.UUID, data: SymptomIn, ctx: RequestContext) -> SymptomLog:
        if data.cycle_id and not await CycleRepo(self.s).get(user_id, data.cycle_id):
            raise validation("cycle_id does not refer to one of your cycles")
        x = await self.repo.add(SymptomLog(user_id=user_id, source="manual", **data.model_dump()))
        await self._stage_timeline(x)
        await self._finish_write(x, "create", ctx)
        return x

    async def delete(self, user_id: uuid.UUID, item_id: uuid.UUID, ctx: RequestContext) -> None:
        if not await self.repo.delete(user_id, item_id):
            raise not_found("Symptom log")
        await self._finish_delete(user_id, item_id, ctx)

    async def list(self, user_id: uuid.UUID, ctx: RequestContext, *, date_from: datetime | None,
                   date_to: datetime | None, symptom_code: str | None, limit: int,
                   offset: int) -> list[SymptomLog]:
        filters = []
        if date_from:
            filters.append(SymptomLog.logged_at >= date_from)
        if date_to:
            filters.append(SymptomLog.logged_at <= date_to)
        if symptom_code:
            filters.append(SymptomLog.symptom_code == symptom_code)
        rows = await self.repo.list(user_id, *filters, limit=limit, offset=offset)
        await self._audit_read(ctx, len(rows))
        return rows


class LifestyleService(_RecordService):
    table, kind = "lifestyle_records", "lifestyle"

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self.repo = LifestyleRepo(self.s)

    def _timeline_row(self, r: LifestyleRecord):
        return midnight_utc(r.date), {
            "sleep_hours": float(r.sleep_hours) if r.sleep_hours is not None else None,
            "sleep_quality": r.sleep_quality, "activity_minutes": r.activity_minutes,
            "water_ml": r.water_ml, "stress_level": r.stress_level}

    async def create(self, user_id: uuid.UUID, data: LifestyleIn, ctx: RequestContext):
        if await self.repo.by_date(user_id, data.date):
            raise conflict(f"A lifestyle entry for {data.date} already exists; update it instead.")
        r = await self.repo.add(LifestyleRecord(user_id=user_id, **data.model_dump()))
        await self._stage_timeline(r)
        await self._finish_write(r, "create", ctx)
        return r

    async def update(self, user_id: uuid.UUID, item_id: uuid.UUID, data: LifestyleIn,
                     ctx: RequestContext):
        r = _require(await self.repo.get(user_id, item_id), "Lifestyle entry")
        if data.date != r.date and await self.repo.by_date(user_id, data.date):
            raise conflict(f"A lifestyle entry for {data.date} already exists.")
        for k, v in data.model_dump().items():
            setattr(r, k, v)
        await self._stage_timeline(r)
        await self._finish_write(r, "update", ctx)
        return r

    async def list(self, user_id: uuid.UUID, ctx: RequestContext, *, date_from: date | None,
                   date_to: date | None, limit: int, offset: int):
        filters = []
        if date_from:
            filters.append(LifestyleRecord.date >= date_from)
        if date_to:
            filters.append(LifestyleRecord.date <= date_to)
        rows = await self.repo.list(user_id, *filters, limit=limit, offset=offset)
        await self._audit_read(ctx, len(rows))
        return rows

    async def summary(self, user_id: uuid.UUID, days: int, ctx: RequestContext) -> LifestyleSummary:
        r = await self.repo.summary(user_id, datetime.now(UTC).date() - timedelta(days=days))
        await self._audit_read(ctx, r["n"])
        rnd = lambda v: round(float(v), 2) if v is not None else None  # noqa: E731
        return LifestyleSummary(period_days=days, n_entries=r["n"], avg_sleep_hours=rnd(r["sleep"]),
                                avg_activity_minutes=rnd(r["activity"]), avg_stress=rnd(r["stress"]))


class MoodService(_RecordService):
    table, kind = "mood_records", "mood"

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)
        self.repo = MoodRepo(self.s)

    def _timeline_row(self, m: MoodRecord):
        return m.logged_at, {"mood_score": m.mood_score, "tags": m.tags}

    async def create(self, user_id: uuid.UUID, data: MoodIn, ctx: RequestContext) -> MoodRecord:
        m = await self.repo.add(MoodRecord(user_id=user_id, **data.model_dump()))
        await self._stage_timeline(m)
        await self._finish_write(m, "create", ctx)
        return m

    async def list(self, user_id: uuid.UUID, ctx: RequestContext, *, date_from: datetime | None,
                   date_to: datetime | None, limit: int, offset: int) -> list[MoodRecord]:
        filters = []
        if date_from:
            filters.append(MoodRecord.logged_at >= date_from)
        if date_to:
            filters.append(MoodRecord.logged_at <= date_to)
        rows = await self.repo.list(user_id, *filters, limit=limit, offset=offset)
        await self._audit_read(ctx, len(rows))
        return rows
