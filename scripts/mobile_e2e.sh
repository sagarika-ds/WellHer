#!/usr/bin/env bash
# Runs the mobile app's REAL API layer against a LIVE backend (fresh database, real uvicorn).
# Requires local PostgreSQL + Redis (scripts/dev_services.sh) and `npm ci` in mobile/.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB=wellness_e2e; PORT=8766
su postgres -c "psql -qc 'drop database if exists $DB'" >/dev/null 2>&1
su postgres -c "psql -qc 'create database $DB owner wellness'" >/dev/null
cd "$ROOT/backend"
export DATABASE_URL=postgresql+asyncpg://wellness:testpw@localhost:5432/$DB REDIS_URL=redis://localhost:6379/13
export APP_ENV=development EVENTS_INLINE=true LOGIN_MAX_ATTEMPTS=50
export JWT_SECRET="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export FIELD_ENCRYPTION_KEY="$(python -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')"
redis-cli -n 13 flushdb >/dev/null
alembic upgrade head 2>&1 | tail -1
uvicorn app.main:app --port $PORT --log-level warning >/tmp/uv-e2e.log 2>&1 < /dev/null & UV=$!
trap 'kill $UV 2>/dev/null' EXIT
for i in $(seq 1 40); do curl -s localhost:$PORT/health >/dev/null && break; sleep 0.5; done
cd "$ROOT/mobile"
BACKEND_URL=http://localhost:$PORT/api/v1 npx jest -c jest.e2e.config.js --runInBand --forceExit "$@"
