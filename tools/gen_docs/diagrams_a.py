"""Diagram definitions 1-10. Each entry feeds tools/gen_docs/generate.py.

All diagrams describe the PLANNED implementation (ZIP 1 = design milestone).
"""

DIAGRAMS_A = [
    {
        "n": 1, "slug": "01-overall-system-architecture", "title": "Overall System Architecture",
        "mermaid": """flowchart TB
    APP["Mobile App<br/>React Native + Expo + TypeScript"]
    NGX["Nginx<br/>TLS + rate limit"]
    subgraph CORE["Core Backend - FastAPI modular monolith"]
        API["REST API v1"]
        SVC["Services + Repositories"]
        BUS["Event bus + ARQ worker"]
        GATE["Egress gate"]
    end
    subgraph ML["ML Engine - FastAPI"]
        CYC["Cycle / Risk / Twin"]
        PAT["Patterns / Deviation"]
        NLP["NLP / RAG / Evidence"]
        SPE["STT / TTS"]
    end
    PG[("PostgreSQL")]
    RD[("Redis")]
    QD[("Qdrant")]
    S3[("S3 / MinIO")]
    MLF["MLflow registry"]
    LLM["LLM (local default)"]
    MON["Prometheus + Grafana"]
    APP -->|HTTPS JWT| NGX --> API
    API --> SVC --> PG
    SVC --> RD
    SVC --> S3
    SVC --> BUS
    SVC -->|internal REST + service token| ML
    NLP --> QD
    ML --> MLF
    NLP --> GATE
    GATE --> LLM
    CORE --> MON
    ML --> MON""",
        "components": [
            ("Mobile app", "Only client. Talks exclusively to the core backend; never reaches the ML engine."),
            ("Nginx", "TLS termination, request rate limiting, request-ID injection."),
            ("Core backend", "Auth, records, consent, audit, orchestration, reports. Owns all user data."),
            ("Event bus + ARQ worker", "Runs post-save pipelines asynchronously (patterns, deviations, twin, graph)."),
            ("Egress gate", "Single choke point that checks consent and strips identifiers before any LLM call."),
            ("ML engine", "Stateless inference service for models, NLP, RAG, speech. Receives de-identified features."),
            ("PostgreSQL / Redis / Qdrant / S3", "Relational truth / cache + queue + denylist / vectors / PDFs."),
            ("MLflow", "Experiment tracking and model registry."),
            ("Prometheus + Grafana", "Latency, errors, inference time dashboards."),
        ],
        "flow": "App -> Nginx -> core API -> service layer -> Postgres. When intelligence is needed the service builds a minimal feature payload and calls the ML engine over a private network. Slow work is queued to the worker. LLM calls leave only via the egress gate.",
        "tech": [
            ("FastAPI", "Async, typed (Pydantic v2), automatic OpenAPI; same language across both services."),
            ("PostgreSQL", "Relational integrity for health records; JSONB for flexible payloads."),
            ("Redis", "Cache, ARQ queue broker, JWT denylist, rate limits in one component."),
            ("Qdrant", "Vector search for the curated knowledge base."),
            ("Docker Compose", "One-command local stack; same images in deployment."),
        ],
        "comms": "Mobile<->core: REST/JSON over HTTPS. Core<->ML: REST over private Docker network with service token. Core<->worker: Redis queue.",
        "security": "ML engine is not published to the host network; two-service limit keeps the attack surface small; secrets only via environment variables.",
        "example": "User opens the dashboard: app calls GET /dashboard, core reads Postgres, fetches a cached cycle prediction from Redis, returns JSON in one round trip.",
    },
    {
        "n": 2, "slug": "02-mobile-application-architecture", "title": "Mobile Application Architecture",
        "mermaid": """flowchart TB
    subgraph UI["Presentation"]
        SCR["Screens by feature"]
        CMP["Shared components<br/>forms, calendar, bar chart, states"]
        THM["Theme: light / dark / system"]
    end
    subgraph STATE["State and logic"]
        QRY["TanStack Query<br/>server cache + mutations"]
        FRM["React Hook Form + Zod"]
        AUTHC["AuthContext<br/>session lifecycle"]
    end
    subgraph DATA["Data access"]
        EPS["Typed endpoints<br/>(types generated from OpenAPI)"]
        AX["Axios client"]
        INT["Interceptors: bearer, single-flight refresh,<br/>error normalisation"]
        MEM["Access token: memory only"]
        SEC["expo-secure-store<br/>refresh token only"]
    end
    NAV["React Navigation<br/>signed-out / signed-in stacks + tabs"]
    NAV --> SCR
    SCR --> CMP
    SCR --> QRY --> EPS --> AX --> INT
    SCR --> FRM
    AUTHC --> NAV
    AUTHC --> SEC
    INT --> MEM
    INT --> SEC
    INT -->|HTTPS| BE["Core backend"]
    THM -.-> SCR""",
        "components": [
            ("Navigation", "RootNavigator chooses the tree from the auth status: splash, offline retry, onboarding, auth stack, or tabs + form screens."),
            ("Screens", "Today, Cycle, Log, Me and their forms. Later milestones add twin, patterns, time machine, detective, wearables, planner, reports, graph, memory, vault screens."),
            ("Components", "Form fields (text, date, 1-5 score, chips, switch), month calendar, dependency-free bar chart, loading/empty/error states, ConsentGate."),
            ("TanStack Query", "Caches server data, invalidates after writes, never retries 4xx, retries flaky networks twice."),
            ("React Hook Form + Zod", "Client-side validation that mirrors backend rules; the server remains the authority."),
            ("AuthContext", "Restores the session silently at start, handles login/register/logout, clears the cache on sign-out."),
            ("Typed endpoints + Axios", "Every route the app calls is listed once; a contract test checks each exists in the backend's OpenAPI document."),
            ("Interceptors", "Attach the bearer token, refresh once for all concurrent 401s, store the rotated refresh token, normalise errors."),
            ("Token storage", "Refresh token in the OS keychain/keystore; access token in memory only."),
        ],
        "flow": "Screen -> Query hook -> typed endpoint -> Axios -> interceptor adds the in-memory access token -> backend. A 401 triggers one shared refresh with the keychain refresh token; the rotated token is saved and the request retried. If the refresh token is rejected the session ends and the cache is cleared.",
        "tech": [
            ("React Native + Expo SDK 58 (dev client)", "One codebase for Android/iOS; EAS builds AAB/IPA; dev client leaves room for native health modules."),
            ("TypeScript strict + generated API types", "Compile-time contract with the backend."),
            ("React Navigation + React Native Paper", "Standard navigation and accessible Material 3 components."),
            ("TanStack Query", "Purpose-built server-state cache; avoids a hand-rolled global store."),
            ("Custom bar chart", "A few Views, no native dependency, accessible by construction; a chart library can be added when richer charts are needed (Recharts is web-only)."),
        ],
        "comms": "REST/JSON over HTTPS to the core backend only. Native modules in use: secure-store, async-storage (non-sensitive flags), date picker. HealthKit/Health Connect, audio and notifications arrive in later milestones.",
        "security": "Only the refresh token is persisted (keychain/keystore, device-only); access token in memory; cache cleared on sign-out; no secrets in the bundle; screens never log health data; offline does not sign the user out.",
        "example": "User logs sleep: form validates -> POST /lifestyle (or PUT if that day already has an entry) -> Query invalidates the lifestyle queries -> Today re-renders the sleep bars.",
    },
    {
        "n": 3, "slug": "03-primary-backend-architecture", "title": "Primary Backend Architecture",
        "mermaid": """flowchart TB
    REQ["HTTP request"] --> MW["Middleware<br/>request-id, rate limit, audit"]
    MW --> RT["Routers /api/v1"]
    RT --> DEP["Dependencies<br/>auth, RBAC, consent check"]
    DEP --> SV["Services<br/>business logic"]
    SV --> RP["Repositories<br/>SQLAlchemy 2.0"]
    RP --> DB[("PostgreSQL")]
    SV --> INT["Integrations<br/>ml_client, storage, push"]
    SV --> EV["Event publisher"]
    EV --> RDS[("Redis / ARQ")]
    RDS --> WK["Worker handlers"]
    WK --> RP
    WK --> INT
    SV --> SCH["Pydantic schemas"]
    CFG["Config + logging + exceptions"] -.-> SV""",
        "components": [
            ("Middleware", "Adds request ID, enforces rate limits, writes audit entries."),
            ("Routers", "Thin HTTP layer; validation through Pydantic v2 schemas."),
            ("Dependencies", "JWT verification, role check, per-purpose consent check."),
            ("Services", "All business rules. Feature modules: conversation, timeline, twin, patterns, deviations, wearables, planner, reports, graph, memory, privacy."),
            ("Repositories", "Only layer allowed to run SQL; async SQLAlchemy sessions."),
            ("Integrations", "ml_client (service token), S3 storage, push provider."),
            ("Event publisher + worker", "Decouples saving a record from analysis."),
        ],
        "flow": "Request -> middleware -> router -> dependencies -> service -> repository -> DB. Services publish events; the worker consumes them and writes derived data through the same repositories.",
        "tech": [
            ("SQLAlchemy 2.0 + Alembic", "Typed ORM and versioned migrations."),
            ("Pydantic v2", "Validation and serialization; OpenAPI source."),
            ("ARQ", "Async-native job queue on Redis; lighter than Celery."),
            ("Argon2", "Memory-hard password hashing."),
        ],
        "comms": "Internal calls are plain function calls (modular monolith). External: ML engine REST, S3, push, Redis.",
        "security": "Authorization at dependency level, not scattered in handlers; repositories always filter by user_id; audit middleware is append-only.",
        "example": "POST /cycles: router validates body, service checks overlap rules, repository inserts, service emits record.confirmed.",
    },
    {
        "n": 4, "slug": "04-ai-ml-service-architecture", "title": "AI/ML Service Architecture",
        "mermaid": """flowchart TB
    IN["Internal REST<br/>service-token auth"] --> RTR["Routers /v1"]
    RTR --> CY["cycle"]
    RTR --> RK["risk"]
    RTR --> TW["twin"]
    RTR --> PT["patterns"]
    RTR --> DV["deviation"]
    RTR --> RC["recommender / planner"]
    RTR --> NL["nlp: extraction, rag, evidence"]
    RTR --> SP["speech: stt, tts"]
    CY --> EX["explain: SHAP"]
    RK --> EX
    CY --> REG["registry loader"]
    RK --> REG
    DV --> REG
    REG --> MLF["MLflow"]
    NL --> QD[("Qdrant")]
    NL --> EMB["Sentence Transformers"]
    NL --> GATE["LLM adapter"]
    SP --> WH["faster-whisper"]
    SP --> PI["Piper / fallback TTS"]
    TRN["training/ offline"] --> MLF""",
        "components": [
            ("Routers", "Versioned contracts, one per capability."),
            ("cycle / risk / deviation", "Baselines first, ML only if it beats the baseline on time-split evaluation."),
            ("twin / patterns", "Per-user statistical models and association/correlation mining."),
            ("explain", "SHAP for tree models; coefficients for linear twin models."),
            ("nlp", "Ontology-constrained symptom extraction, RAG retrieval, evidence-type tagging."),
            ("speech", "faster-whisper STT; TTS where a verified voice exists."),
            ("registry", "Loads models by stage from MLflow."),
            ("training/", "Offline scripts and synthetic generators; never trains on live user data."),
        ],
        "flow": "Request carries only de-identified features. Engine loads the registered model, computes output (+ explanation), returns it. Nothing about users is persisted in the engine.",
        "tech": [
            ("scikit-learn / XGBoost", "Strong on small tabular data."),
            ("SHAP", "Feature attributions for tree models."),
            ("MLflow", "Reproducible runs and model registry."),
            ("sentence-transformers + Qdrant", "Semantic retrieval for RAG."),
            ("faster-whisper", "Fast multilingual STT; CPU int8 option."),
        ],
        "comms": "Called only by the core backend. Outbound: Qdrant, MLflow, LLM adapter.",
        "security": "Not exposed publicly; service token required; payloads carry no names/emails; audio is processed in memory and not stored by default.",
        "example": "Core posts 8 cycle lengths to /v1/cycle/predict; engine returns next-start estimate, interval, SHAP factors, model version.",
    },
    {
        "n": 5, "slug": "05-personal-wellness-digital-twin-architecture", "title": "Personal Wellness Digital Twin Architecture",
        "mermaid": """flowchart LR
    TL[("timeline_events + records")] --> FE["Feature builder<br/>daily table"]
    FE --> GATE1{"Enough data?<br/>n days threshold"}
    GATE1 -->|no| NOP["Return: not enough data"]
    GATE1 -->|yes| FIT["Per-user model<br/>Bayesian ridge on own history"]
    FIT --> TP[("twin_profiles")]
    USR["What-if request<br/>sleep +1h, stress -1 ..."] --> SIM["Scenario engine<br/>apply deltas, re-evaluate fit"]
    TP --> SIM
    SIM --> OUT["Baseline vs scenario series<br/>+ uncertainty band"]
    OUT --> LBL["Label: HYPOTHETICAL<br/>+ assumptions + factors"]
    LBL --> SC[("simulation_scenarios")]
    EVT["record.confirmed event"] --> FE""",
        "components": [
            ("Feature builder", "Aligns sleep, mood, stress, activity, symptoms, cycle day onto a daily table."),
            ("Data sufficiency gate", "Refuses to fit below a minimum number of observed days."),
            ("Per-user model", "Bayesian ridge regression of outcomes (e.g. mood, fatigue entries) on the user's own lifestyle inputs. Coefficients are the explanation."),
            ("Scenario engine", "Applies requested input changes inside the user's observed range and re-evaluates the fitted relationship."),
            ("Labeling step", "Every output is stored with is_hypothetical = true and the assumptions used."),
        ],
        "flow": "Each confirmed record triggers a feature refresh. The twin refits when enough new data exists. A what-if request reads the latest twin profile, perturbs inputs, and returns baseline-versus-scenario curves with uncertainty.",
        "tech": [
            ("scikit-learn BayesianRidge", "Gives uncertainty and works with small samples; interpretable."),
            ("Pandas / NumPy", "Daily feature table."),
            ("PostgreSQL", "twin_profiles, simulation_scenarios (CHECK is_hypothetical)."),
        ],
        "comms": "Core twin module requests ML engine /v1/twin/fit and /v1/twin/simulate; mobile reads via /twin endpoints.",
        "security": "Per-user data only; payload de-identified; consent purpose ml_processing required.",
        "example": "User asks 'what if I sleep 1 hour more?'. If her history shows higher mood on longer-sleep days, the chart shows a modest hypothetical rise with a wide band and the note 'based on associations in your own records, not a biological simulation'.",
    },
    {
        "n": 6, "slug": "06-hidden-pattern-detection-workflow", "title": "Hidden Pattern Detection Workflow",
        "mermaid": """flowchart TB
    EVT["record.confirmed"] --> LOAD["Load windowed history"]
    LOAD --> MIN{"Min support met?"}
    MIN -->|no| SKIP["No pattern reported"]
    MIN -->|yes| A["Cycle-day alignment<br/>symptom vs cycle day"]
    MIN --> B["Lagged correlation<br/>sleep vs fatigue"]
    MIN --> C["Association rules<br/>symptom co-occurrence"]
    MIN --> D["Day clustering<br/>wellness profiles"]
    A --> FDR["Multiple-testing correction"]
    B --> FDR
    C --> FDR
    D --> FDR
    FDR --> OBS["pattern_observations<br/>+ evidence_record_ids"]
    OBS --> API["GET /patterns, /patterns/id/evidence"]
    OBS --> KG["Knowledge graph upsert"]""",
        "components": [
            ("Min-support gate", "A pattern needs repeated occurrences (e.g. 3+ cycles) before it is shown."),
            ("Cycle-day alignment", "Counts when each symptom falls relative to cycle start across cycles."),
            ("Lagged correlation", "Spearman correlation with 0-2 day lags (sleep vs next-day fatigue)."),
            ("Association rules", "Apriori/FP-growth on daily symptom sets (support, confidence, lift)."),
            ("Clustering", "k-means/GMM on daily feature vectors to find recurring day types."),
            ("FDR correction", "Benjamini-Hochberg to limit false discoveries."),
            ("Evidence IDs", "Every observation stores the exact record IDs behind it."),
        ],
        "flow": "Event triggers a windowed re-analysis. Candidate patterns pass support and FDR filters, then are stored with evidence record IDs and rendered as timelines/heatmaps.",
        "tech": [
            ("SciPy / statsmodels", "Correlation and multiple-testing correction."),
            ("mlxtend", "Association rule mining."),
            ("scikit-learn", "Clustering."),
        ],
        "comms": "Worker calls ML engine /v1/patterns/analyze; results persisted by core; graph module consumes observations.",
        "security": "Runs per user; evidence IDs never leave the user's scope; wording uses 'tends to appear with', never causal language.",
        "example": "Headache entries fall on cycle days 1-2 in 3 of 3 recorded cycles: the card lists those 3 headache logs and their dates.",
    },
    {
        "n": 7, "slug": "07-multilingual-symptom-detective-workflow", "title": "Multilingual Symptom Detective Workflow",
        "mermaid": """sequenceDiagram
    actor U as User
    participant M as Mobile
    participant C as Core backend
    participant E as ML engine
    participant DB as PostgreSQL
    U->>M: speaks or types (en/hi/kn/te)
    M->>C: POST /conversation/turn (audio or text)
    C->>E: /v1/speech/transcribe
    E-->>C: text + detected language
    C->>E: /v1/nlp/extract (ontology-constrained)
    E-->>C: symptoms, severity, missing fields
    alt urgent keywords
        C-->>M: safety escalation message
    else follow-up needed
        C-->>M: follow-up question
    else complete
        C->>DB: save conversation_draft (pending)
        C-->>M: confirmation card
    end
    U->>M: confirm / edit / discard
    M->>C: POST /drafts/id/confirm
    C->>DB: write symptom_logs + timeline_events
    C-->>C: emit record.confirmed
    C-->>M: saved + educational guidance""",
        "components": [
            ("STT", "faster-whisper with language detection; reports confidence."),
            ("Extraction", "LLM constrained to a fixed multilingual symptom ontology, with lexicon/rule fallback. Unknown terms are returned as 'unrecognized', never invented."),
            ("Follow-up policy", "Asks only for missing fields (severity, onset, duration)."),
            ("Safety interceptor", "Rule-based urgent-symptom detection that runs before the LLM and returns a fixed reviewed message."),
            ("Draft store", "conversation_drafts; nothing enters health tables until user confirms."),
        ],
        "flow": "Audio/text -> transcript -> extraction -> follow-ups -> confirmation card -> explicit confirm -> structured records -> event. Server enforces that only confirmed drafts can be written.",
        "tech": [
            ("faster-whisper", "Multilingual; Kannada/Telugu accuracy will be measured, not assumed."),
            ("YAML symptom ontology (en/hi/kn/te)", "Deterministic anchor; prevents invented symptoms."),
            ("LLM adapter (local default)", "Structured JSON extraction; passes through egress gate."),
        ],
        "comms": "Mobile -> core only. Core -> ML engine for STT and extraction. Core -> Postgres for drafts and records.",
        "security": "Audio not stored by default; drafts expire; confirmation required server-side; LLM calls via egress gate.",
        "example": "'Mujhe aaj bahut thakaan hai aur sir dard bhi hai' -> fatigue + headache detected, asks severity, user confirms, two symptom_logs saved.",
    },
    {
        "n": 8, "slug": "08-wellness-deviation-detection-workflow", "title": "Wellness Deviation Detection Workflow",
        "mermaid": """flowchart TB
    EVT["record.confirmed / import"] --> BL["Update personal baseline<br/>median + MAD per metric"]
    BL --> TS["Per-metric checks"]
    TS --> Z["Robust z-score"]
    TS --> EW["EWMA control chart"]
    TS --> CP["Change-point<br/>CUSUM / ruptures"]
    BL --> MV["Isolation Forest<br/>multivariate, needs history"]
    Z --> MRG["Merge + deduplicate<br/>start time of deviation"]
    EW --> MRG
    CP --> MRG
    MV --> MRG
    MRG --> AE[("anomaly_events<br/>+ supporting_record_ids")]
    AE --> NTF["Notification (if enabled)"]
    AE --> API["GET /deviations"]""",
        "components": [
            ("Personal baseline", "Median and MAD over a rolling window of the user's own data; stored in wellness_baselines."),
            ("Univariate detectors", "Robust z-score, EWMA, CUSUM/change-point per metric (sleep, mood, activity, symptom frequency, cycle length)."),
            ("Isolation Forest", "Used only when enough multivariate history exists."),
            ("Merge step", "Combines simultaneous deviations and finds the estimated start date."),
            ("anomaly_events", "Stores method, score, status, and the records behind each event."),
        ],
        "flow": "New data updates the baseline, detectors run, results are merged into events with start time and evidence, and optionally trigger a notification. Wording: 'differs from your usual pattern', never a diagnosis.",
        "tech": [
            ("NumPy/SciPy", "Robust statistics."),
            ("ruptures", "Change-point detection."),
            ("scikit-learn IsolationForest", "Multivariate anomaly scoring."),
        ],
        "comms": "Worker -> ML engine /v1/deviation/detect; core stores events; mobile shows them in Insights.",
        "security": "Per-user baselines; thresholds documented; no disease labels.",
        "example": "Average sleep drops from ~7.2h to ~5.4h for 6 nights while fatigue entries rise: one event 'started 6 days ago: sleep duration, fatigue entries'.",
    },
    {
        "n": 9, "slug": "09-wellness-time-machine-architecture", "title": "Wellness Time Machine Architecture",
        "mermaid": """flowchart LR
    M["Mobile: range picker<br/>1m / 3m / 6m / 1y"] --> API["GET /timemachine"]
    API --> AGG["Aggregation service<br/>SQL + Pandas"]
    AGG --> TL[("timeline_events")]
    AGG --> CMP["Period comparison<br/>A vs B"]
    AGG --> REC["Recurring observations<br/>from pattern_observations"]
    CMP --> FACT["Computed fact table"]
    REC --> FACT
    FACT --> TPL["Summary templates<br/>numbers injected"]
    TPL --> OPT["Optional LLM polish<br/>numbers fixed, via egress gate"]
    OPT --> SUM["Summary text"]
    TPL --> SUM
    API --> DAY["GET /timemachine/day/date"]
    DAY --> TL""",
        "components": [
            ("timeline_events", "Unified read model fed by confirmed records and imports."),
            ("Aggregation service", "Weekly/monthly means, symptom counts, cycle stats per window."),
            ("Comparison", "Computes differences between two periods."),
            ("Fact table", "The only source of numbers used in any summary."),
            ("Template summaries", "Deterministic sentences from computed facts; LLM polishing is optional and cannot change figures."),
        ],
        "flow": "Pick a range -> aggregate -> compute comparisons -> produce facts -> render summary. Tapping a point opens the actual day records.",
        "tech": [
            ("PostgreSQL window functions", "Efficient time-bucketed aggregation without a separate time-series DB."),
            ("Pandas", "Comparison calculations."),
        ],
        "comms": "Core backend module; optionally calls ML engine for text polish.",
        "security": "All queries scoped by user_id; summaries contain only values computed from the user's records.",
        "example": "'Compared with your first month, average recorded sleep rose from 6.1h to 6.9h and fatigue entries fell from 9 to 4.'",
    },
    {
        "n": 10, "slug": "10-multimodal-data-integration-workflow", "title": "Multimodal Data Integration Workflow",
        "mermaid": """flowchart TB
    subgraph DEV["On the phone"]
        HK["Apple HealthKit"]
        HC["Android Health Connect"]
        PERM["User grants per-metric permission"]
    end
    PERM --> HK
    PERM --> HC
    HK --> RD["Read on device"]
    HC --> RD
    RD --> NRM["Normalize<br/>units, UTC time, metric codes"]
    NRM --> UP["POST /wearables/import (batch)"]
    UP --> VAL["Validate + dedupe hash"]
    VAL --> IM[("imported_measurements<br/>source_app, source_device")]
    IM --> TLE["timeline_events"]
    TLE --> UNI["Unified analytics<br/>with manual records"]
    DIS["DELETE /wearables/id"] --> REV["Revoke + stop sync<br/>optional purge"]""",
        "components": [
            ("Platform readers", "HealthKit (iOS) and Health Connect (Android) via native modules."),
            ("Permission step", "Per-metric consent; nothing is read without it."),
            ("Normalizer", "Maps platform types to internal metric codes and units."),
            ("Import API", "Idempotent batch ingestion with dedupe hash."),
            ("imported_measurements", "source_app and source_device are mandatory (attribution)."),
            ("Disconnect", "Revokes integration; user can also delete imported data."),
        ],
        "flow": "Device read -> normalize -> upload -> validate/dedupe -> store with source -> merge into the timeline -> analytics treat manual and imported data side by side, labeled by source.",
        "tech": [
            ("Expo dev client + native health modules", "Required because Expo Go cannot access HealthKit/Health Connect."),
            ("PostgreSQL", "Unique dedupe constraint."),
        ],
        "comms": "Mobile -> core /wearables/*. Not testable without a physical device; ingestion logic is unit-tested separately.",
        "security": "Minimum scopes; user can disconnect at any time; heart-rate/HRV never interpreted as hormones or diagnoses; UI states when no device is connected.",
        "example": "Watch reports 6h 12m sleep; stored with source 'Apple Watch / Health'; shown beside manual entry for that night.",
    },
]
