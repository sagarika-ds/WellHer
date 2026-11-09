# AI-Driven Personalized Wellness and Preventive Healthcare System for Women

**Milestone: ZIP 3 - Mobile application** (builds on ZIP 1 design and ZIP 2 backend; see `docs/status/STATUS.md`).

This is a wellness and preventive-awareness project, **not** a medical diagnostic system. No model output in this
project is a diagnosis, and the design forbids presenting it as one.

## What is in this ZIP (cumulative)

| Path | Contents | State |
|---|---|---|
| `docs/architecture/` | 20 Mermaid diagrams (`.mmd`) + a document for each (components, data flow, tech and why, communication, security, example) | Written; all 20 sources pass `mermaid.parse` |
| `docs/api/` | `endpoints.md` (89 operations + 15 internal ML contracts + schemas + error codes), `openapi.yaml`, `examples.md` | Generated from one spec; OpenAPI validated |
| `docs/db/schema.md` | 40-table design with constraints and design notes | Written; ER diagram consistent with it |
| `docs/status/STATUS.md` | What is done / not done, tests, known issues | Maintained per milestone |
| `docs/architecture/DECISIONS.md` | Technology decisions with reasons | Written |
| `backend/` | **Working core backend**: auth, consent, audit, encrypted records, privacy export/erasure, event pipeline + worker, 13-table migration, 96 tests (96 % coverage). See `backend/README.md` | Run and tested against real PostgreSQL + Redis |
| `mobile/` | **Working Expo + TypeScript app**: onboarding, auth, Today, Cycle, Log, privacy and account screens; 171 tests + 6 end-to-end tests against the live backend. **Never run on a device.** See `mobile/README.md` | Typechecked, linted, tested, production bundle builds |
| `ml-engine/` | Python 3.12 FastAPI skeleton: `/health` only | Skeleton |
| `docker-compose.yml`, `.env.example`, `infra/`, `.github/workflows/` | Stack definition, env template, nginx/prometheus config, CI skeletons | Written, **not executed** (see below) |
| `tools/gen_docs/` | Single-source generators for the diagram, API and DB docs | Runs |

## What is NOT in this ZIP
No ML models, no chatbot/voice, none of the 12 advanced features beyond their backend foundations.
Those arrive in ZIPs 4-6. Folders under `backend/app/modules/`, `ml-engine/app/*` and `mobile/src/screens/{twin,patterns,timemachine,detective,wearables,planner,reports,graph,memory,vault,...}` are placeholders.

## Quick start (backend)
```bash
bash scripts/dev_services.sh                 # local PostgreSQL + Redis without Docker (Debian/Ubuntu, root)
cd backend && pip install -e ".[dev]" && pytest        # 96 tests
bash ../scripts/smoke_test.sh                # real server + real worker, end to end
```
Running the API yourself: see `backend/README.md`. Mobile: `cd mobile && npm ci && npx expo start` (see `mobile/README.md`).
Full stack: `cp .env.example .env`, replace every `CHANGE_ME`, then `docker compose up --build`.
`docker-compose.yml` and the Dockerfiles were written in a sandbox without a Docker daemon, so they have **not been
run**; expect to fix small issues on first start.

Note: run the two services' tests separately (they share the package names `app`/`tests`).

## Regenerate the docs
```bash
pip install pyyaml
python tools/gen_docs/generate.py
```
Edit `tools/gen_docs/{diagrams_a,diagrams_b,api_spec,db_spec}.py`, not the generated markdown.

## Viewing diagrams
Open any `docs/architecture/diagrams/*.md` in GitHub or VS Code with a Mermaid preview, or paste a `.mmd` file into
https://mermaid.live.
# WellHer
