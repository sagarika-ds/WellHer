"""Test fixtures. Tests run against REAL PostgreSQL 16 and Redis (no mocks for the data layer).
Start them with scripts/dev_services.sh (no Docker) or `docker compose up postgres redis`."""
import base64
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://wellness:testpw@localhost:5432/wellness_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("JWT_SECRET", "test-only-secret-" + "x" * 40)
os.environ.setdefault("FIELD_ENCRYPTION_KEY", base64.b64encode(b"0123456789abcdef0123456789abcdef").decode())
os.environ["EVENTS_INLINE"] = "true"
os.environ["LOGIN_MAX_ATTEMPTS"] = "5"
os.environ["APP_ENV"] = "test"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Apply the real Alembic migrations to the test database (this also tests them)."""
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND,
                       capture_output=True, text=True, env=os.environ.copy())
    assert r.returncode == 0, r.stderr[-2000:]


@pytest_asyncio.fixture(autouse=True)
async def clean_state():
    from app.core.redis import get_redis_client
    from app.db.session import get_engine
    async with get_engine().begin() as conn:
        await conn.execute(text("TRUNCATE users CASCADE"))
    await get_redis_client().flushdb()
    yield


@pytest_asyncio.fixture
async def client():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def sessionmaker_():
    from app.db.session import get_sessionmaker
    return get_sessionmaker()
