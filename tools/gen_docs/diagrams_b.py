"""Diagram definitions 11-20."""

DIAGRAMS_B = [
    {
        "n": 11, "slug": "11-adaptive-wellness-planner-workflow", "title": "Adaptive Wellness Planner Workflow",
        "mermaid": """flowchart TB
    NL["Natural-language schedule<br/>college 9-4, dance 6pm"] --> PRS["Schedule parser<br/>LLM to JSON time blocks"]
    PRS --> CONF["User confirms parsed blocks"]
    CONF --> SB[("schedule_blocks")]
    CTX["Recent sleep, mood, activity<br/>+ preferences from memory"] --> CAND["Candidate activities<br/>rule library"]
    SB --> SLOT["Constraint-based slot filler<br/>deterministic"]
    CAND --> SLOT
    SLOT --> PLN[("daily_plans + plan_items")]
    PLN --> UI["Plan screen"]
    UI -->|done / skip / reject / edit| FB[("plan_feedback")]
    FB --> PREF["Preference learning<br/>weights per activity"]
    PREF --> CAND
    NEWD["New data or schedule change"] --> ADAPT["Re-plan remaining day"]
    ADAPT --> SLOT""",
        "components": [
            ("Schedule parser", "LLM only converts free text to time blocks; output is shown for confirmation."),
            ("Rule library", "Curated, referenced suggestions (movement, hydration, wind-down, meals). No cycle-phase restrictions."),
            ("Slot filler", "Deterministic algorithm placing activities in free time within duration/buffer constraints."),
            ("Feedback + preference learning", "Accept/skip/reject updates per-activity weights."),
            ("Adaptation", "Re-plans the rest of the day when data or schedule changes."),
        ],
        "flow": "Parse -> confirm -> generate candidates from recent data and preferences -> place into free slots -> user acts on items -> feedback updates weights -> next plan reflects them.",
        "tech": [
            ("Deterministic scheduler (Python)", "Testable and predictable; LLM is not trusted with timing."),
            ("Simple weighted preference model", "Works with tiny feedback volumes."),
        ],
        "comms": "Core planner module; ML engine for parsing and optional ranking; reads memory preferences.",
        "security": "Schedule text is personal data: egress gate applies; stored encrypted.",
        "example": "'College 9-4, dance 6pm' -> free windows 4-6pm and after 7:30pm; plan places a 20-min walk at 4:15pm, hydration reminders, and a wind-down at 10pm.",
    },
    {
        "n": 12, "slug": "12-doctor-visit-report-generation-workflow", "title": "Doctor-Visit Report Generation Workflow",
        "mermaid": """flowchart LR
    SEL["User selects period + sections"] --> PRV["POST /reports/preview"]
    PRV --> COL["Collector<br/>reads confirmed records only"]
    COL --> CHT["Charts<br/>matplotlib to PNG"]
    COL --> QST["Suggested questions<br/>template library"]
    CHT --> ASM["Report assembler"]
    QST --> ASM
    ASM --> PREV["Preview JSON/HTML"]
    PREV --> EDT["User edits notes + questions"]
    EDT --> GEN["POST /reports/id/generate<br/>ReportLab PDF"]
    GEN --> CHK["Content check<br/>no diagnostic phrases"]
    CHK --> S3[("S3 / MinIO<br/>encrypted")]
    S3 --> DL["Download"]
    S3 --> SHR["Share link<br/>expiring token + revoke"]""",
        "components": [
            ("Collector", "Reads only records the user selected and confirmed."),
            ("Chart renderer", "Server-side charts embedded in the PDF."),
            ("Question library", "Template questions chosen from observed patterns."),
            ("Preview + edit", "User can edit free-text notes and questions; recorded data stays read-only."),
            ("Content check", "Automated test blocks diagnostic wording."),
            ("Sharing", "Hashed tokens with expiry, revocation, and access count."),
        ],
        "flow": "Select -> preview -> edit -> generate PDF -> store in encrypted object storage -> download or share by revocable link.",
        "tech": [
            ("ReportLab", "Precise, professional PDF layout in Python."),
            ("matplotlib", "Chart images for PDF."),
            ("S3 / MinIO", "Encrypted file storage with presigned access."),
        ],
        "comms": "Core reports module (async job for generation); reads timeline, patterns, deviations.",
        "security": "Sharing is explicit and revocable; share events are audit-logged; links store only token hashes.",
        "example": "Last 3 months: cycle table, symptom frequency, sleep/mood trends, 5 suggested questions; user edits one note and shares for 7 days.",
    },
    {
        "n": 13, "slug": "13-personal-health-knowledge-graph-architecture", "title": "Personal Health Knowledge Graph Architecture",
        "mermaid": """flowchart TB
    SRC["Sources: symptom_logs, cycle_records,<br/>lifestyle, mood, pattern_observations,<br/>anomaly_events, recommendations"] --> UPS["Graph upsert handler<br/>event-driven"]
    UPS --> ENT[("kg_entities<br/>type, ref_table, ref_id")]
    UPS --> EDG[("kg_edges<br/>relation, weight, evidence_ids,<br/>explanation_key")]
    GR["GraphRepository interface"] --> PGI["Postgres implementation<br/>recursive CTEs"]
    GR -.optional later.-> N4["Neo4j implementation"]
    PGI --> ENT
    PGI --> EDG
    API["GET /graph/subgraph"] --> GR
    CHATCTX["Chat context builder"] --> GR
    API --> VIS["Mobile graph view"]
    EDG --> EXP["Explanation: why this edge exists<br/>+ underlying records"]""",
        "components": [
            ("Upsert handler", "Creates entities and edges from confirmed records and detected patterns."),
            ("kg_entities / kg_edges", "Typed nodes referencing source rows; edges carry weight, evidence IDs, and an explanation key."),
            ("GraphRepository", "Interface so storage can change without touching callers."),
            ("Postgres implementation", "Recursive CTEs for 2-3 hop traversal."),
            ("Neo4j implementation (optional)", "Not shipped by default; added only if variable-depth traversal at scale is needed."),
            ("Context builder", "Feeds relevant subgraph facts to chat (allowlisted)."),
        ],
        "flow": "Event -> upsert nodes/edges -> API returns a user-scoped subgraph -> UI draws it and each edge can show its evidence -> chat can retrieve connected facts.",
        "tech": [
            ("PostgreSQL recursive CTEs", "Per-user graphs are small; no extra database to operate."),
            ("Neo4j (deferred)", "Valuable for deep traversal across large graphs; documented trade-off, not added for appearance."),
        ],
        "comms": "Internal core module; ML engine receives graph-derived context only when building chat prompts.",
        "security": "All traversals scoped to one user_id; edges always reference real records; deletion cascades with account erasure.",
        "example": "Edge 'poor sleep -> fatigue (lag 1d)' links to 9 sleep logs and 7 fatigue entries; tapping it lists them.",
    },
    {
        "n": 14, "slug": "14-rag-and-evidence-engine-architecture", "title": "RAG and Evidence Engine Architecture",
        "mermaid": """flowchart TB
    subgraph OFFLINE["Offline ingestion"]
        DOC["Fetched documents<br/>WHO, NHS, govt, institutions"] --> MAN["manifest.json<br/>url, org, retrieved_at, license"]
        DOC --> CHK["Chunk + checksum"]
        CHK --> EMB["Sentence Transformers"]
        EMB --> QD[("Qdrant")]
        MAN --> ES[("evidence_sources")]
    end
    Q["User question"] --> SAFE["Safety + scope check"]
    SAFE -->|urgent| FIXED["Fixed safety message"]
    SAFE --> RET["Retrieve top-k chunks"]
    RET --> QD
    PERS["Personal context<br/>allowlisted observations"] --> PRM["Prompt builder<br/>answer only from context"]
    RET --> PRM
    PRM --> GATE["Egress gate"] --> LLM["LLM"]
    LLM --> TAG["Segment tagger"]
    TAG --> OUT["Segments with type + sources"]
    OUT --> VER["Citation verifier<br/>every cited id exists"]""",
        "components": [
            ("Ingestion", "Only documents actually fetched and stored; manifest records URL, publisher, date, license, checksum."),
            ("Qdrant", "Vector index of chunks with source metadata."),
            ("Safety + scope check", "Urgent symptoms and diagnosis requests are intercepted or refused."),
            ("Prompt builder", "Instructs the model to answer only from retrieved context and personal records."),
            ("Segment tagger", "Labels each segment: supported evidence / general wellness / personal observation / hypothetical / uncertain."),
            ("Citation verifier", "Rejects any citation not present in evidence_sources, preventing fabricated references."),
        ],
        "flow": "Question -> safety -> retrieval -> prompt (evidence + allowed personal facts) -> LLM -> tag segments -> verify citations -> return segments with sources and an uncertainty note when retrieval is weak.",
        "tech": [
            ("Sentence Transformers", "Local embeddings; no text sent out for vectorization."),
            ("Qdrant", "Filterable vector search with payload metadata."),
            ("Custom RAG (no LangChain)", "Small, auditable pipeline."),
        ],
        "comms": "Core chat gateway -> ML engine /v1/chat/respond; engine -> Qdrant, LLM adapter.",
        "security": "Egress gate; personal context only from user allowlist; KB provenance tracked; no fabricated references.",
        "example": "'Is a 35-day cycle normal?' -> retrieved guidance chunk (cited) + personal note 'your last 3 cycles were 33-36 days' + advice to discuss persistent variation with a clinician.",
    },
    {
        "n": 15, "slug": "15-privacy-and-security-architecture", "title": "Privacy and Security Architecture",
        "mermaid": """flowchart TB
    CL["Client"] -->|TLS| EDGE["Nginx"]
    EDGE --> AUTHN["Authentication<br/>JWT access + rotating refresh"]
    AUTHN --> AUTHZ["Authorization<br/>RBAC + ownership checks"]
    AUTHZ --> CONS["Consent check per purpose"]
    CONS --> SVC["Service layer"]
    SVC --> ENC["Field encryption<br/>AES-GCM envelope keys"]
    ENC --> DB[("PostgreSQL<br/>encrypted at rest")]
    SVC --> AUD["Append-only audit log"]
    SVC --> EG{"Egress gate"}
    EG -->|consent + allowlist ok| EXT["External or local LLM"]
    EG -->|otherwise| BLK["Blocked + logged"]
    SVC --> EXP["Export / erasure jobs"]
    SVC --> ACC["Access history view"]""",
        "components": [
            ("JWT + refresh rotation", "Short-lived access tokens, revocable refresh tokens, Redis denylist."),
            ("RBAC + ownership", "Role plus per-row user_id enforcement."),
            ("Consent check", "Purposes: health_tracking, ml_processing, llm_external, analytics."),
            ("Field encryption", "Application-level AES-GCM for notes, chat text, schedule text."),
            ("Audit log", "Append-only; users can view their own access history."),
            ("Egress gate", "Blocks external LLM calls unless consent, allowlist and de-identification pass."),
            ("Export / erasure", "Machine-readable export; hard-purge after soft delete."),
        ],
        "flow": "Every request passes authn -> authz -> consent before reaching services. Sensitive fields are encrypted before storage. Any outbound AI call must pass the egress gate. All sensitive actions are audit-logged.",
        "tech": [
            ("Argon2", "Password hashing."),
            ("AES-GCM (cryptography lib)", "Authenticated field encryption."),
            ("Redis", "Token denylist and rate limits."),
            ("PostgreSQL grants", "Audit table without UPDATE/DELETE privileges."),
        ],
        "comms": "Cross-cutting: applies to core, ML engine (service token), storage, and LLM adapter.",
        "security": "This diagram is the security model. Production keys come from a managed KMS/secret store; threat model documented separately in later milestones.",
        "example": "User turns off 'external AI': the next chat request is answered by the local model or declined; the blocked attempt appears in her access history.",
    },
    {
        "n": 16, "slug": "16-wellness-memory-architecture", "title": "Wellness Memory Architecture",
        "mermaid": """flowchart TB
    CONV["Conversation / settings"] --> DET["Preference proposal detector"]
    DET --> PROP[("preference_proposals<br/>pending")]
    PROP --> UIA["User approves or rejects"]
    UIA -->|approve| PREF[("user_preferences<br/>source = user_approved")]
    UIA -->|reject| DROP["Discard"]
    SW{"personalization_enabled?"} -->|no| NONE["No preferences used"]
    SW -->|yes| RET["Preference retriever"]
    PREF --> RET
    RET --> CHAT["Chat prompt: language, length, tone"]
    RET --> PLAN["Planner: food, fitness, timing"]
    RET --> NOTIF["Notification times"]
    VIEW["View / edit / delete screen"] --> PREF
    HEALTH[("Health records")] -. separate store .-> PREF""",
        "components": [
            ("Proposal detector", "Suggests preferences it noticed; it never stores them directly."),
            ("preference_proposals", "Pending items awaiting explicit approval."),
            ("user_preferences", "Approved key-value items: language, response length, diet, fitness, notification time, tone."),
            ("Master switch", "personalization_enabled turns the whole system off."),
            ("Retriever", "Selects only relevant preferences per context."),
            ("Separation rule", "Preferences are stored apart from medical/health history; sensitive health conclusions are never inferred into memory."),
        ],
        "flow": "Detect -> propose -> user approves -> stored -> retrieved by chat, planner and notifications -> user can view, edit, or delete at any time.",
        "tech": [
            ("PostgreSQL key-value tables", "Simple, transparent, exportable."),
        ],
        "comms": "Core memory module read by conversation, planner, notification services.",
        "security": "Included in export and erasure; excluded from LLM context unless the user allows it.",
        "example": "User says 'keep answers short' -> proposal appears -> she approves -> later answers are concise.",
    },
    {
        "n": 17, "slug": "17-complete-database-er-diagram", "title": "Complete Database ER Diagram",
        "mermaid": """erDiagram
    USERS ||--|| HEALTH_PROFILES : has
    USERS ||--o{ REFRESH_TOKENS : holds
    USERS ||--o{ PASSWORD_RESET_TOKENS : requests
    USERS ||--o{ USER_CONSENTS : grants
    USERS ||--o{ AUDIT_LOGS : generates
    USERS ||--o{ CYCLE_RECORDS : logs
    USERS ||--o{ SYMPTOM_LOGS : logs
    USERS ||--o{ LIFESTYLE_RECORDS : logs
    USERS ||--o{ MOOD_RECORDS : logs
    CYCLE_RECORDS ||--o{ SYMPTOM_LOGS : links
    USERS ||--o{ TIMELINE_EVENTS : owns
    USERS ||--o{ PREDICTIONS : receives
    PREDICTIONS ||--o{ EXPLANATIONS : has
    USERS ||--o{ RISK_ASSESSMENTS : receives
    USERS ||--o{ RECOMMENDATIONS : receives
    USERS ||--o{ WELLNESS_BASELINES : has
    USERS ||--o{ ANOMALY_EVENTS : has
    USERS ||--o| TWIN_PROFILES : has
    TWIN_PROFILES ||--o{ SIMULATION_SCENARIOS : runs
    USERS ||--o{ PATTERN_OBSERVATIONS : has
    USERS ||--o{ CONVERSATION_DRAFTS : drafts
    USERS ||--o{ CHAT_SESSIONS : starts
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : contains
    USERS ||--o{ WEARABLE_INTEGRATIONS : connects
    WEARABLE_INTEGRATIONS ||--o{ IMPORTED_MEASUREMENTS : supplies
    USERS ||--o{ SCHEDULE_BLOCKS : defines
    USERS ||--o{ DAILY_PLANS : receives
    DAILY_PLANS ||--o{ PLAN_ITEMS : contains
    PLAN_ITEMS ||--o{ PLAN_FEEDBACK : receives
    USERS ||--o{ KG_ENTITIES : owns
    KG_ENTITIES ||--o{ KG_EDGES : source
    EVIDENCE_SOURCES ||--o{ EVIDENCE_CHUNKS : split_into
    USERS ||--o{ USER_PREFERENCES : approves
    USERS ||--o{ PREFERENCE_PROPOSALS : reviews
    USERS ||--|| AI_SETTINGS : configures
    USERS ||--o{ GENERATED_REPORTS : owns
    GENERATED_REPORTS ||--o{ REPORT_SHARES : shared_via
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ NOTIFICATION_PREFERENCES : configures
    USERS ||--o{ PIPELINE_RUNS : triggers""",
        "components": [
            ("Identity and governance", "users, health_profiles, refresh_tokens, password_reset_tokens, user_consents, audit_logs, ai_settings."),
            ("Core records", "cycle_records, symptom_logs, lifestyle_records, mood_records."),
            ("Unified timeline", "timeline_events is the read model used by Time Machine, patterns and reports."),
            ("Intelligence outputs", "predictions (+explanations), risk_assessments, recommendations, wellness_baselines, anomaly_events, twin_profiles, simulation_scenarios, pattern_observations."),
            ("Conversation", "conversation_drafts, chat_sessions, chat_messages."),
            ("Integrations", "wearable_integrations, imported_measurements."),
            ("Planner", "schedule_blocks, daily_plans, plan_items, plan_feedback."),
            ("Graph and evidence", "kg_entities, kg_edges, evidence_sources, evidence_chunks."),
            ("Memory, reports, ops", "user_preferences, preference_proposals, generated_reports, report_shares, notifications, notification_preferences, pipeline_runs."),
        ],
        "flow": "Relationships only are drawn here to stay readable; column-level definitions, constraints and indexes are in docs/db/schema.md. Almost every table hangs off users with ON DELETE CASCADE so erasure is complete.",
        "tech": [
            ("PostgreSQL 16", "ACID relational store; JSONB, arrays, partial indexes, recursive CTEs."),
            ("Alembic", "Versioned schema changes."),
        ],
        "comms": "Accessed only by the core backend repositories (and the ARQ worker through the same repositories).",
        "security": "UUID keys, per-row ownership, encrypted free-text columns, append-only audit_logs, cascade deletion.",
        "example": "Deleting an account cascades through every user-owned table, leaving only anonymous evidence_sources (shared reference data).",
    },
    {
        "n": 18, "slug": "18-authentication-authorization-sequence", "title": "Authentication and Authorization Sequence",
        "mermaid": """sequenceDiagram
    actor U as User
    participant M as Mobile
    participant C as Core backend
    participant R as Redis
    participant DB as PostgreSQL
    U->>M: email + password
    M->>C: POST /auth/login
    C->>DB: load user, verify Argon2 hash
    C->>DB: store refresh token jti + device
    C-->>M: access JWT (15 min) + refresh token
    M->>M: save in secure store
    M->>C: GET /cycles (Bearer access)
    C->>R: check denylist (token id + session id)
    C->>C: verify signature, role, ownership
    C->>C: check consent: health_tracking
    C->>DB: query WHERE user_id = me
    C-->>M: 200 data
    Note over M,C: access token expires
    M->>C: POST /auth/refresh
    C->>DB: validate jti, rotate token
    C-->>M: new access + new refresh
    U->>M: logout
    M->>C: POST /auth/logout
    C->>R: denylist access jti
    C->>DB: revoke refresh token""",
        "components": [
            ("Login", "Verifies Argon2 hash; issues short-lived access JWT and rotating refresh token."),
            ("Refresh rotation", "Each refresh invalidates the old token; reuse of an old token revokes the session family."),
            ("Denylist", "Redis set of revoked access token IDs until expiry."),
            ("Ownership + consent", "Checked on every protected route."),
        ],
        "flow": "Credentials -> tokens -> authenticated calls -> silent refresh -> logout revokes both tokens.",
        "tech": [
            ("JWT (HS256 or RS256)", "Stateless access checks."),
            ("Argon2", "Resistant to GPU cracking."),
            ("expo-secure-store", "OS-backed secret storage on device."),
        ],
        "comms": "Mobile <-> core only.",
        "security": "Rate-limited login, generic error messages, refresh reuse detection, audit entries for login/logout/failures.",
        "example": "Stolen old refresh token is replayed: backend detects reuse, revokes the family, and the user must log in again.",
    },
    {
        "n": 19, "slug": "19-main-application-data-flow", "title": "Main Application Data Flow (Fatigue Example)",
        "mermaid": """flowchart TB
    S1["1 Voice recording"] --> S2["2 Transcript + language"]
    S2 --> S3["3 Structured symptoms"]
    S3 --> S4["4 User confirmation"]
    S4 --> S5[("5 symptom_logs + timeline_events")]
    S5 --> EVT[["6 record.confirmed event"]]
    EVT --> H1["7 Time Machine aggregates"]
    EVT --> H2["8 Pattern detector"]
    EVT --> H3["9 Deviation detector"]
    EVT --> H4["10 Twin refit"]
    EVT --> H5["11 Graph upsert"]
    H2 --> REC["12 Recommendations + planner"]
    H3 --> REC
    H4 --> REC
    H5 --> CHAT["13 Available to AI assistant<br/>(allowlisted)"]
    S5 --> RPT["14 Selectable in doctor-visit report"]
    REC --> NTF["15 Notification if enabled"]
    EVT --> PR[("pipeline_runs: status per handler")]""",
        "components": [
            ("Steps 1-4", "Conversation and confirmation (see diagram 7)."),
            ("Step 5", "Single transactional write of records and timeline event."),
            ("Event + handlers", "Independent, idempotent handlers; each logged in pipeline_runs."),
            ("Recommendations / planner", "Consume outputs of pattern, deviation and twin handlers."),
            ("Chat and reports", "Read the same stored records; no separate copy."),
        ],
        "flow": "Confirmed data is written once, then fans out through events. Every consumer reads from the same tables, so modules stay consistent.",
        "tech": [
            ("ARQ + Redis", "Reliable async execution with retries."),
            ("pipeline_runs table", "Observability and retry of failed handlers."),
        ],
        "comms": "Core services -> Redis queue -> worker -> ML engine -> core repositories.",
        "security": "Handlers act only on the event's user_id; failures never expose data; retries are idempotent.",
        "example": "'I'm tired and have a headache' confirmed at 21:04; by 21:05 the timeline shows both, a deviation check has run, and the assistant can reference them if she allows it.",
    },
    {
        "n": 20, "slug": "20-deployment-architecture", "title": "Deployment Architecture",
        "mermaid": """flowchart TB
    DEVR["Developer push"] --> GHA["GitHub Actions<br/>lint, test, build"]
    GHA --> ECR["Container registry (ECR)"]
    GHA --> EAS["EAS Build<br/>Android AAB / iOS IPA"]
    EAS --> PLAY["Play Console"]
    EAS --> TF["TestFlight"]
    subgraph AWS["AWS"]
        subgraph EC2["EC2 host with Docker Compose"]
            NG["Nginx + TLS"]
            BE["backend"]
            WK["worker"]
            ML["ml-engine"]
            QDR["qdrant"]
            MLF["mlflow"]
            PRO["prometheus + grafana"]
        end
        RDS[("RDS PostgreSQL")]
        S3[("S3 bucket")]
        SM["Secrets Manager / KMS"]
    end
    ECR --> EC2
    NG --> BE
    BE --> RDS
    BE --> S3
    BE --> ML
    ML --> QDR
    ML --> MLF
    SM -.-> BE
    PHONE["User phone"] -->|HTTPS| NG""",
        "components": [
            ("GitHub Actions", "CI (lint, tests, image build) and deploy."),
            ("EAS Build", "Cloud builds of Android AAB/APK and iOS IPA without a local Mac."),
            ("EC2 + Docker Compose", "Single host for the demo-scale deployment; ml-engine/qdrant/mlflow stay on the internal network."),
            ("RDS PostgreSQL", "Managed database with encryption at rest and backups."),
            ("S3", "Encrypted report storage."),
            ("Secrets Manager / KMS", "Source of secrets and encryption keys in production."),
        ],
        "flow": "Push -> CI -> images to registry -> deploy on EC2; mobile builds go through EAS to Play/TestFlight. Phones reach only Nginx.",
        "tech": [
            ("Docker Compose", "Simple, reproducible; ECS/EKS only if scale requires."),
            ("Terraform or CloudFormation (planned)", "Reproducible infrastructure."),
        ],
        "comms": "Public: HTTPS to Nginx. Everything else private.",
        "security": "Security groups allow only 80/443; RDS private subnet; no secrets in images; TLS via ACM/Let's Encrypt.",
        "example": "Merge to main -> tests pass -> new backend image deployed with a rolling container restart; health endpoint confirms.",
    },
]
