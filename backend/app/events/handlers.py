"""Event handlers. ZIP 2 ships one real handler (cache invalidation). Analytics handlers
(patterns, deviations, twin, graph) are added in later milestones by registering with @on(...)."""
from redis.asyncio import Redis

from app.events.bus import DomainEvent, on

RECORD_EVENTS = ("record.confirmed", "record.deleted")


def dashboard_cache_key(user_id) -> str:
    return f"dash:{user_id}"


@on(*RECORD_EVENTS)
async def invalidate_dashboard_cache(event: DomainEvent, redis: Redis) -> None:
    await redis.delete(dashboard_cache_key(event.user_id))
