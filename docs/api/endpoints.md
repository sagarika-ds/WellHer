# API contracts (design stage)

Base path `/api/v1`. All bodies are JSON. Errors use the envelope in the last section. These are **contracts, not implementations**; status per endpoint is in `docs/status/STATUS.md`.

Auth legend: `none` public; `JWT` valid access token and ownership; `JWT+consent:<purpose>` additionally requires that consent purpose to be granted (otherwise 403 `consent_required`).

## Auth

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| POST | `/auth/register` | none | RegisterRequest | UserOut | Create account and record initial consents |
| POST | `/auth/login` | none | LoginRequest | TokenPair | Log in |
| POST | `/auth/refresh` | none | RefreshRequest | TokenPair | Rotate refresh token |
| POST | `/auth/logout` | JWT | - | Ok | Revoke current session |
| POST | `/auth/forgot-password` | none | ForgotPasswordRequest | Ok | Send reset email (always 202) |
| POST | `/auth/reset-password` | none | ResetPasswordRequest | Ok | Reset password with token |
| GET | `/auth/me` | JWT | - | UserOut | Current user |

## Profile

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/profile` | JWT | - | ProfileOut | Get health profile |
| PUT | `/profile` | JWT | ProfileIn | ProfileOut | Update health profile |

## Consent

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/consents` | JWT | - | list[ConsentOut] | List consents |
| PUT | `/consents/{purpose}` | JWT | ConsentSet | ConsentOut | Grant or revoke a consent |

## Cycles

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/cycles` | JWT+consent:health_tracking | - | list[CycleOut] | List cycles |
| POST | `/cycles` | JWT+consent:health_tracking | CycleIn | CycleOut | Log a cycle |
| PUT | `/cycles/{id}` | JWT+consent:health_tracking | CycleIn | CycleOut | Update a cycle |
| DELETE | `/cycles/{id}` | JWT+consent:health_tracking | - | Ok | Delete a cycle |
| GET | `/cycles/stats` | JWT+consent:health_tracking | - | CycleStats | Cycle statistics |

## Symptoms

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/symptoms` | JWT+consent:health_tracking | - | list[SymptomOut] | List symptom logs |
| POST | `/symptoms` | JWT+consent:health_tracking | SymptomIn | SymptomOut | Log a symptom manually |
| DELETE | `/symptoms/{id}` | JWT+consent:health_tracking | - | Ok | Delete symptom log |

## Lifestyle

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/lifestyle` | JWT+consent:health_tracking | - | list[LifestyleOut] | List daily entries |
| POST | `/lifestyle` | JWT+consent:health_tracking | LifestyleIn | LifestyleOut | Create daily entry |
| PUT | `/lifestyle/{id}` | JWT+consent:health_tracking | LifestyleIn | LifestyleOut | Update daily entry |
| GET | `/lifestyle/summary` | JWT+consent:health_tracking | - | LifestyleSummary | Summary over a period |

## Mood

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/mood` | JWT+consent:health_tracking | - | list[MoodOut] | List mood entries |
| POST | `/mood` | JWT+consent:health_tracking | MoodIn | MoodOut | Log mood |

## Predictions

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/predictions/cycle/next` | JWT+consent:ml_processing | - | CyclePrediction | Next period prediction with interval |
| GET | `/predictions/{id}/explanation` | JWT+consent:ml_processing | - | Explanation | Explanation of a prediction |

## Insights

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/insights/risk` | JWT+consent:ml_processing | - | RiskInsight | Awareness-level pattern category (not a diagnosis) |

