# Architecture decisions (ZIP 1)

| # | Decision | Reason | Revisit when |
|---|---|---|---|
| 1 | Two backend services only: core FastAPI monolith + ML engine | Different dependencies (torch/whisper) and scaling; more services add cost without benefit | Never for this scope |
| 2 | Expo (dev client) for React Native | EAS builds Android AAB/iOS IPA without a local Mac; dev client allows native health modules | Need unsupported native code |
| 3 | `react-native-gifted-charts`, not Recharts | Recharts is web-only and does not run in React Native | - |
| 4 | No TimescaleDB | A few rows/user/day; indexed PostgreSQL is sufficient | Millions of users or high-frequency wearable streams |
| 5 | Knowledge graph in PostgreSQL behind `GraphRepository`; Neo4j optional | Per-user graphs are small with 2-3 hop queries; extra database not justified yet | Deep variable-length traversal at scale |
| 6 | No LangChain; small custom RAG pipeline | About 150 lines; avoids abstraction and version churn | - |
| 7 | ARQ (Redis) for background jobs | Async-native and lighter than Celery | Need complex workflows |
| 8 | LLM behind an adapter; local default; external only via egress gate with consent | Largest privacy risk in the system | - |
| 9 | Events (`record.confirmed`) integrate the 12 intelligence features | Avoids 12 disconnected modules; one write, many idempotent consumers, tracked in `pipeline_runs` | - |
| 10 | Digital twin = per-user Bayesian ridge on the user's own data; what-ifs are labeled hypothetical | No scientifically validated biological simulator is available; claiming one would be dishonest | A validated model exists |
| 11 | Federated learning documented, not implemented | No real distributed clients; a simulation would be decorative | Real multi-device data exists |
| 12 | Synthetic, labeled data for all ML development | No ethically cleared real dataset | Ethics-approved data obtained |
| 13 | Kannada/Telugu quality measured, not assumed; text-only replies where no verified TTS voice exists | Whisper/TTS quality varies by language | Verified voices available |

## Added in ZIP 2
| # | Decision | Reason | Revisit when |
|---|---|---|---|
| 14 | Services commit explicitly; events publish AFTER commit | Avoids events for rolled-back writes; no reliance on dependency-exit timing | Need transactional outbox for guaranteed delivery |
| 15 | Audit uses its own session/transaction | Failed requests (bad login) must still be recorded | - |
| 16 | `audit_logs.user_id` SET NULL on erasure + append-only trigger | Erasure must remove the person but keep an anonymised security trail | Legal retention rules differ |
| 17 | `user_consents` holds current state; history lives in the audit log | Simple queries; history is not lost | Need regulator-grade consent receipts |
| 18 | Refresh tokens are opaque and hashed; access JWT carries `sid` | Revocation by session family; DB leak does not expose usable tokens | - |
| 19 | Registration answers 409 for an existing email | Better UX; reveals account existence (login and reset do not) | Enumeration becomes a concern |
| 20 | Field-encryption key from an environment variable | Simple and testable; real envelope encryption needs a KMS | Production deployment (AWS KMS) |
| 21 | Export returns inline JSON | No object storage wired yet | ZIP 6 (S3 delivery) |
| 22 | Egress gate built before any LLM integration | No later code can bypass consent/scrubbing | - |

## Added in ZIP 3
| # | Decision | Reason | Revisit when |
|---|---|---|---|
| 23 | Expo SDK 58 / React Native 0.88 / React 19.3 / TypeScript 6; compatible versions taken from Expo's own `bundledNativeModules.json` | Avoids version drift between native modules | Upgrading SDK |
| 24 | TanStack Query for server state, no global store | Cache, invalidation and retry policy without hand-written reducers | Large offline-first needs |
| 25 | Only the refresh token is persisted (keychain); access token in memory | A stolen device file system yields no usable short-lived token | - |
| 26 | One shared refresh for concurrent 401s; sign out only when the server rejects the refresh token | Refresh tokens are single-use; offline must not log users out | - |
| 27 | API types generated from the backend's real OpenAPI; route-contract test | Mobile cannot silently drift from the backend | - |
| 28 | `openapi-typescript` run via `npm run gen:api` (npx), not a project dependency | It does not yet support TypeScript 6 | It does |
| 29 | Dependency-free bar chart instead of a chart library | Fewer native dependencies; Recharts is web-only | Need richer charts |
| 30 | Today screen shows computed facts only; no predictions | ML models do not exist yet; faking them is not acceptable | ZIP 4 |
| 31 | All consents default OFF at registration; ConsentGate reacts to the server's `consent_required` | Opt-in, and the server stays the single authority | - |
| 32 | Backend OpenAPI documents 400 + error envelope instead of FastAPI's 422 | The contract must describe real responses (found while generating mobile types) | - |
| 33 | `tsconfig` declares `types: ["jest", "node"]` | TypeScript 6 no longer auto-includes `@types/*` | - |
