# Mobile app (ZIP 3)

React Native (Expo SDK 58, dev client) + TypeScript (strict) + React Navigation + React Native Paper + TanStack Query +
React Hook Form + Zod + Axios. Android and iOS from one codebase.

## What it does today
| Area | Screens / behaviour |
|---|---|
| Onboarding | 3 pages, shown once; states plainly that the app is wellness awareness, not diagnosis |
| Auth | Sign in, register (all consents **off** by default), forgot/reset password, silent session restore, offline-aware start |
| Today | Real cycle facts (cycle day from your last period, average cycle length), 7-day sleep and mood bars, recent symptoms. **No predictions** (ML arrives in a later milestone). |
| Cycle | Month calendar with logged period days, history, add/edit/delete period |
| Log | Symptom, sleep and lifestyle (one entry per day, edit-in-place), mood with tags, recent entries |
| Me | Health profile, privacy and consent switches, AI and data-sharing settings, access history, export my data (share sheet), delete account, light/dark/system theme |
| Cross-cutting | Loading / error / offline / empty states, consent gate driven by the server's `consent_required`, form validation mirroring the backend, accessibility labels, WCAG-AA-tested palette |

Not built yet (later milestones): chatbot, voice, Symptom Detective, Digital Twin, patterns, deviations, Time Machine UI,
wearables, planner, reports, knowledge graph, memory, notifications, predictions.

## Security design
* Only the **refresh token** is persisted, in the OS keychain/keystore (`expo-secure-store`, device-only, when-unlocked).
* The short-lived **access token lives in memory only**.
* On 401 the client refreshes **once, shared by all concurrent requests** (refresh tokens are single-use), stores the rotated token,
  retries, and signs the user out only if the server rejects the refresh token (never just because the phone is offline).
* Logging out or an ended session clears the query cache so one user's health data never lingers for the next.
* No secrets in the bundle: only `EXPO_PUBLIC_API_BASE_URL` (a public URL) is embedded.
* API types are **generated from the backend's real OpenAPI document**; a test fails if the app calls a route the backend lacks.

## Run
```bash
cd mobile
npm ci
cp .env.example .env                 # set EXPO_PUBLIC_API_BASE_URL (emulator: http://10.0.2.2:8000/api/v1)
npx expo start                       # Expo Go works for everything implemented so far
```
Backend: see `backend/README.md` (`alembic upgrade head`, `uvicorn app.main:app`). Use HTTPS for any non-emulator backend.

## Quality gates
```bash
npm run typecheck     # tsc --noEmit (strict, noUncheckedIndexedAccess)
npm run lint          # eslint (expo config + React Compiler rules)
npm test              # 170 tests (unit, component, screen, navigation, contract)
npm run bundle        # real Metro production bundle for Android (Hermes bytecode)
bash ../scripts/mobile_e2e.sh   # the app's REAL API layer against a LIVE backend + PostgreSQL (6 tests)
npm run gen:api       # regenerate src/types/api.generated.ts after the backend contract changes
```

## Build installable apps (not done in the authoring sandbox)
```bash
npm i -g eas-cli && eas login
eas build -p android --profile preview      # APK for direct install
eas build -p android --profile production   # AAB for Google Play
eas build -p ios --profile production       # needs an Apple Developer account ($99/yr)
eas submit -p ios                           # TestFlight
```
Set `EXPO_PUBLIC_API_BASE_URL` per profile (EAS environment variables). `com.example.wellness` identifiers in `app.config.ts`
must be replaced with your own before store submission.

## Not verified here
Running on a physical phone/emulator or in Expo Go, native date-picker behaviour, secure-store on a real keychain, screen-reader
(TalkBack/VoiceOver) walkthroughs, EAS builds, store submission, layouts on small/large screens, performance. See `docs/status/STATUS.md`.
