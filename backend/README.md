# Core backend (ZIP 2)

FastAPI + SQLAlchemy 2.0 (async) + Alembic + PostgreSQL 16 + Redis + ARQ. Python 3.12.

## What is implemented
| Area | Details |
|---|---|
| Auth | Register, login, refresh (rotating, reuse detection revokes the whole session), logout, forgot/reset password, `/auth/me` |
| Security | Argon2id hashing, JWT access tokens (15 min) with `sid`/`jti`, Redis denylist, RBAC dependency, per-row ownership, login rate limit, AES-256-GCM field encryption, uniform error envelope, request IDs, security headers |
| Consent + privacy | Per-purpose consent gating of health endpoints, AI settings (context allowlist, external-LLM switch), access history, inline JSON export, account erasure with anonymised audit trail |
| Egress gate | `services/egress.py`: the only sanctioned path for text/context destined for an LLM (consent + allowlist + scrubbing + audit). Nothing calls an LLM yet. |
| Records | Cycles (+stats), symptoms, lifestyle (+summary), mood, health profile; every write also writes `timeline_events` in the same transaction |
| Events | `record.confirmed` / `record.deleted` after commit; ARQ queue (or inline for tests); idempotent handlers tracked in `pipeline_runs`; one real handler (dashboard-cache invalidation) |
| Ops | `/health`, `/ready` (checks PostgreSQL and Redis), `/metrics` (Prometheus, route-template labels) |
| Database | 13 tables, Alembic migration `0001` (extensions, constraints, indexes, append-only audit trigger) |

Not implemented here (later milestones): ML calls, chat/voice, wearables, planner, reports, graph, memory, SMTP email, S3 storage.

## Run locally
```bash
cd backend
pip install -e ".[dev]"
cp ../.env.example .env        # replace every CHANGE_ME; see comments in the file for generating secrets
alembic upgrade head
uvicorn app.main:app --reload              # API  -> http://localhost:8000/docs
arq app.tasks.worker.WorkerSettings        # worker (needed when EVENTS_INLINE=false)
```
No Docker? `scripts/dev_services.sh` starts local PostgreSQL 16 + Redis (Debian/Ubuntu, run as root).

## Test
```bash
bash ../scripts/dev_services.sh      # or: docker compose up -d postgres redis (and create DB wellness_test)
pytest                                # 96 tests, ~50 s, real PostgreSQL + Redis, applies the real migrations
pytest --cov                          # coverage (greenlet-aware): 96 %
bash ../scripts/smoke_test.sh         # real uvicorn + real arq worker + curl, fresh database
```
Test DB defaults: `postgresql+asyncpg://wellness:testpw@127.0.0.1:5432/wellness_test`, Redis db 15 (override with env vars).

## Layout
`app/core` config, security, crypto, errors, logging · `app/models` ORM · `app/schemas` Pydantic · `app/repositories` SQL only ·
`app/services` business rules · `app/api` deps + routers · `app/events` bus + handlers · `app/tasks` ARQ worker · `app/middleware` ·
`alembic/` migrations · `tests/` unit, integration, security.

## Known limitations
See `docs/status/STATUS.md` ("Known issues").
