import os
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest

BACKEND = Path(__file__).resolve().parents[1]
ADMIN = "postgresql://wellness:testpw@127.0.0.1:5432/postgres"
SCRATCH = "wellness_migtest"


def alembic(*args, db=SCRATCH):
    env = {**os.environ, "DATABASE_URL": f"postgresql+asyncpg://wellness:testpw@127.0.0.1:5432/{db}"}
    return subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env,
                          capture_output=True, text=True)


@pytest.fixture
async def scratch_db():
    conn = await asyncpg.connect(ADMIN)
    await conn.execute(f"DROP DATABASE IF EXISTS {SCRATCH}")
    await conn.execute(f"CREATE DATABASE {SCRATCH} OWNER wellness")
    await conn.close()
    yield
    conn = await asyncpg.connect(ADMIN)
    await conn.execute(f"DROP DATABASE IF EXISTS {SCRATCH}")
    await conn.close()


async def _tables():
    c = await asyncpg.connect(f"postgresql://wellness:testpw@127.0.0.1:5432/{SCRATCH}")
    rows = await c.fetch("select table_name from information_schema.tables where table_schema='public'")
    await c.close()
    return {r[0] for r in rows}


async def test_upgrade_downgrade_upgrade_on_empty_database(scratch_db):
    up = alembic("upgrade", "head")
    assert up.returncode == 0, up.stderr[-1500:]
    t = await _tables()
    assert {"users", "audit_logs", "cycle_records", "pipeline_runs", "password_reset_tokens"} <= t
    down = alembic("downgrade", "base")
    assert down.returncode == 0, down.stderr[-1500:]
    assert await _tables() == {"alembic_version"}
    assert alembic("upgrade", "head").returncode == 0


async def test_models_and_migrations_are_in_sync(scratch_db):
    assert alembic("upgrade", "head").returncode == 0
    chk = alembic("check")
    assert chk.returncode == 0 and "No new upgrade operations" in chk.stdout + chk.stderr