## Recommendations

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/recommendations` | JWT | - | list[RecommendationOut] | List recommendations |
| POST | `/recommendations/{id}/feedback` | JWT | RecommendationFeedback | Ok | Record feedback |

## Chat

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| POST | `/chat/sessions` | JWT | - | ChatSessionOut | Start chat session |
| GET | `/chat/sessions` | JWT | - | list[ChatSessionOut] | List sessions |
| POST | `/chat/sessions/{id}/messages` | JWT | ChatMessageIn | ChatReply | Send a message; evidence-tagged reply |
| DELETE | `/chat/sessions/{id}` | JWT | - | Ok | Delete session and messages |

## Voice

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| POST | `/voice/query` | JWT | ConversationTurnIn | VoiceReply | Audio upload -> transcript + reply (+audio) |

## Notifications

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/notifications` | JWT | - | list[NotificationOut] | List notifications |
| PUT | `/notifications/preferences` | JWT | NotificationPrefs | NotificationPrefs | Update preferences |
| POST | `/notifications/device-token` | JWT | DeviceToken | Ok | Register push token |

## Dashboard

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/dashboard` | JWT | - | Dashboard | Home overview |

## Detective

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| POST | `/conversation/turn` | JWT+consent:health_tracking | ConversationTurnIn | ConversationTurnOut | One conversational turn (text or audio) |
| GET | `/conversation/drafts/{id}` | JWT | - | DraftOut | Get draft |
| PUT | `/conversation/drafts/{id}` | JWT | DraftEdit | DraftOut | Edit draft before confirming |
| POST | `/conversation/drafts/{id}/confirm` | JWT+consent:health_tracking | - | DraftConfirmOut | Confirm and save (only way to persist) |
| POST | `/conversation/drafts/{id}/discard` | JWT | - | Ok | Discard draft |

## Twin

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/twin` | JWT+consent:ml_processing | - | TwinOut | Digital twin status and baselines |
| POST | `/twin/simulate` | JWT+consent:ml_processing | SimulateIn | SimulateOut | Run a hypothetical what-if |
| GET | `/twin/simulations` | JWT | - | list[SimulateOut] | Past scenarios |

## Patterns

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/patterns` | JWT+consent:ml_processing | - | list[PatternOut] | List detected patterns |
| GET | `/patterns/{id}/evidence` | JWT | - | PatternEvidence | Underlying records of a pattern |
| GET | `/patterns/heatmap` | JWT | - | Heatmap | Heatmap for a metric |

## Deviations

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/deviations` | JWT+consent:ml_processing | - | list[DeviationOut] | List deviations from personal baseline |
| GET | `/deviations/{id}` | JWT | - | DeviationDetail | Deviation detail with records |
| POST | `/deviations/{id}/dismiss` | JWT | - | Ok | Dismiss |

## TimeMachine

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/timemachine` | JWT | - | TimeMachineOut | Timeline for 1m/3m/6m/1y |
| GET | `/timemachine/compare` | JWT | - | CompareOut | Compare two periods |
| GET | `/timemachine/day/{date}` | JWT | - | DayOut | All records for a date |
| GET | `/timemachine/summary` | JWT | - | SummaryOut | Summary generated from records |

## Wearables

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| POST | `/wearables/connect` | JWT | WearableConnectIn | WearableOut | Register an integration |
| DELETE | `/wearables/{id}` | JWT | - | Ok | Disconnect (optional purge) |
| POST | `/wearables/import` | JWT | ImportBatchIn | ImportBatchOut | Batch import of normalized measurements |
| GET | `/wearables/measurements` | JWT | - | list[MeasurementOut] | List imported measurements with source |
| GET | `/analytics/unified` | JWT | - | UnifiedAnalytics | Unified manual + imported analytics |

## Planner

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| POST | `/planner/schedule/parse` | JWT | ScheduleParseIn | ScheduleParseOut | Parse natural-language schedule |
| POST | `/planner/plans/generate` | JWT | PlanGenerateIn | PlanOut | Generate a daily plan |
| PATCH | `/planner/items/{id}` | JWT | PlanItemPatch | PlanItemOut | Mark done / skip / reject / edit |
| POST | `/planner/plans/{id}/adapt` | JWT | PlanAdaptIn | PlanOut | Re-plan after change |
| GET | `/planner/progress` | JWT | - | PlanProgress | Progress tracking |

## Reports

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| POST | `/reports/preview` | JWT | ReportPreviewIn | ReportPreviewOut | Preview a report |
| PUT | `/reports/{id}/notes` | JWT | ReportNotesIn | ReportPreviewOut | Edit notes/questions |
| POST | `/reports/{id}/generate` | JWT | - | ReportOut | Generate PDF (async) |
| GET | `/reports/{id}` | JWT | - | ReportOut | Report status |
| GET | `/reports/{id}/download` | JWT | - | file | Download PDF |
| POST | `/reports/{id}/share` | JWT | ShareIn | ShareOut | Create expiring share link |
| DELETE | `/reports/shares/{id}` | JWT | - | Ok | Revoke share link |

## Graph

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/graph/subgraph` | JWT+consent:ml_processing | - | SubgraphOut | User-scoped subgraph |
| GET | `/graph/edges/{id}/explanation` | JWT | - | EdgeExplanation | Why this connection exists |

