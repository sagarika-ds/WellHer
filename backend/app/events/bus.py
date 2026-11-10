"""Event pipeline. A confirmed/saved record emits an event AFTER its transaction commits.

Delivery: ARQ (Redis) in normal operation; inline when EVENTS_INLINE=true (tests/dev).
Handlers are idempotent per (event_id, handler) via the pipeline_runs table, so retries are safe.
"""
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from redis.asyncio import Redis
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.models import PipelineRun

log = logging.getLogger("app.events")

Handler = Callable[["DomainEvent", Redis], Awaitable[None]]
_REGISTRY: dict[str, list[Handler]] = {}
_pool: ArqRedis | None = None


@dataclass(frozen=True)
class DomainEvent:
    type: str
    user_id: uuid.UUID
    payload: dict[str, Any]
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(id=str(self.id), user_id=str(self.user_id), occurred_at=self.occurred_at.isoformat())
        return d

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> "DomainEvent":
        return cls(type=d["type"], user_id=uuid.UUID(d["user_id"]), payload=d["payload"],
                   id=uuid.UUID(d["id"]), occurred_at=datetime.fromisoformat(d["occurred_at"]))


def on(*event_types: str) -> Callable[[Handler], Handler]:
    def deco(fn: Handler) -> Handler:
        for t in event_types:
            _REGISTRY.setdefault(t, []).append(fn)
        return fn
    return deco


def handlers_for(event_type: str) -> list[Handler]:
    return list(_REGISTRY.get(event_type, []))


class HandlersFailed(Exception):
    pass


async def _claim(event: DomainEvent, name: str) -> bool:
    """True if this worker should run the handler (new, or previously failed)."""
    stmt = pg_insert(PipelineRun).values(
        event_id=event.id, event_type=event.type, user_id=event.user_id, handler=name,
        status="running")
    stmt = stmt.on_conflict_do_update(
        index_elements=["event_id", "handler"],
        set_={"status": "running", "attempts": PipelineRun.attempts + 1, "error": None,
              "started_at": datetime.now(UTC), "finished_at": None},
        where=PipelineRun.status == "failed",
    ).returning(PipelineRun.id)
    try:
        async with get_sessionmaker()() as s:
            got = (await s.execute(stmt)).scalar_one_or_none()
            await s.commit()
            return got is not None
    except IntegrityError:  # user was deleted before the handler ran
        return False


async def _finish(event: DomainEvent, name: str, status: str, error: str | None) -> None:
    async with get_sessionmaker()() as s:
        await s.execute(update(PipelineRun).where(
            PipelineRun.event_id == event.id, PipelineRun.handler == name
        ).values(status=status, error=error, finished_at=datetime.now(UTC)))
        await s.commit()


async def run_handlers(event: DomainEvent, redis: Redis) -> None:
    failed: list[str] = []
    for h in handlers_for(event.type):
        name = h.__name__
        if not await _claim(event, name):
            continue
        try:
            await h(event, redis)
        except Exception as exc:
            log.exception("handler %s failed for event %s", name, event.id)
            await _finish(event, name, "failed", f"{type(exc).__name__}: {exc}"[:1000])
            failed.append(name)
        else:
            await _finish(event, name, "done", None)
    if failed:
        raise HandlersFailed(", ".join(failed))


async def _get_pool() -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def publish(event: DomainEvent, redis: Redis) -> None:
    """Never raises into the request path: the record is already committed."""
    try:
        if get_settings().events_inline:
            try:
                await run_handlers(event, redis)
            except HandlersFailed:
                pass  # recorded in pipeline_runs
        else:
            pool = await _get_pool()
            await pool.enqueue_job("process_event", event.to_json(), _job_id=str(event.id))
    except Exception:
        log.exception("failed to publish event %s", event.type)
