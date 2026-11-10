#!/usr/bin/env bash
# End-to-end smoke test: fresh DB -> migrations -> real uvicorn server + real ARQ worker -> HTTP calls.
# Requires local PostgreSQL + Redis (scripts/dev_services.sh). Uses a throw-away database.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT/backend"
DB=wellness_smoke
su postgres -c "psql -qc 'drop database if exists $DB'" >/dev/null 2>&1
su postgres -c "psql -qc 'create database $DB owner wellness'" >/dev/null
export DATABASE_URL=postgresql+asyncpg://wellness:testpw@localhost:5432/$DB REDIS_URL=redis://localhost:6379/14
export APP_ENV=development EVENTS_INLINE=false
export JWT_SECRET="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export FIELD_ENCRYPTION_KEY="$(python -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')"
redis-cli -n 14 flushdb >/dev/null
alembic upgrade head 2>&1 | tail -1
uvicorn app.main:app --port 8765 --log-level warning >/tmp/uv.log 2>&1 < /dev/null & UV=$!
arq app.tasks.worker.WorkerSettings >/tmp/arq.log 2>&1 < /dev/null & AQ=$!
trap 'kill $UV $AQ 2>/dev/null' EXIT
for i in $(seq 1 40); do curl -s localhost:8765/health >/dev/null && break; sleep 0.5; done
B=localhost:8765/api/v1; H='content-type: application/json'; PW='Violet-Harbor-Lamp-42'
echo "health : $(curl -s localhost:8765/health)"
echo "ready  : $(curl -s localhost:8765/ready)"
echo "register: $(curl -s -X POST $B/auth/register -H "$H" -d "{\"email\":\"smoke@example.com\",\"password\":\"$PW\",\"display_name\":\"Smoke\",\"consents\":[{\"purpose\":\"health_tracking\",\"granted\":true}]}" | head -c 120)"
TOK=$(curl -s -X POST $B/auth/login -H "$H" -d "{\"email\":\"smoke@example.com\",\"password\":\"$PW\"}" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
echo "cycle  : $(curl -s -X POST $B/cycles -H "authorization: Bearer $TOK" -H "$H" -d '{"start_date":"2026-10-01","notes":"smoke"}' | head -c 120)"
sleep 3
echo "pipeline_runs : $(PGPASSWORD=testpw psql -h localhost -U wellness -d $DB -tAc "select handler||' '||status||' attempts='||attempts from pipeline_runs")"
echo "timeline rows : $(PGPASSWORD=testpw psql -h localhost -U wellness -d $DB -tAc 'select count(*) from timeline_events')"
echo "notes at rest : $(PGPASSWORD=testpw psql -h localhost -U wellness -d $DB -tAc 'select left(notes,12) from cycle_records')"
echo "no token      : HTTP $(curl -s -o /dev/null -w '%{http_code}' $B/cycles)"
echo "bad register  : $(curl -s -X POST $B/auth/register -H "$H" -d '{"email":"x@example.com","password":"short","display_name":"x"}' | head -c 150)"
