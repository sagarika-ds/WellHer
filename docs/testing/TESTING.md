# Testing (ZIP 2: core backend)

## How the tests are built
* Real PostgreSQL 16 and Redis. No mocked data layer. The real Alembic migrations are applied before the run.
* Each test starts from `TRUNCATE users CASCADE` and a flushed Redis db.
* The ARQ test enqueues through Redis and runs a genuine ARQ `Worker` in burst mode.
* `scripts/smoke_test.sh` additionally starts a real `uvicorn` server and a real `arq` worker process and calls the API with curl.

## Results (authoring sandbox, PostgreSQL 16.15, Redis 7.0.15, Python 3.12)
| Suite | Tests | Result |
|---|---|---|
| `test_security_unit.py` (hashing, JWT, AES-GCM, settings validation) | 11 | pass |
| `test_auth.py` (register, login, lockout, rotation, reuse detection, logout, reset flow) | 28 | pass |
| `test_consent_profile.py` | 8 | pass |
| `test_records.py` (CRUD, validation, ownership, encryption at rest, timeline lifecycle, DB constraints) | 14 | pass |
| `test_privacy_audit.py` (AI settings, history, export, erasure, append-only audit) | 9 | pass |
| `test_egress.py` (scrubbing, allowlist, consent gating, audit without payload) | 8 | pass |
| `test_events.py` (inline, idempotency, failure + retry, ARQ queue + worker) | 7 | pass |
| `test_rbac_ops.py` (RBAC, deactivation, health/ready/metrics, error envelope, OpenAPI == contract) | 9 | pass |
| `test_migrations.py` (upgrade/downgrade/upgrade, models == migration) | 2 | pass |
| **Total** | **96** | **96 passed** |

Line coverage (`pytest --cov`, greenlet-aware): **96 %** (1751 statements, 77 missed). Missed lines are mostly: logging setup,
app lifespan, the console email backend, and some list-filter branches (date filters on symptoms/mood/lifestyle).
Coverage is a measure of lines executed, not of correctness.

## Do the tests actually catch bugs? Mutation check
I injected 10 deliberate bugs, one at a time, and ran the relevant suite. All 10 were detected (then the code was restored):

| Injected bug | Detected |
|---|---|
| Repository `get` stops filtering by `user_id` | yes |
| Consent check disabled | yes |
| Refresh-token reuse no longer revokes the session family | yes |
| JWT denylist ignored | yes |
| Egress gate stops scrubbing | yes |
| Hosted LLM allowed without consent | yes |
| Login rate limiter disabled | yes |
| Timeline row not written | yes |
| Account deletion keeps data | yes |
| Field encryption stores plaintext | yes |

## Issue found by the tests during development
`test_metrics_labels_use_route_templates_not_ids` failed once because my assertion assumed a `/api/v1` prefix in metric labels;
the labels are templates without the prefix (no IDs leak). The test was corrected, not the code.

## Not covered
Load/performance tests, penetration testing, mobile tests, `docker compose` runs, and GitHub Actions execution have not been done.


---
# Testing (ZIP 3: mobile app)

## How the tests are built
* Jest (`jest-expo` preset) + React Native Testing Library 14 (async API). Only the network and native modules are mocked.
* Screens are rendered with the real theme, real react-query hooks, real forms and real validation; only `endpoints` (HTTP) and native modules (secure-store, date picker, icons) are replaced.
* The API client tests use `axios-mock-adapter` with an injected refresh transport to test token refresh precisely.
* **Contract tests read the backend:** `docs/api/openapi.implemented.json` (routes) and `backend/app/core/ontology.py` (symptom codes).
* **E2E (`scripts/mobile_e2e.sh`)**: a real `uvicorn` + fresh PostgreSQL database; the app's real axios client, interceptors and endpoint functions run in Node against it.

## Results (authoring sandbox, Node 22, no device)
| Suite | Tests |
|---|---|
| `api/client.test.ts` (bearer, refresh, rotation, single-flight, sign-out rules, no loops) | 9 |
| `api/endpoints.contract.test.ts` (every route exists in the backend OpenAPI and vice versa; params/bodies) | 34 |
| `api/errors.test.ts`, `api/queryClient.test.ts` | 5 + 3 |
| `auth/AuthContext.test.tsx` (restore, offline start, login/register/logout, cache wipe) | 9 |
| `components/components.test.tsx` (ConsentGate, calendar, chart) | 5 |
| `navigation/RootNavigator.test.tsx` (loading, offline, onboarding, signed-out, signed-in) | 5 |
| `screens/auth.screens.test.tsx` | 11 |
| `screens/tracking.screens.test.tsx` (Today, cycle, symptom, lifestyle, mood, log hub) | 16 |
| `screens/me.screens.test.tsx` (consents, AI settings, export, delete, profile, history) | 13 |
| `App.test.tsx` (boot with no network) | 2 |
| `theme/contrast.test.ts` (WCAG AA in light and dark) | 39 |
| `utils/utils.test.ts`, `utils/validation.test.ts` | 10 + 9 |
| `types/ontology.contract.test.ts` | 1 |
| **Total** | **171 passed** |
| E2E vs live backend | 6 passed |

Coverage (`jest --coverage`): lines 89 %, statements 87 %, branches 77 %. Not exercised by unit tests: native-module wiring, parts of `forms.tsx`, and `endpoints.ts` (covered by the e2e run instead).

## Mutation check (15 injected bugs)
All detected: refresh not single-flight; rotated refresh token not saved; sign-out on any refresh failure; bearer on public endpoints; offline start wipes the session; logout keeps cached health data; low-contrast primary colour; ConsentGate never gates; consents pre-ticked; delete-account without exact `DELETE`; missing sleep charted as zero; Sunday-first calendar; external-AI switch always enabled; retry of 4xx errors; **unset sleep saved as 0 instead of null**.
The last one **initially survived**: no test checked an empty sleep field. A test was added and the mutant is now caught.

## Problems found while building
* `expo-asset` (a required peer of the icon/font stack) was missing; found by a test failing to start, fixed by installing the SDK-pinned version. The production bundle step did not catch it.
* TypeScript 6 no longer auto-includes `@types/*`; `tsconfig` now declares `jest` and `node`.
* The backend's OpenAPI advertised a 422 response that the API never returns; fixed at the source (+1 backend test).
* `SafeAreaProvider` renders nothing without native layout events, so the App-level test uses the library's official mock.

## Not covered
Device or emulator runs, screenshots, accessibility audits with a screen reader, performance, EAS builds, store submission.