## Evidence

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/evidence/sources/{id}` | JWT | - | EvidenceSourceOut | Source details for a citation |

## Vault

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/privacy/ai-settings` | JWT | - | AISettings | Read AI privacy settings |
| PUT | `/privacy/ai-settings` | JWT | AISettings | AISettings | Update AI privacy settings |
| GET | `/privacy/access-history` | JWT | - | list[AccessHistoryItem] | Access and audit history |
| POST | `/privacy/export` | JWT | - | ExportOut | Export all of the user's data (inline JSON in this milestone) |
| DELETE | `/privacy/account` | JWT | DeleteAccountIn | Ok | Erase account and data |

## Memory

| Method | Path | Auth | Request schema | Response schema | Summary |
|---|---|---|---|---|---|
| GET | `/memory/preferences` | JWT | - | list[PreferenceOut] | List approved preferences |
| PUT | `/memory/preferences` | JWT | PreferenceIn | PreferenceOut | Add/update a preference |
| DELETE | `/memory/preferences/{key}` | JWT | - | Ok | Delete a preference |
| GET | `/memory/proposals` | JWT | - | list[ProposalOut] | Pending proposals |
| POST | `/memory/proposals/{id}/approve` | JWT | - | PreferenceOut | Approve proposal |
| POST | `/memory/proposals/{id}/reject` | JWT | - | Ok | Reject proposal |
| PUT | `/memory/enabled` | JWT | MemoryEnabledIn | Ok | Turn personalization on/off |

