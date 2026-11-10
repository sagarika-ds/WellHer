"""Single source of truth for API contracts (design stage).

generate.py turns this into docs/api/endpoints.md and docs/api/openapi.yaml.
Auth values: "none" | "JWT" | "JWT+consent:<purpose>" | "service-token" (ML engine only).
"""

# name -> {field: type}. Types: str, int, float, bool, date, datetime, uuid, obj, list[...]
SCHEMAS = {
    "Error": {"error": "obj{code:str,message:str,request_id:str}"},
    "RegisterRequest": {"email": "str", "password": "str(min 12)", "display_name": "str", "consents": "list[ConsentChoice]"},
    "LoginRequest": {"email": "str", "password": "str", "device": "str"},
    "TokenPair": {"access_token": "str", "refresh_token": "str", "expires_in": "int"},
    "RefreshRequest": {"refresh_token": "str"},
    "ForgotPasswordRequest": {"email": "str"},
    "ResetPasswordRequest": {"token": "str", "new_password": "str"},
    "UserOut": {"id": "uuid", "email": "str", "display_name": "str", "role": "str"},
    "ProfileIn": {"date_of_birth": "date", "height_cm": "float", "weight_kg": "float", "typical_cycle_length": "int", "contraceptive_use": "bool|null", "conditions_self_reported": "list[str]", "activity_level": "str", "dietary_prefs": "list[str]", "goals": "list[str]"},
    "ProfileOut": {"user_id": "uuid", "date_of_birth": "date", "height_cm": "float", "weight_kg": "float", "typical_cycle_length": "int", "contraceptive_use": "bool|null", "conditions_self_reported": "list[str]", "activity_level": "str", "dietary_prefs": "list[str]", "goals": "list[str]"},
    "ConsentChoice": {"purpose": "str(health_tracking|ml_processing|llm_external|analytics)", "granted": "bool"},
    "ConsentSet": {"granted": "bool"},
    "ConsentOut": {"purpose": "str", "granted": "bool", "version": "str", "granted_at": "datetime", "revoked_at": "datetime|null"},
    "CycleIn": {"start_date": "date", "end_date": "date|null", "flow_intensity": "int(1-5)", "notes": "str|null"},
    "CycleOut": {"id": "uuid", "start_date": "date", "end_date": "date|null", "cycle_length_days": "int|null", "flow_intensity": "int", "notes": "str|null"},
    "CycleStats": {"n_cycles": "int (number of intervals between logged starts)", "mean_length": "float|null", "std_length": "float|null", "min": "int|null", "max": "int|null"},
    "SymptomIn": {"logged_at": "datetime", "symptom_code": "str", "severity": "int(1-5)", "cycle_id": "uuid|null"},
    "SymptomOut": {"id": "uuid", "logged_at": "datetime", "symptom_code": "str", "severity": "int", "cycle_id": "uuid|null"},
    "LifestyleIn": {"date": "date", "sleep_hours": "float", "sleep_quality": "int(1-5)", "activity_minutes": "int", "water_ml": "int", "stress_level": "int(1-5)", "nutrition_notes": "str|null"},
    "LifestyleOut": {"id": "uuid", "date": "date", "sleep_hours": "float", "sleep_quality": "int", "activity_minutes": "int", "water_ml": "int", "stress_level": "int"},
    "LifestyleSummary": {"period_days": "int", "n_entries": "int", "avg_sleep_hours": "float|null", "avg_activity_minutes": "float|null", "avg_stress": "float|null"},
    "MoodIn": {"logged_at": "datetime", "mood_score": "int(1-5)", "tags": "list[str]"},
    "MoodOut": {"id": "uuid", "logged_at": "datetime", "mood_score": "int", "tags": "list[str]"},
    "CyclePrediction": {"id": "uuid", "next_start_date": "date", "interval_low": "date", "interval_high": "date", "confidence": "float", "method": "str(baseline|ml)", "model_version": "str", "n_cycles_used": "int", "note": "str"},
    "Explanation": {"prediction_id": "uuid", "factors": "list[{feature:str,contribution:float,direction:str,plain_text:str}]", "disclaimer": "str"},
    "RiskInsight": {"category": "str(no_notable_pattern|worth_tracking|consider_discussing_with_clinician)", "factors": "list[str]", "limitations": "str", "model_version": "str"},
    "RecommendationOut": {"id": "uuid", "category": "str", "title": "str", "body": "str", "source": "str(rule|ml)", "evidence_source_ids": "list[uuid]"},
    "RecommendationFeedback": {"action": "str(helpful|not_helpful|dismissed|completed)"},
    "ChatSessionOut": {"id": "uuid", "created_at": "datetime", "title": "str|null"},
    "ChatMessageIn": {"text": "str", "language": "str|null"},
    "ChatReply": {"message_id": "uuid", "segments": "list[Segment]", "uncertainty_note": "str|null", "escalation": "bool"},
    "Segment": {"type": "str(supported_evidence|general_wellness|personal_observation|hypothetical|uncertain)", "text": "str", "source_ids": "list[uuid]", "record_ids": "list[uuid]"},
    "VoiceReply": {"transcript": "str", "language": "str", "reply": "ChatReply", "audio_url": "str|null"},
    "NotificationOut": {"id": "uuid", "type": "str", "title": "str", "body": "str", "created_at": "datetime", "read": "bool"},
    "NotificationPrefs": {"period_reminder": "bool", "reminder_time": "str(HH:MM)", "wellness_nudges": "bool", "deviation_alerts": "bool"},
    "DeviceToken": {"platform": "str(ios|android)", "token": "str"},
    "Dashboard": {"next_period": "CyclePrediction|null", "today_summary": "obj", "active_deviations": "int", "plan_progress": "obj", "latest_recommendations": "list[RecommendationOut]"},
    "ConversationTurnIn": {"draft_id": "uuid|null", "text": "str|null", "audio_base64": "str|null", "language_hint": "str(en|hi|kn|te)|null"},
    "ConversationTurnOut": {"draft_id": "uuid", "transcript": "str", "language": "str", "state": "str(needs_followup|ready_to_confirm|escalation)", "followup_question": "str|null", "extracted": "list[ExtractedSymptom]", "escalation_message": "str|null"},
    "ExtractedSymptom": {"symptom_code": "str", "severity": "int|null", "onset": "str|null", "duration": "str|null", "source_phrase": "str"},
    "DraftOut": {"id": "uuid", "status": "str(pending|confirmed|discarded)", "extracted": "list[ExtractedSymptom]", "comparison_with_history": "str|null"},
    "DraftEdit": {"extracted": "list[ExtractedSymptom]"},
    "DraftConfirmOut": {"saved_symptom_ids": "list[uuid]", "guidance": "list[Segment]"},
    "TwinOut": {"status": "str(ready|insufficient_data)", "n_days": "int", "min_days_required": "int", "baselines": "list[obj]", "model_version": "str|null"},
    "SimulateIn": {"changes": "list[{variable:str(sleep_hours|activity_minutes|stress_level|water_ml|routine_consistency),delta:float}]", "horizon_days": "int"},
    "SimulateOut": {"scenario_id": "uuid", "is_hypothetical": "bool(always true)", "baseline_series": "list[obj]", "scenario_series": "list[obj]", "uncertainty_band": "obj", "assumptions": "list[str]", "factors_considered": "list[str]", "disclaimer": "str"},
    "PatternOut": {"id": "uuid", "type": "str", "description": "str", "support": "int", "confidence": "float", "p_adjusted": "float|null", "created_at": "datetime"},
    "PatternEvidence": {"pattern_id": "uuid", "records": "list[{table:str,id:uuid,date:date,summary:str}]"},
    "Heatmap": {"metric": "str", "axis_x": "list[str]", "axis_y": "list[str]", "values": "list[list[float]]"},
    "DeviationOut": {"id": "uuid", "metrics": "list[str]", "started_at": "date", "method": "str", "score": "float", "status": "str(open|dismissed|resolved)", "explanation": "str"},
    "DeviationDetail": {"id": "uuid", "explanation": "str", "baseline": "obj", "records": "list[obj]"},
    "TimeMachineOut": {"range": "str(1m|3m|6m|1y)", "series": "list[obj]", "cycle_summary": "obj", "symptom_frequency": "list[obj]", "recurring_observations": "list[PatternOut]"},
    "CompareOut": {"period_a": "obj", "period_b": "obj", "differences": "list[{metric:str,a:float,b:float,change:float}]"},
    "DayOut": {"date": "date", "records": "list[obj]", "imported": "list[obj]"},
    "SummaryOut": {"range": "str", "text": "str", "facts": "list[obj]", "generated_from_record_count": "int"},
    "WearableConnectIn": {"platform": "str(apple_health|health_connect)", "granted_metrics": "list[str]"},
    "WearableOut": {"id": "uuid", "platform": "str", "status": "str", "connected_at": "datetime", "granted_metrics": "list[str]"},
    "ImportBatchIn": {"integration_id": "uuid", "measurements": "list[{metric:str,value:float,unit:str,start:datetime,end:datetime,source_app:str,source_device:str|null}]"},
    "ImportBatchOut": {"accepted": "int", "duplicates": "int", "rejected": "int"},
    "MeasurementOut": {"id": "uuid", "metric": "str", "value": "float", "unit": "str", "start": "datetime", "source_app": "str", "source_device": "str|null"},
    "UnifiedAnalytics": {"range": "str", "metrics": "list[{metric:str,points:list[obj],sources:list[str]}]", "relationships": "list[PatternOut]"},
    "ScheduleParseIn": {"text": "str", "date": "date"},
    "ScheduleParseOut": {"blocks": "list[{title:str,start:str,end:str}]", "needs_confirmation": "bool"},
    "PlanGenerateIn": {"date": "date", "blocks": "list[obj]", "available_minutes": "int|null"},
    "PlanOut": {"id": "uuid", "date": "date", "items": "list[PlanItemOut]", "rationale": "list[str]"},
    "PlanItemOut": {"id": "uuid", "start": "str", "end": "str", "category": "str", "title": "str", "status": "str(planned|done|skipped|rejected)"},
    "PlanItemPatch": {"status": "str|null", "start": "str|null", "end": "str|null"},
    "PlanAdaptIn": {"reason": "str(new_schedule|new_data|user_request)", "new_text": "str|null"},
    "PlanProgress": {"period_days": "int", "completed": "int", "skipped": "int", "completion_rate": "float"},
    "ReportPreviewIn": {"period_start": "date", "period_end": "date", "sections": "list[str]"},
    "ReportPreviewOut": {"report_id": "uuid", "sections": "list[obj]", "suggested_questions": "list[str]"},
    "ReportNotesIn": {"notes": "str", "questions": "list[str]"},
    "ReportOut": {"id": "uuid", "status": "str(draft|generating|ready|failed)", "period_start": "date", "period_end": "date", "download_url": "str|null"},
    "ShareIn": {"expires_in_days": "int(1-30)"},
    "ShareOut": {"id": "uuid", "url": "str", "expires_at": "datetime"},
    "SubgraphOut": {"nodes": "list[{id:uuid,type:str,label:str}]", "edges": "list[{id:uuid,source:uuid,target:uuid,relation:str,weight:float}]"},
    "EdgeExplanation": {"edge_id": "uuid", "explanation": "str", "evidence": "list[obj]"},
    "EvidenceSourceOut": {"id": "uuid", "organization": "str", "title": "str", "url": "str", "retrieved_at": "datetime", "license": "str|null"},
    "AISettings": {"personalization_enabled": "bool", "external_llm_allowed": "bool", "context_allowlist": "list[str]", "chat_retention_days": "int"},
    "AccessHistoryItem": {"timestamp": "datetime", "action": "str", "resource": "str|null", "outcome": "str(success|failure|blocked)", "ip": "str|null"},
    "ExportOut": {"job_id": "uuid", "status": "str(ready)", "download_url": "str|null (S3 delivery in ZIP 6)", "data": "obj (inline JSON export in this milestone)"},
    "DeleteAccountIn": {"password": "str", "confirm": "str('DELETE')"},
    "PreferenceIn": {"key": "str", "value": "str"},
    "PreferenceOut": {"key": "str", "value": "str", "source": "str(user_approved)", "approved_at": "datetime"},
    "ProposalOut": {"id": "uuid", "key": "str", "value": "str", "reason": "str", "status": "str"},
    "MemoryEnabledIn": {"enabled": "bool"},
    "Ok": {"ok": "bool"},
}

