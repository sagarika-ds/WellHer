# Database schema (design stage)

PostgreSQL 16 via SQLAlchemy 2.0 + Alembic. **Conventions** (apply to every table unless noted): UUID `id` primary key; `created_at`/`updated_at` timestamptz; user-owned tables carry `user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE` with an index on `(user_id, <time column> DESC)`; `(enc)` marks application-level AES-GCM encrypted columns.

See [diagram 17](../architecture/diagrams/17-complete-database-er-diagram.md) for relationships.

## Identity and governance

| Table | State | Purpose | Columns / constraints |
|---|---|---|---|
| `users` | **migrated (0001)** | Account | email citext UNIQUE; password_hash (Argon2id); display_name; role CHECK in (user,admin); is_active |
| `health_profiles` | **migrated (0001)** | One per user (PK = user_id) | date_of_birth; height_cm; weight_kg; typical_cycle_length; contraceptive_use; conditions_self_reported (enc, JSON list stored as encrypted text); activity_level; dietary_prefs jsonb; goals jsonb |
| `refresh_tokens` | **migrated (0001)** | Rotating opaque refresh tokens (SHA-256 hashed); family_id = access-token `sid` | token_hash UNIQUE; family_id; device; expires_at; revoked_at; replaced_by |
| `password_reset_tokens` | **migrated (0001)** | Single-use reset tokens (hashed) | token_hash UNIQUE; expires_at; used_at |
| `user_consents` | **migrated (0001)** | Current consent state: one row per (user, purpose); change history is in audit_logs | UNIQUE(user_id,purpose); purpose CHECK in (health_tracking,ml_processing,llm_external,analytics); granted; version; granted_at; revoked_at |
| `audit_logs` | **migrated (0001)** | Append-only (DB trigger); user_id is NULLed, not deleted, on account erasure | user_id NULL FK ON DELETE SET NULL; action; resource; resource_id; outcome CHECK-free varchar; ip; user_agent; request_id; details jsonb (never health values); occurred_at |
| `ai_settings` | **migrated (0001)** | One per user | personalization_enabled; external_llm_allowed; context_allowlist text[]; chat_retention_days |

## Core records

| Table | State | Purpose | Columns / constraints |
|---|---|---|---|
| `cycle_records` | **migrated (0001)** | Period start/end | start_date; end_date; flow_intensity 1-5; notes(enc). UNIQUE(user_id,start_date); CHECK end_date >= start_date |
| `symptom_logs` | **migrated (0001)** | Symptom entries | logged_at; symptom_code (ontology); severity 1-5; cycle_id NULL FK ON DELETE SET NULL; source CHECK in (manual,conversation,import). `draft_id` is added with conversation_drafts in the Detective milestone |
| `lifestyle_records` | **migrated (0001)** | Daily lifestyle | date; sleep_hours 0-24; sleep_quality 1-5; activity_minutes; water_ml; stress_level 1-5; nutrition_notes(enc). UNIQUE(user_id,date) |
| `mood_records` | **migrated (0001)** | Mood entries | logged_at; mood_score 1-5; tags text[] |
| `timeline_events` | **migrated (0001)** | Unified read model | occurred_at; kind; source_table; source_id; payload jsonb. UNIQUE(source_table,source_id); index (user_id,occurred_at DESC) |

## Intelligence outputs

| Table | State | Purpose | Columns / constraints |
|---|---|---|---|
| `predictions` | design | Model outputs | type; method CHECK in (baseline,ml); model_name; model_version; predicted_value; interval_low; interval_high; confidence; input_hash |
| `explanations` | design | Per-prediction factors | prediction_id FK; feature; contribution; direction; plain_text |
| `risk_assessments` | design | Awareness categories (no diagnoses) | category CHECK in (no_notable_pattern,worth_tracking,consider_discussing_with_clinician); factors jsonb; model_version; disclaimer_version |
| `recommendations` | design | Suggestions | category; title; body; source CHECK in (rule,ml); rule_id; status; valid_until; evidence_source_ids uuid[] |
| `wellness_baselines` | design | Personal baselines | metric; window_days; median; mad; n_obs; computed_at. UNIQUE(user_id,metric,window_days) |
| `anomaly_events` | design | Deviations | metrics text[]; started_at; method; score; status CHECK in (open,dismissed,resolved); supporting_record_ids jsonb; explanation_key |
| `twin_profiles` | design | One per user | model_version; n_days; fit_quality jsonb; coefficients jsonb; features text[]; fitted_at |
| `simulation_scenarios` | design | Hypothetical runs | twin_profile_id FK; changes jsonb; outputs jsonb; assumptions jsonb; is_hypothetical bool NOT NULL CHECK (is_hypothetical) |
| `pattern_observations` | design | Detected patterns | type; template_key; statistic; support; confidence; p_adjusted; evidence_record_ids jsonb NOT NULL |