## Internal ML engine contracts (service-token auth, private network only)

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/cycle/predict` | cycle lengths + optional features -> prediction, interval, SHAP |
| POST | `/v1/risk/assess` | aggregated features -> awareness category + factors |
| POST | `/v1/recommend` | profile + trends -> ranked candidates |
| POST | `/v1/twin/fit` | daily feature table -> twin profile (or insufficient_data) |
| POST | `/v1/twin/simulate` | twin profile + changes -> baseline vs scenario series |
| POST | `/v1/patterns/analyze` | windowed history -> patterns with evidence ids |
| POST | `/v1/deviation/detect` | history + baselines -> deviation events |
| POST | `/v1/nlp/extract` | transcript + language -> ontology-constrained symptoms |
| POST | `/v1/schedule/parse` | free text -> time blocks |
| POST | `/v1/chat/respond` | question + allowlisted context -> tagged segments + citations |
| POST | `/v1/speech/transcribe` | audio -> text + language |
| POST | `/v1/speech/synthesize` | text + language -> audio (where voice available) |
| GET | `/health` | liveness (implemented in ZIP 1) |
| GET | `/models` | registered model versions |
| GET | `/metrics` | Prometheus metrics |

## Error envelope and codes

```json
{"error": {"code": "string", "message": "string", "request_id": "string"}}
```

| HTTP | code | Meaning |
|---|---|---|
| 400 | validation_error / invalid_reset_token | Request body or query failed validation, or a password-reset token is invalid/expired/used |
| 401 | unauthenticated | Missing, invalid, expired or revoked token |
| 403 | forbidden / consent_required | Role or ownership check failed, or required consent not granted |
| 404 | not_found | Resource does not exist for this user |
| 409 | conflict | Duplicate or overlapping record |
| 422 | insufficient_data | Not enough records for the requested analysis (twin, patterns) |
| 429 | rate_limited | Too many requests |
| 502 | ml_unavailable | ML engine unreachable (feature degrades gracefully where possible) |

## Schemas

### Error

| Field | Type |
|---|---|
| error | `obj{code:str,message:str,request_id:str}` |

### RegisterRequest

| Field | Type |
|---|---|
| email | `str` |
| password | `str(min 12)` |
| display_name | `str` |
| consents | `list[ConsentChoice]` |

### LoginRequest

| Field | Type |
|---|---|
| email | `str` |
| password | `str` |
| device | `str` |

### TokenPair

| Field | Type |
|---|---|
| access_token | `str` |
| refresh_token | `str` |
| expires_in | `int` |

### RefreshRequest

| Field | Type |
|---|---|
| refresh_token | `str` |

### ForgotPasswordRequest

| Field | Type |
|---|---|
| email | `str` |

### ResetPasswordRequest

| Field | Type |
|---|---|
| token | `str` |
| new_password | `str` |

### UserOut

| Field | Type |
|---|---|
| id | `uuid` |
| email | `str` |
| display_name | `str` |
| role | `str` |

### ProfileIn

| Field | Type |
|---|---|
| date_of_birth | `date` |
| height_cm | `float` |
| weight_kg | `float` |
| typical_cycle_length | `int` |
| contraceptive_use | `bool|null` |
| conditions_self_reported | `list[str]` |
| activity_level | `str` |
| dietary_prefs | `list[str]` |
| goals | `list[str]` |

### ProfileOut

| Field | Type |
|---|---|
| user_id | `uuid` |
| date_of_birth | `date` |
| height_cm | `float` |
| weight_kg | `float` |
| typical_cycle_length | `int` |
| contraceptive_use | `bool|null` |
| conditions_self_reported | `list[str]` |
| activity_level | `str` |
| dietary_prefs | `list[str]` |
| goals | `list[str]` |

### ConsentChoice

| Field | Type |
|---|---|
| purpose | `str(health_tracking|ml_processing|llm_external|analytics)` |
| granted | `bool` |

### ConsentSet

| Field | Type |
|---|---|
| granted | `bool` |

### ConsentOut

| Field | Type |
|---|---|
| purpose | `str` |
| granted | `bool` |
| version | `str` |
| granted_at | `datetime` |
| revoked_at | `datetime|null` |

### CycleIn

| Field | Type |
|---|---|
| start_date | `date` |
| end_date | `date|null` |
| flow_intensity | `int(1-5)` |
| notes | `str|null` |

### CycleOut

| Field | Type |
|---|---|
| id | `uuid` |
| start_date | `date` |
| end_date | `date|null` |
| cycle_length_days | `int|null` |
| flow_intensity | `int` |
| notes | `str|null` |

### CycleStats

| Field | Type |
|---|---|
| n_cycles | `int (number of intervals between logged starts)` |
| mean_length | `float|null` |
| std_length | `float|null` |
| min | `int|null` |
| max | `int|null` |

### SymptomIn

| Field | Type |
|---|---|
| logged_at | `datetime` |
| symptom_code | `str` |
| severity | `int(1-5)` |
| cycle_id | `uuid|null` |

### SymptomOut

| Field | Type |
|---|---|
| id | `uuid` |
| logged_at | `datetime` |
| symptom_code | `str` |
| severity | `int` |
| cycle_id | `uuid|null` |

### LifestyleIn

| Field | Type |
|---|---|
| date | `date` |
| sleep_hours | `float` |
| sleep_quality | `int(1-5)` |
| activity_minutes | `int` |
| water_ml | `int` |
| stress_level | `int(1-5)` |
| nutrition_notes | `str|null` |

### LifestyleOut

| Field | Type |
|---|---|
| id | `uuid` |
| date | `date` |
| sleep_hours | `float` |
| sleep_quality | `int` |
| activity_minutes | `int` |
| water_ml | `int` |
| stress_level | `int` |

### LifestyleSummary

| Field | Type |
|---|---|
| period_days | `int` |
| n_entries | `int` |
| avg_sleep_hours | `float|null` |
| avg_activity_minutes | `float|null` |
| avg_stress | `float|null` |

### MoodIn

| Field | Type |
|---|---|
| logged_at | `datetime` |
| mood_score | `int(1-5)` |
| tags | `list[str]` |

### MoodOut

| Field | Type |
|---|---|
| id | `uuid` |
| logged_at | `datetime` |
| mood_score | `int` |
| tags | `list[str]` |

### CyclePrediction

| Field | Type |
|---|---|
| id | `uuid` |
| next_start_date | `date` |
| interval_low | `date` |
| interval_high | `date` |
| confidence | `float` |
| method | `str(baseline|ml)` |
| model_version | `str` |
| n_cycles_used | `int` |
| note | `str` |

### Explanation

| Field | Type |
|---|---|
| prediction_id | `uuid` |
| factors | `list[{feature:str,contribution:float,direction:str,plain_text:str}]` |
| disclaimer | `str` |

### RiskInsight

| Field | Type |
|---|---|
| category | `str(no_notable_pattern|worth_tracking|consider_discussing_with_clinician)` |
| factors | `list[str]` |
| limitations | `str` |
| model_version | `str` |

### RecommendationOut

| Field | Type |
|---|---|
| id | `uuid` |
| category | `str` |
| title | `str` |
| body | `str` |
| source | `str(rule|ml)` |
| evidence_source_ids | `list[uuid]` |

### RecommendationFeedback

| Field | Type |
|---|---|
| action | `str(helpful|not_helpful|dismissed|completed)` |

### ChatSessionOut

| Field | Type |
|---|---|
| id | `uuid` |
| created_at | `datetime` |
| title | `str|null` |

### ChatMessageIn

| Field | Type |
|---|---|
| text | `str` |
| language | `str|null` |

### ChatReply

| Field | Type |
|---|---|
| message_id | `uuid` |
| segments | `list[Segment]` |
| uncertainty_note | `str|null` |
| escalation | `bool` |

### Segment

| Field | Type |
|---|---|
| type | `str(supported_evidence|general_wellness|personal_observation|hypothetical|uncertain)` |
| text | `str` |
| source_ids | `list[uuid]` |
| record_ids | `list[uuid]` |

### VoiceReply

| Field | Type |
|---|---|
| transcript | `str` |
| language | `str` |
| reply | `ChatReply` |
| audio_url | `str|null` |

### NotificationOut

| Field | Type |
|---|---|
| id | `uuid` |
| type | `str` |
| title | `str` |
| body | `str` |
| created_at | `datetime` |
| read | `bool` |

### NotificationPrefs

| Field | Type |
|---|---|
| period_reminder | `bool` |
| reminder_time | `str(HH:MM)` |
| wellness_nudges | `bool` |
| deviation_alerts | `bool` |

### DeviceToken

| Field | Type |
|---|---|
| platform | `str(ios|android)` |
| token | `str` |

### Dashboard

| Field | Type |
|---|---|
| next_period | `CyclePrediction|null` |
| today_summary | `obj` |
| active_deviations | `int` |
| plan_progress | `obj` |
| latest_recommendations | `list[RecommendationOut]` |

### ConversationTurnIn

| Field | Type |
|---|---|
| draft_id | `uuid|null` |
| text | `str|null` |
| audio_base64 | `str|null` |
| language_hint | `str(en|hi|kn|te)|null` |

### ConversationTurnOut

| Field | Type |
|---|---|
| draft_id | `uuid` |
| transcript | `str` |
| language | `str` |
| state | `str(needs_followup|ready_to_confirm|escalation)` |
| followup_question | `str|null` |
| extracted | `list[ExtractedSymptom]` |
| escalation_message | `str|null` |

### ExtractedSymptom

| Field | Type |
|---|---|
| symptom_code | `str` |
| severity | `int|null` |
| onset | `str|null` |
| duration | `str|null` |
| source_phrase | `str` |

### DraftOut

| Field | Type |
|---|---|
| id | `uuid` |
| status | `str(pending|confirmed|discarded)` |
| extracted | `list[ExtractedSymptom]` |
| comparison_with_history | `str|null` |

### DraftEdit

| Field | Type |
|---|---|
| extracted | `list[ExtractedSymptom]` |

### DraftConfirmOut

| Field | Type |
|---|---|
| saved_symptom_ids | `list[uuid]` |
| guidance | `list[Segment]` |

### TwinOut

| Field | Type |
|---|---|
| status | `str(ready|insufficient_data)` |
| n_days | `int` |
| min_days_required | `int` |
| baselines | `list[obj]` |
| model_version | `str|null` |

### SimulateIn

| Field | Type |
|---|---|
| changes | `list[{variable:str(sleep_hours|activity_minutes|stress_level|water_ml|routine_consistency),delta:float}]` |
| horizon_days | `int` |

### SimulateOut

| Field | Type |
|---|---|
| scenario_id | `uuid` |
| is_hypothetical | `bool(always true)` |
| baseline_series | `list[obj]` |
| scenario_series | `list[obj]` |
| uncertainty_band | `obj` |
| assumptions | `list[str]` |
| factors_considered | `list[str]` |
| disclaimer | `str` |

### PatternOut

| Field | Type |
|---|---|
| id | `uuid` |
| type | `str` |
| description | `str` |
| support | `int` |
| confidence | `float` |
| p_adjusted | `float|null` |
| created_at | `datetime` |

### PatternEvidence

| Field | Type |
|---|---|
| pattern_id | `uuid` |
| records | `list[{table:str,id:uuid,date:date,summary:str}]` |

### Heatmap

| Field | Type |
|---|---|
| metric | `str` |
| axis_x | `list[str]` |
| axis_y | `list[str]` |
| values | `list[list[float]]` |

### DeviationOut

| Field | Type |
|---|---|
| id | `uuid` |
| metrics | `list[str]` |
| started_at | `date` |
| method | `str` |
| score | `float` |
| status | `str(open|dismissed|resolved)` |
| explanation | `str` |

### DeviationDetail

| Field | Type |
|---|---|
| id | `uuid` |
| explanation | `str` |
| baseline | `obj` |
| records | `list[obj]` |

### TimeMachineOut

| Field | Type |
|---|---|
| range | `str(1m|3m|6m|1y)` |
| series | `list[obj]` |
| cycle_summary | `obj` |
| symptom_frequency | `list[obj]` |
| recurring_observations | `list[PatternOut]` |

### CompareOut

| Field | Type |
|---|---|
| period_a | `obj` |
| period_b | `obj` |
| differences | `list[{metric:str,a:float,b:float,change:float}]` |

### DayOut

| Field | Type |
|---|---|
| date | `date` |
| records | `list[obj]` |
| imported | `list[obj]` |

### SummaryOut

| Field | Type |
|---|---|
| range | `str` |
| text | `str` |
| facts | `list[obj]` |
| generated_from_record_count | `int` |

### WearableConnectIn

| Field | Type |
|---|---|
| platform | `str(apple_health|health_connect)` |
| granted_metrics | `list[str]` |

### WearableOut

| Field | Type |
|---|---|
| id | `uuid` |
| platform | `str` |
| status | `str` |
| connected_at | `datetime` |
| granted_metrics | `list[str]` |

### ImportBatchIn

| Field | Type |
|---|---|
| integration_id | `uuid` |
| measurements | `list[{metric:str,value:float,unit:str,start:datetime,end:datetime,source_app:str,source_device:str|null}]` |

### ImportBatchOut

| Field | Type |
|---|---|
| accepted | `int` |
| duplicates | `int` |
| rejected | `int` |

### MeasurementOut

| Field | Type |
|---|---|
| id | `uuid` |
| metric | `str` |
| value | `float` |
| unit | `str` |
| start | `datetime` |
| source_app | `str` |
| source_device | `str|null` |

### UnifiedAnalytics

| Field | Type |
|---|---|
| range | `str` |
| metrics | `list[{metric:str,points:list[obj],sources:list[str]}]` |
| relationships | `list[PatternOut]` |

### ScheduleParseIn

| Field | Type |
|---|---|
| text | `str` |
| date | `date` |

### ScheduleParseOut

| Field | Type |
|---|---|
| blocks | `list[{title:str,start:str,end:str}]` |
| needs_confirmation | `bool` |

### PlanGenerateIn

| Field | Type |
|---|---|
| date | `date` |
| blocks | `list[obj]` |
| available_minutes | `int|null` |

### PlanOut

| Field | Type |
|---|---|
| id | `uuid` |
| date | `date` |
| items | `list[PlanItemOut]` |
| rationale | `list[str]` |

### PlanItemOut

| Field | Type |
|---|---|
| id | `uuid` |
| start | `str` |
| end | `str` |
| category | `str` |
| title | `str` |
| status | `str(planned|done|skipped|rejected)` |

### PlanItemPatch

| Field | Type |
|---|---|
| status | `str|null` |
| start | `str|null` |
| end | `str|null` |

### PlanAdaptIn

| Field | Type |
|---|---|
| reason | `str(new_schedule|new_data|user_request)` |
| new_text | `str|null` |

### PlanProgress

| Field | Type |
|---|---|
| period_days | `int` |
| completed | `int` |
| skipped | `int` |
| completion_rate | `float` |

### ReportPreviewIn

| Field | Type |
|---|---|
| period_start | `date` |
| period_end | `date` |
| sections | `list[str]` |

### ReportPreviewOut

| Field | Type |
|---|---|
| report_id | `uuid` |
| sections | `list[obj]` |
| suggested_questions | `list[str]` |

### ReportNotesIn

| Field | Type |
|---|---|
| notes | `str` |
| questions | `list[str]` |

### ReportOut

| Field | Type |
|---|---|
| id | `uuid` |
| status | `str(draft|generating|ready|failed)` |
| period_start | `date` |
| period_end | `date` |
| download_url | `str|null` |

### ShareIn

| Field | Type |
|---|---|
| expires_in_days | `int(1-30)` |

### ShareOut

| Field | Type |
|---|---|
| id | `uuid` |
| url | `str` |
| expires_at | `datetime` |

### SubgraphOut

| Field | Type |
|---|---|
| nodes | `list[{id:uuid,type:str,label:str}]` |
| edges | `list[{id:uuid,source:uuid,target:uuid,relation:str,weight:float}]` |

### EdgeExplanation

| Field | Type |
|---|---|
| edge_id | `uuid` |
| explanation | `str` |
| evidence | `list[obj]` |

### EvidenceSourceOut

| Field | Type |
|---|---|
| id | `uuid` |
| organization | `str` |
| title | `str` |
| url | `str` |
| retrieved_at | `datetime` |
| license | `str|null` |

### AISettings

| Field | Type |
|---|---|
| personalization_enabled | `bool` |
| external_llm_allowed | `bool` |
| context_allowlist | `list[str]` |
| chat_retention_days | `int` |

### AccessHistoryItem

| Field | Type |
|---|---|
| timestamp | `datetime` |
| action | `str` |
| resource | `str|null` |
| outcome | `str(success|failure|blocked)` |
| ip | `str|null` |

### ExportOut

| Field | Type |
|---|---|
| job_id | `uuid` |
| status | `str(ready)` |
| download_url | `str|null (S3 delivery in ZIP 6)` |
| data | `obj (inline JSON export in this milestone)` |

### DeleteAccountIn

| Field | Type |
|---|---|
| password | `str` |
| confirm | `str('DELETE')` |

### PreferenceIn

| Field | Type |
|---|---|
| key | `str` |
| value | `str` |

### PreferenceOut

| Field | Type |
|---|---|
| key | `str` |
| value | `str` |
| source | `str(user_approved)` |
| approved_at | `datetime` |

### ProposalOut

| Field | Type |
|---|---|
| id | `uuid` |
| key | `str` |
| value | `str` |
| reason | `str` |
| status | `str` |

### MemoryEnabledIn

| Field | Type |
|---|---|
| enabled | `bool` |

### Ok

| Field | Type |
|---|---|
| ok | `bool` |