# (group, method, path, auth, summary, request_schema|None, response_schema|None)
E = []


def add(group, method, path, auth, summary, req=None, resp="Ok"):
    E.append((group, method, path, auth, summary, req, resp))


# Auth
add("Auth", "POST", "/auth/register", "none", "Create account and record initial consents", "RegisterRequest", "UserOut")
add("Auth", "POST", "/auth/login", "none", "Log in", "LoginRequest", "TokenPair")
add("Auth", "POST", "/auth/refresh", "none", "Rotate refresh token", "RefreshRequest", "TokenPair")
add("Auth", "POST", "/auth/logout", "JWT", "Revoke current session")
add("Auth", "POST", "/auth/forgot-password", "none", "Send reset email (always 202)", "ForgotPasswordRequest")
add("Auth", "POST", "/auth/reset-password", "none", "Reset password with token", "ResetPasswordRequest")
add("Auth", "GET", "/auth/me", "JWT", "Current user", None, "UserOut")
# Profile + consent
add("Profile", "GET", "/profile", "JWT", "Get health profile", None, "ProfileOut")
add("Profile", "PUT", "/profile", "JWT", "Update health profile", "ProfileIn", "ProfileOut")
add("Consent", "GET", "/consents", "JWT", "List consents", None, "list[ConsentOut]")
add("Consent", "PUT", "/consents/{purpose}", "JWT", "Grant or revoke a consent", "ConsentSet", "ConsentOut")
# Records
add("Cycles", "GET", "/cycles", "JWT+consent:health_tracking", "List cycles", None, "list[CycleOut]")
add("Cycles", "POST", "/cycles", "JWT+consent:health_tracking", "Log a cycle", "CycleIn", "CycleOut")
add("Cycles", "PUT", "/cycles/{id}", "JWT+consent:health_tracking", "Update a cycle", "CycleIn", "CycleOut")
add("Cycles", "DELETE", "/cycles/{id}", "JWT+consent:health_tracking", "Delete a cycle")
add("Cycles", "GET", "/cycles/stats", "JWT+consent:health_tracking", "Cycle statistics", None, "CycleStats")
add("Symptoms", "GET", "/symptoms", "JWT+consent:health_tracking", "List symptom logs", None, "list[SymptomOut]")
add("Symptoms", "POST", "/symptoms", "JWT+consent:health_tracking", "Log a symptom manually", "SymptomIn", "SymptomOut")
add("Symptoms", "DELETE", "/symptoms/{id}", "JWT+consent:health_tracking", "Delete symptom log")
add("Lifestyle", "GET", "/lifestyle", "JWT+consent:health_tracking", "List daily entries", None, "list[LifestyleOut]")
add("Lifestyle", "POST", "/lifestyle", "JWT+consent:health_tracking", "Create daily entry", "LifestyleIn", "LifestyleOut")
add("Lifestyle", "PUT", "/lifestyle/{id}", "JWT+consent:health_tracking", "Update daily entry", "LifestyleIn", "LifestyleOut")
add("Lifestyle", "GET", "/lifestyle/summary", "JWT+consent:health_tracking", "Summary over a period", None, "LifestyleSummary")
add("Mood", "GET", "/mood", "JWT+consent:health_tracking", "List mood entries", None, "list[MoodOut]")
add("Mood", "POST", "/mood", "JWT+consent:health_tracking", "Log mood", "MoodIn", "MoodOut")
# Predictions
add("Predictions", "GET", "/predictions/cycle/next", "JWT+consent:ml_processing", "Next period prediction with interval", None, "CyclePrediction")
add("Predictions", "GET", "/predictions/{id}/explanation", "JWT+consent:ml_processing", "Explanation of a prediction", None, "Explanation")
add("Insights", "GET", "/insights/risk", "JWT+consent:ml_processing", "Awareness-level pattern category (not a diagnosis)", None, "RiskInsight")
add("Recommendations", "GET", "/recommendations", "JWT", "List recommendations", None, "list[RecommendationOut]")
add("Recommendations", "POST", "/recommendations/{id}/feedback", "JWT", "Record feedback", "RecommendationFeedback")
# Chat / voice
add("Chat", "POST", "/chat/sessions", "JWT", "Start chat session", None, "ChatSessionOut")
add("Chat", "GET", "/chat/sessions", "JWT", "List sessions", None, "list[ChatSessionOut]")
add("Chat", "POST", "/chat/sessions/{id}/messages", "JWT", "Send a message; evidence-tagged reply", "ChatMessageIn", "ChatReply")
add("Chat", "DELETE", "/chat/sessions/{id}", "JWT", "Delete session and messages")
add("Voice", "POST", "/voice/query", "JWT", "Audio upload -> transcript + reply (+audio)", "ConversationTurnIn", "VoiceReply")
# Notifications
add("Notifications", "GET", "/notifications", "JWT", "List notifications", None, "list[NotificationOut]")
add("Notifications", "PUT", "/notifications/preferences", "JWT", "Update preferences", "NotificationPrefs", "NotificationPrefs")
add("Notifications", "POST", "/notifications/device-token", "JWT", "Register push token", "DeviceToken")
# Dashboard
add("Dashboard", "GET", "/dashboard", "JWT", "Home overview", None, "Dashboard")
# Detective
add("Detective", "POST", "/conversation/turn", "JWT+consent:health_tracking", "One conversational turn (text or audio)", "ConversationTurnIn", "ConversationTurnOut")
add("Detective", "GET", "/conversation/drafts/{id}", "JWT", "Get draft", None, "DraftOut")
add("Detective", "PUT", "/conversation/drafts/{id}", "JWT", "Edit draft before confirming", "DraftEdit", "DraftOut")
add("Detective", "POST", "/conversation/drafts/{id}/confirm", "JWT+consent:health_tracking", "Confirm and save (only way to persist)", None, "DraftConfirmOut")
add("Detective", "POST", "/conversation/drafts/{id}/discard", "JWT", "Discard draft")
# Twin
add("Twin", "GET", "/twin", "JWT+consent:ml_processing", "Digital twin status and baselines", None, "TwinOut")
add("Twin", "POST", "/twin/simulate", "JWT+consent:ml_processing", "Run a hypothetical what-if", "SimulateIn", "SimulateOut")
add("Twin", "GET", "/twin/simulations", "JWT", "Past scenarios", None, "list[SimulateOut]")
# Patterns
add("Patterns", "GET", "/patterns", "JWT+consent:ml_processing", "List detected patterns", None, "list[PatternOut]")
add("Patterns", "GET", "/patterns/{id}/evidence", "JWT", "Underlying records of a pattern", None, "PatternEvidence")
add("Patterns", "GET", "/patterns/heatmap", "JWT", "Heatmap for a metric", None, "Heatmap")
# Deviations
add("Deviations", "GET", "/deviations", "JWT+consent:ml_processing", "List deviations from personal baseline", None, "list[DeviationOut]")
add("Deviations", "GET", "/deviations/{id}", "JWT", "Deviation detail with records", None, "DeviationDetail")
add("Deviations", "POST", "/deviations/{id}/dismiss", "JWT", "Dismiss")
# Time Machine
add("TimeMachine", "GET", "/timemachine", "JWT", "Timeline for 1m/3m/6m/1y", None, "TimeMachineOut")
add("TimeMachine", "GET", "/timemachine/compare", "JWT", "Compare two periods", None, "CompareOut")
add("TimeMachine", "GET", "/timemachine/day/{date}", "JWT", "All records for a date", None, "DayOut")
add("TimeMachine", "GET", "/timemachine/summary", "JWT", "Summary generated from records", None, "SummaryOut")
# Wearables
add("Wearables", "POST", "/wearables/connect", "JWT", "Register an integration", "WearableConnectIn", "WearableOut")
add("Wearables", "DELETE", "/wearables/{id}", "JWT", "Disconnect (optional purge)")
add("Wearables", "POST", "/wearables/import", "JWT", "Batch import of normalized measurements", "ImportBatchIn", "ImportBatchOut")
add("Wearables", "GET", "/wearables/measurements", "JWT", "List imported measurements with source", None, "list[MeasurementOut]")
add("Wearables", "GET", "/analytics/unified", "JWT", "Unified manual + imported analytics", None, "UnifiedAnalytics")
# Planner
add("Planner", "POST", "/planner/schedule/parse", "JWT", "Parse natural-language schedule", "ScheduleParseIn", "ScheduleParseOut")
add("Planner", "POST", "/planner/plans/generate", "JWT", "Generate a daily plan", "PlanGenerateIn", "PlanOut")
add("Planner", "PATCH", "/planner/items/{id}", "JWT", "Mark done / skip / reject / edit", "PlanItemPatch", "PlanItemOut")
add("Planner", "POST", "/planner/plans/{id}/adapt", "JWT", "Re-plan after change", "PlanAdaptIn", "PlanOut")
add("Planner", "GET", "/planner/progress", "JWT", "Progress tracking", None, "PlanProgress")
# Reports
add("Reports", "POST", "/reports/preview", "JWT", "Preview a report", "ReportPreviewIn", "ReportPreviewOut")
add("Reports", "PUT", "/reports/{id}/notes", "JWT", "Edit notes/questions", "ReportNotesIn", "ReportPreviewOut")
add("Reports", "POST", "/reports/{id}/generate", "JWT", "Generate PDF (async)", None, "ReportOut")
add("Reports", "GET", "/reports/{id}", "JWT", "Report status", None, "ReportOut")
add("Reports", "GET", "/reports/{id}/download", "JWT", "Download PDF", None, None)
add("Reports", "POST", "/reports/{id}/share", "JWT", "Create expiring share link", "ShareIn", "ShareOut")
add("Reports", "DELETE", "/reports/shares/{id}", "JWT", "Revoke share link")
# Graph / evidence
add("Graph", "GET", "/graph/subgraph", "JWT+consent:ml_processing", "User-scoped subgraph", None, "SubgraphOut")
add("Graph", "GET", "/graph/edges/{id}/explanation", "JWT", "Why this connection exists", None, "EdgeExplanation")
add("Evidence", "GET", "/evidence/sources/{id}", "JWT", "Source details for a citation", None, "EvidenceSourceOut")
# Vault / privacy
add("Vault", "GET", "/privacy/ai-settings", "JWT", "Read AI privacy settings", None, "AISettings")
add("Vault", "PUT", "/privacy/ai-settings", "JWT", "Update AI privacy settings", "AISettings", "AISettings")
add("Vault", "GET", "/privacy/access-history", "JWT", "Access and audit history", None, "list[AccessHistoryItem]")
add("Vault", "POST", "/privacy/export", "JWT", "Export all of the user's data (inline JSON in this milestone)", None, "ExportOut")
add("Vault", "DELETE", "/privacy/account", "JWT", "Erase account and data", "DeleteAccountIn")
# Memory
add("Memory", "GET", "/memory/preferences", "JWT", "List approved preferences", None, "list[PreferenceOut]")
add("Memory", "PUT", "/memory/preferences", "JWT", "Add/update a preference", "PreferenceIn", "PreferenceOut")
add("Memory", "DELETE", "/memory/preferences/{key}", "JWT", "Delete a preference")
add("Memory", "GET", "/memory/proposals", "JWT", "Pending proposals", None, "list[ProposalOut]")
add("Memory", "POST", "/memory/proposals/{id}/approve", "JWT", "Approve proposal", None, "PreferenceOut")
add("Memory", "POST", "/memory/proposals/{id}/reject", "JWT", "Reject proposal")
add("Memory", "PUT", "/memory/enabled", "JWT", "Turn personalization on/off", "MemoryEnabledIn")