## Conversation

| Table | State | Purpose | Columns / constraints |
|---|---|---|---|
| `conversation_drafts` | design | Unconfirmed extractions | language; transcript(enc); extracted jsonb; status CHECK in (pending,confirmed,discarded); expires_at |
| `chat_sessions` | design | Chat sessions | title; retention_expires_at |
| `chat_messages` | design | Messages | session_id FK; role; content(enc); intent; segments jsonb; retrieved_source_ids uuid[] |

## Integrations

| Table | State | Purpose | Columns / constraints |
|---|---|---|---|
| `wearable_integrations` | design | Connected platforms | platform CHECK in (apple_health,health_connect); status; granted_metrics text[]; connected_at; revoked_at |
| `imported_measurements` | design | Normalized wearable data | integration_id FK; metric; value; unit; start_at; end_at; source_app NOT NULL; source_device; dedupe_hash UNIQUE(user_id,dedupe_hash) |

## Planner

| Table | State | Purpose | Columns / constraints |
|---|---|---|---|
| `schedule_blocks` | design | User commitments | date; title(enc); start_time; end_time; origin CHECK in (parsed,manual) |
| `daily_plans` | design | A day's plan | date; rationale jsonb; generated_by. UNIQUE(user_id,date) |
| `plan_items` | design | Plan entries | plan_id FK; start_time; end_time; category; title; rule_id; status CHECK in (planned,done,skipped,rejected) |
| `plan_feedback` | design | Learning signal | plan_item_id FK; action; weight_delta |

## Graph and evidence

| Table | State | Purpose | Columns / constraints |
|---|---|---|---|
| `kg_entities` | design | Graph nodes | type; ref_table; ref_id; label. UNIQUE(user_id,ref_table,ref_id) |
| `kg_edges` | design | Graph edges | src_id FK; dst_id FK; relation; weight; evidence_ids jsonb NOT NULL; explanation_key. Indexes on (src_id),(dst_id) |
| `evidence_sources` | design | Curated KB documents (shared, not user-owned) | organization; title; url; retrieved_at; license; checksum; reviewed_by |
| `evidence_chunks` | design | KB chunks | source_id FK; chunk_index; text; qdrant_point_id |

## Memory, reports, ops

| Table | State | Purpose | Columns / constraints |
|---|---|---|---|
| `user_preferences` | design | Approved preferences | key; value; source CHECK (source = 'user_approved'); approved_at. UNIQUE(user_id,key) |
| `preference_proposals` | design | Pending proposals | key; value; reason; status CHECK in (pending,approved,rejected) |
| `generated_reports` | design | Reports | period_start; period_end; sections text[]; notes(enc); s3_key; status; checksum |
| `report_shares` | design | Share links | report_id FK; token_hash UNIQUE; expires_at; revoked_at; access_count |
| `notifications` | design | Notification inbox | type; title; body(enc); read_at |
| `notification_preferences` | design | Preferences | type; channel; schedule; enabled |
| `pipeline_runs` | **migrated (0001)** | Event handler tracking | event_id; event_type; handler; status; attempts; error; started_at; finished_at. UNIQUE(event_id,handler) |

## Design notes

- Changes made during implementation (ZIP 2): `users.deleted_at` dropped (erasure is a hard delete); `password_reset_tokens` added; `refresh_tokens` stores `token_hash` instead of `jti`; `user_consents` holds current state only; `audit_logs.user_id` is SET NULL on erasure so an anonymised trail survives.
- The 16 proposed entities were consolidated into groups: WellnessTimelineEvents became one `timeline_events` read model; KnowledgeGraphEntities/Relationships became `kg_entities`/`kg_edges`; AIConversationPreferences and UserMemoryPreferences became `ai_settings` + `user_preferences`; DigitalTwinProfiles + SimulationScenarios kept separate because a profile has many scenarios.
- `timeline_events` is a derived read model; source tables remain the source of truth. It is rebuildable from them.
- `evidence_sources`/`evidence_chunks` are shared reference data (no user_id) and are not deleted on account erasure.
- All user-owned tables cascade on user deletion (audit_logs excepted, see above); a hard-purge job also clears Redis keys, S3 objects and Qdrant payloads tied to the user.
- Free-text and sensitive columns marked (enc) use AES-GCM with envelope keys, in addition to storage-level encryption at rest.
- TimescaleDB is intentionally not used: expected volume is a few rows per user per day; plain PostgreSQL with (user_id, time DESC) indexes is sufficient.

Total tables in design: **41**; migrated so far: **13**.
