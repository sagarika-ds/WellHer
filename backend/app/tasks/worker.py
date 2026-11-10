"""ARQ worker. Run:  arq app.tasks.worker.WorkerSettings"""
from typing import Any

from arq.connections import RedisSettings

import app.events.handlers  # noqa: F401  (registers handlers)
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.redis import close_redis, get_redis_client
from app.db.session import dispose_engine
from app.events.bus import DomainEvent, run_handlers


async def process_event(ctx: dict[str, Any], event: dict[str, Any]) -> None:
    await run_handlers(DomainEvent.from_json(event), get_redis_client())


async def startup(ctx: dict[str, Any]) -> None:
    configure_logging(get_settings().log_level)


async def shutdown(ctx: dict[str, Any]) -> None:
    await close_redis()
    await dispose_engine()


class WorkerSettings:
    functions = [process_event]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_tries = 3
    job_timeout = 120