# Internal ML engine contracts (not mobile-facing)
ML = [
    ("POST", "/v1/cycle/predict", "cycle lengths + optional features -> prediction, interval, SHAP"),
    ("POST", "/v1/risk/assess", "aggregated features -> awareness category + factors"),
    ("POST", "/v1/recommend", "profile + trends -> ranked candidates"),
    ("POST", "/v1/twin/fit", "daily feature table -> twin profile (or insufficient_data)"),
    ("POST", "/v1/twin/simulate", "twin profile + changes -> baseline vs scenario series"),
    ("POST", "/v1/patterns/analyze", "windowed history -> patterns with evidence ids"),
    ("POST", "/v1/deviation/detect", "history + baselines -> deviation events"),
    ("POST", "/v1/nlp/extract", "transcript + language -> ontology-constrained symptoms"),
    ("POST", "/v1/schedule/parse", "free text -> time blocks"),
    ("POST", "/v1/chat/respond", "question + allowlisted context -> tagged segments + citations"),
    ("POST", "/v1/speech/transcribe", "audio -> text + language"),
    ("POST", "/v1/speech/synthesize", "text + language -> audio (where voice available)"),
    ("GET", "/health", "liveness (implemented in ZIP 1)"),
    ("GET", "/models", "registered model versions"),
    ("GET", "/metrics", "Prometheus metrics"),
]

