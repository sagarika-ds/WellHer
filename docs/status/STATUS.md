# Project status

## Milestone history
| ZIP | Scope | State |
|---|---|---|
| 1 | Design, 20 diagrams, DB design, API contracts, scaffold | Delivered |
| 2 | Core backend + database | Delivered |
| **3** | **Mobile application (this milestone)** | **Delivered; details below** |
| 4 | AI/ML intelligence | Not started |
| 5 | Conversational and advanced intelligence | Not started |
| 6 | Complete integrated application | Not started |

---
## Milestone: ZIP 3 - Mobile application

**Overall: a working, tested app for tracking and privacy controls, verified without a phone. It has never been run on a device or emulator. None of the 12 headline features is complete: each still needs ML/NLP work.**

### 1. Completed modules (mobile + the backend routes they use)
* Onboarding, sign in, register (opt-in consents), forgot/reset password, silent session restore, offline-aware start
* Today dashboard from real data (cycle day, average cycle length, 7-day sleep/mood bars, recent symptoms)
* Cycle calendar + history + add/edit/delete period
* Log symptom, sleep and lifestyle (edit-in-place per day), mood with tags
* Health profile, privacy and consent switches, AI/data-sharing settings, access history, data export (share sheet), account deletion
* Light/dark/system theme with a contrast-tested palette
* API layer: typed endpoints generated from the backend OpenAPI, single-flight token refresh, error normalisation
* Backend change: OpenAPI now documents the real 400 error envelope (was FastAPI's 422)

### 2. Pending
Everything intelligent or conversational (predictions, twin, patterns, deviations, Time Machine UI, Symptom Detective, chat, voice, planner, reports, graph, memory, wearables, notifications), plus device verification, EAS builds, store submission, translations.

### 3. Files created
`mobile/` (about 45 source files: app config, `src/` api, auth, theme, components, navigation, 6 screen modules, utils; 14 unit/component test suites + 1 contract test; `e2e/`), `scripts/mobile_e2e.sh`, `mobile/README.md`, generated `mobile/src/types/api.generated.ts`, `package-lock.json`.

### 4. Files modified (from ZIP 2)
`backend/app/main.py` (OpenAPI customisation), `backend/tests/test_rbac_ops.py` (+1 test), `docs/api/openapi.implemented.json` (regenerated), `.github/workflows/mobile-ci.yml` (real pipeline), `scripts/make_zip.sh` (excludes), `tools/gen_docs/*` (diagram 2 and statuses), `docs/architecture/*`, `docs/testing/TESTING.md`, `DECISIONS.md` (23-33), `README.md`.

### 5. Tests executed and results
| Check | Result |
|---|---|
| `tsc --noEmit` (strict, includes tests and e2e) | clean |
| `eslint` (expo config, React Compiler rules) | clean (0 errors, 0 warnings) |
| Jest: 15 suites | **171 passed**; line coverage 89 % (statements 87 %, branches 77 %) |
| E2E: the app's real API layer vs live backend + PostgreSQL | **6 passed** |
| Production bundle (`expo export`, Android, Hermes) | built, 4.4 MB |
| Mutation check: 15 deliberate bugs | all detected (one initially survived; a test was added and it is now caught) |
| Backend suite | **97 passed** (was 96), ruff clean |
| Design docs: 20 Mermaid diagrams parse, OpenAPI validates | yes |

### 6. Not verified
* **Never run on a phone, emulator or Expo Go; no screenshots reviewed.** Layout, spacing, small-screen behaviour and visual polish are unverified.
* Native date picker, secure-store on a real keychain, Share sheet behaviour on devices
* Screen readers (TalkBack/VoiceOver), touch-target measurement, performance
* EAS builds (APK/AAB/IPA), TestFlight, GitHub Actions run, `expo-doctor` (offline sandbox)

### 7. Known issues and limitations
1. See section 6: the biggest risk is that nothing has been seen on a real device.
2. Calendar day cells are 40 dp, below the 48 dp recommended touch target.
3. Symptoms and mood can only be logged for "now" (no backdating in the UI yet).
4. Password reset is not completable in practice: the backend does not send emails yet and the app has no deep-link handler (the user would have to paste a code).
5. Export shares JSON text through the system share sheet; very large exports may not fit. File-based export comes later.
6. Today makes six API calls; a single `/dashboard` endpoint is planned.
7. Symptom list is duplicated in the app (a test fails if it drifts from the backend ontology).
8. English only; no biometric lock; no push notifications; no session-expired message (the user just returns to sign-in).
9. Lists are capped (100 cycles, 100 history rows) without paging.
10. Placeholder bundle identifiers (`com.example.wellness`) must be replaced before store submission.
11. ESLint 9.x prints an end-of-support notice; plan an upgrade. `openapi-typescript` runs through npx because it does not support TypeScript 6 yet.
12. Backend limitations from ZIP 2 still apply (no email delivery, env-var encryption key, events lost if the process dies between commit and publish).

### 8. Architectural decisions
`docs/architecture/DECISIONS.md` (items 23-33).

### 9. ZIP archive
`womens-wellness-zip3-mobile.zip` (complete repository snapshot: ZIP 1 + 2 + mobile).

### 10. Next steps (ZIP 4: AI/ML intelligence)
Synthetic data generators with documented assumptions, cycle prediction with baselines and honest evaluation (time-split, beats rolling-mean or it is not used), wellness baselines and deviation detection, pattern detector, digital twin (per-user Bayesian ridge, hypothetical-only), recommendation rules, MLflow tracking, SHAP for tree models, the backend ML client and event handlers, and the matching mobile screens. Before that, please run the app on an emulator or phone and tell me what looks wrong.

## Feature completion matrix
A feature is complete only when frontend, backend, database and AI logic are integrated and tested.

| Feature | Status |
|---|---|
| 1 Digital Twin | Designed |
| 2 Hidden Pattern Detector | Designed |
| 3 Multilingual Symptom Detective | Designed |
| 4 Deviation Detection | Designed |
| 5 Time Machine | Designed (timeline read model exists; no UI) |
| 6 Multimodal / Wearables | Designed |
| 7 Adaptive Planner | Designed |
| 8 Doctor-Visit Report | Designed |
| 9 Knowledge Graph | Designed |
| 10 Evidence and Trust Engine | Designed |
| 11 Private Vault | **Partially implemented, tested end to end** (backend + mobile): consent, audit and access history, AI/data-sharing settings, egress gate (backend), export, erasure, encryption. No LLM path exists yet, so the "external AI" controls have nothing to govern today. Not complete. |
| 12 Wellness Memory | Designed |

---
## Previous milestone (kept for history): ZIP 2 - Core backend and database

**Overall: the backend foundation is real and tested. None of the 12 headline features is complete: each needs mobile UI and ML/NLP work that comes later.**

### 1. Completed modules (backend only)
* Authentication: register, login, refresh with rotation and reuse detection, logout, forgot/reset password, `/auth/me`
* Authorization: RBAC dependency, per-row ownership, consent gating
* Consent management (4 purposes) and AI privacy settings
* Health profile, cycles (+stats), symptoms, lifestyle (+summary), mood CRUD with validation
* `timeline_events` read model written transactionally with every record change
* Event pipeline (publish after commit, ARQ worker, idempotent handlers, `pipeline_runs`)
* Audit logging (own transaction, append-only trigger), access-history endpoint
* Egress gate for future LLM calls
* Data export (inline JSON) and account erasure
* Field-level AES-256-GCM encryption for free-text columns
* Alembic migration 0001 (13 tables), `/health`, `/ready`, `/metrics`

### 2. Pending (not started)
Mobile app, ML engine models, chat/voice, Symptom Detective, Twin, Patterns, Deviation detection, Time Machine aggregation, Wearables, Planner, Reports/PDF, Knowledge Graph, Evidence engine/RAG, Wellness Memory, notifications, dashboard endpoint, predictions/risk/recommendation endpoints, SMTP email, S3 storage. 28 of 41 designed tables are not yet migrated.

### 3. Files created
backend: 12 app packages, 13 models, repositories, 9 services, 6 routers, event bus/handlers/worker, Alembic env + migration, 9 test files; scripts: `dev_services.sh`, `smoke_test.sh`, `export_openapi.py`; docs: `backend/README.md`, `docs/testing/TESTING.md`, `docs/api/openapi.implemented.json`.

### 4. Files modified (from ZIP 1)
`backend/pyproject.toml`, `backend/Dockerfile`, `backend/app/main.py` (replaced skeleton), `docker-compose.yml` (worker added), `.env.example`, `tools/gen_docs/*` (specs updated to match implementation), regenerated `docs/api/*`, `docs/db/schema.md`, `docs/architecture/*`, `DECISIONS.md`, `README.md`, `scripts/make_zip.sh`, `.gitignore`. The old `backend/tests/test_health.py` was removed (superseded by `test_rbac_ops.py::test_health_ready_metrics`).

### 5. Tests executed and results
See `docs/testing/TESTING.md`. Summary: **96 passed**, line coverage **96 %**, `ruff` clean, `alembic check` clean, 10/10 injected bugs detected, end-to-end smoke test with real uvicorn + ARQ worker passed, OpenAPI of the running code equals the design contract for the implemented groups (test), all 20 Mermaid diagrams parse, design OpenAPI validates, `ml-engine` skeleton test passes.

### 6. Not verified
* `docker compose` / Dockerfiles (including the new `worker` service and migration-on-start): written, never run
* GitHub Actions workflows: the backend workflow now declares PostgreSQL 16 + Redis 7 service containers, but it has never run on GitHub
* nginx TLS, Prometheus scraping, Grafana
* Load, performance and penetration testing
* Diagrams are syntax-checked, not visually rendered

### 7. Known issues and limitations
1. Dependencies are version ranges, not locked. Add a lock file before production.
2. Field-encryption key comes from an environment variable (no KMS envelope encryption, no rotation tooling).
3. Password-reset **emails are not delivered** (console backend in development only; disabled in production until an email provider is integrated). The reset flow itself is tested.
4. Login rate limiting is per (email, IP). A distributed attacker is not stopped by it; no global per-account lockout (deliberate, to avoid lockout abuse). Other endpoints have no application-level rate limit (nginx config exists but is untested).
5. Access tokens are revoked via Redis; if Redis loses its data, revoked access tokens work until they expire (at most 15 minutes). Refresh tokens stay revoked (stored in PostgreSQL).
6. Registration returns 409 for an existing email (account enumeration trade-off; login and reset do not leak).
7. Health-data reads are audited one row per request: the audit table will grow; no retention policy is defined yet.
8. Erasure removes PostgreSQL rows, sessions and the dashboard cache. S3/Qdrant purging will be added when those hold user data.
9. Export is inline JSON (no S3 job); very large accounts could produce large responses.
10. A crash between commit and event publish loses the event (no transactional outbox yet). Handlers are idempotent, but a lost event is not replayed.
11. Not covered by tests: logging setup, app lifespan, console email, date-filter branches of symptom/mood/lifestyle list endpoints.
12. Symptom ontology is 24 English codes only (multilingual lexicon arrives with the Symptom Detective).

### 8. Architectural decisions
`docs/architecture/DECISIONS.md` (items 14-22 added).

### 9. ZIP archive
`womens-wellness-zip2-core-backend.zip` (complete repository snapshot, includes ZIP 1 content).

### 10. Next steps (ZIP 3: mobile app)
Expo + TypeScript app: theme (light/dark), navigation, onboarding, auth screens with secure token storage and silent refresh, consent screens, dashboard shell, tracking screens (cycle calendar, symptoms, lifestyle, mood), privacy settings, API client generated against `docs/api/openapi.implemented.json`, Jest tests, `tsc`/ESLint in CI.

## Feature completion matrix (as of ZIP 2)
A feature is complete only when frontend, backend, database and AI logic are integrated and tested.

| Feature | Status |
|---|---|
| 1 Digital Twin | Designed |
| 2 Hidden Pattern Detector | Designed |
| 3 Multilingual Symptom Detective | Designed (ontology codes + `source` column only) |
| 4 Deviation Detection | Designed |
| 5 Time Machine | Designed (timeline read model exists) |
| 6 Multimodal / Wearables | Designed |
| 7 Adaptive Planner | Designed |
| 8 Doctor-Visit Report | Designed |
| 9 Knowledge Graph | Designed |
| 10 Evidence and Trust Engine | Designed |
| 11 Private Vault | **Backend partially implemented and tested** (consent, audit, egress gate, AI settings, export, erasure, encryption). No UI, no external-LLM path yet. Not complete. |
| 12 Wellness Memory | Designed |
