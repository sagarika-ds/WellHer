from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _maker
    if _maker is None:
        _maker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _maker


async def get_session() -> AsyncIterator[AsyncSession]:
    """Request-scoped session. Services commit explicitly; an uncommitted session rolls back on close."""
    async with get_sessionmaker()() as session:
        yield session


async def dispose_engine() -> None:
    global _engine, _maker
    if _engine is not None:
        await _engine.dispose()
    _engine, _maker = None, None