EXAMPLES = [
    ("Login", "POST /auth/login",
     '{"email": "asha@example.com", "password": "correct-horse-battery", "device": "pixel-8"}',
     '{"access_token": "<jwt>", "refresh_token": "<opaque>", "expires_in": 900}'),
    ("Log a cycle", "POST /cycles",
     '{"start_date": "2026-10-03", "end_date": "2026-10-07", "flow_intensity": 3}',
     '{"id": "7f1c...", "start_date": "2026-10-03", "end_date": "2026-10-07", "cycle_length_days": 29, "flow_intensity": 3, "notes": null}'),
    ("Symptom Detective turn", "POST /conversation/turn",
     '{"text": "I feel very tired today and have a headache", "language_hint": "en"}',
     '{"draft_id": "a3d2...", "transcript": "I feel very tired today and have a headache", "language": "en", "state": "needs_followup", "followup_question": "How strong is the headache, from 1 (mild) to 5 (severe)?", "extracted": [{"symptom_code": "fatigue", "severity": null, "onset": "today", "duration": null, "source_phrase": "very tired"}, {"symptom_code": "headache", "severity": null, "onset": "today", "duration": null, "source_phrase": "headache"}], "escalation_message": null}'),
    ("Confirm a draft", "POST /conversation/drafts/{id}/confirm",
     "(no body)",
     '{"saved_symptom_ids": ["c1...", "c2..."], "guidance": [{"type": "general_wellness", "text": "...", "source_ids": [], "record_ids": []}]}'),
    ("Twin what-if", "POST /twin/simulate",
     '{"changes": [{"variable": "sleep_hours", "delta": 1.0}], "horizon_days": 14}',
     '{"scenario_id": "5b...", "is_hypothetical": true, "assumptions": ["Relationships estimated from your own 62 days of records", "Changes stay within your observed range"], "factors_considered": ["sleep_hours", "stress_level"], "disclaimer": "Hypothetical scenario based on associations in your own data. Not a prediction and not a biological simulation.", "...": "series omitted"}'),
    ("Error envelope (all endpoints)", "any failing request",
     "-",
     '{"error": {"code": "consent_required", "message": "Consent for ml_processing is required.", "request_id": "9d3e..."}}'),
]

ERROR_CODES = [
    ("400", "validation_error / invalid_reset_token", "Request body or query failed validation, or a password-reset token is invalid/expired/used"),
    ("401", "unauthenticated", "Missing, invalid, expired or revoked token"),
    ("403", "forbidden / consent_required", "Role or ownership check failed, or required consent not granted"),
    ("404", "not_found", "Resource does not exist for this user"),
    ("409", "conflict", "Duplicate or overlapping record"),
    ("422", "insufficient_data", "Not enough records for the requested analysis (twin, patterns)"),
    ("429", "rate_limited", "Too many requests"),
    ("502", "ml_unavailable", "ML engine unreachable (feature degrades gracefully where possible)"),
]
