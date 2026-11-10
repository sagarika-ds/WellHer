import uuid

import pytest
from arq.connections import RedisSettings, create_pool
from arq.worker import Worker
from sqlalchemy import text

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.events import bus
from app.events.bus import DomainEvent, HandlersFailed, on, run_handlers
from app.events.handlers import dashboard_cache_key
from app.tasks.worker import process_event
from tests.helpers import signup

API = "/api/v1"


@pytest.fixture
def isolated_registry():
    saved = {k: list(v) for k, v in bus._REGISTRY.items()}
    yield
    bus._REGISTRY.clear()
    bus._REGISTRY.update(saved)


async def _runs(sessionmaker_):
    async with sessionmaker_() as s:
        return (await s.execute(text(
            "select handler, status, attempts, error from pipeline_runs order by handler"))).all()


async def test_record_write_runs_handlers_inline_and_invalidates_cache(client, sessionmaker_):
    acc = await signup(client)
    r = get_redis_client()
    await r.set(dashboard_cache_key(acc.user_id), "stale")
    await client.post(f"{API}/cycles", headers=acc.h, json={"start_date": "2026-01-01"})
    assert await r.get(dashboard_cache_key(acc.user_id)) is None
    assert await _runs(sessionmaker_) == [("invalidate_dashboard_cache", "done", 1, None)]


async def test_delete_also_emits_event(client, sessionmaker_):
    acc = await signup(client)
    cid = (await client.post(f"{API}/cycles", headers=acc.h, json={"start_date": "2026-01-01"})).json()["id"]
    await get_redis_client().set(dashboard_cache_key(acc.user_id), "stale")
    await client.delete(f"{API}/cycles/{cid}", headers=acc.h)
    assert await get_redis_client().get(dashboard_cache_key(acc.user_id)) is None
    assert len(await _runs(sessionmaker_)) == 2  # one run per distinct event


async def test_handlers_are_idempotent_per_event(client, sessionmaker_, isolated_registry):
    acc = await signup(client)
    calls = []

    @on("test.event")
    async def counting_handler(event, redis):
        calls.append(event.id)

    ev = DomainEvent("test.event", uuid.UUID(acc.user_id), {})
    r = get_redis_client()
    await run_handlers(ev, r)
    await run_handlers(ev, r)  # redelivery
    assert len(calls) == 1
    assert await _runs(sessionmaker_) == [("counting_handler", "done", 1, None)]


async def test_failed_handler_is_recorded_isolated_and_retried(client, sessionmaker_, isolated_registry):
    acc = await signup(client)
    state = {"fail": True, "other": 0}

    @on("test.flaky")
    async def flaky_handler(event, redis):
        if state["fail"]:
            raise RuntimeError("boom")

    @on("test.flaky")
    async def healthy_handler(event, redis):
        state["other"] += 1

    ev = DomainEvent("test.flaky", uuid.UUID(acc.user_id), {})
    with pytest.raises(HandlersFailed, match="flaky_handler"):
        await run_handlers(ev, get_redis_client())
    runs = {r[0]: r for r in await _runs(sessionmaker_)}
    assert runs["flaky_handler"][1] == "failed" and "boom" in runs["flaky_handler"][3]
    assert runs["healthy_handler"][1] == "done"  # one failure does not stop other handlers
    state["fail"] = False
    await run_handlers(ev, get_redis_client())  # retry
    runs = {r[0]: r for r in await _runs(sessionmaker_)}
    assert runs["flaky_handler"][1:3] == ("done", 2) and state["other"] == 1


async def test_event_for_deleted_user_is_skipped_quietly(client):
    ev = DomainEvent("record.confirmed", uuid.uuid4(), {})
    await run_handlers(ev, get_redis_client())  # no FK crash


async def test_event_json_roundtrip():
    ev = DomainEvent("record.confirmed", uuid.uuid4(), {"a": 1})
    assert DomainEvent.from_json(ev.to_json()) == ev


async def test_publish_via_arq_queue_and_worker(client, sessionmaker_, monkeypatch):
    """Production path: request enqueues to Redis; a separate ARQ worker processes it."""
    monkeypatch.setattr(get_settings(), "events_inline", False)
    acc = await signup(client)
    r = get_redis_client()
    await r.set(dashboard_cache_key(acc.user_id), "stale")
    await client.post(f"{API}/cycles", headers=acc.h, json={"start_date": "2026-01-01"})
    # nothing ran inline
    assert await r.get(dashboard_cache_key(acc.user_id)) == "stale"
    assert await _runs(sessionmaker_) == []
    rs = RedisSettings.from_dsn(get_settings().redis_url)
    pool = await create_pool(rs)
    queued = await pool.queued_jobs()
    assert len(queued) == 1 and queued[0].function == "process_event"
    worker = Worker(functions=[process_event], redis_settings=rs, burst=True, max_jobs=5,
                    handle_signals=False)
    await worker.main()
    await worker.close()
    await pool.aclose()
    assert await r.get(dashboard_cache_key(acc.user_id)) is None
    assert await _runs(sessionmaker_) == [("invalidate_dashboard_cache", "done", 1, None)]
    await bus.close_pool()
