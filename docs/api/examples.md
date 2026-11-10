# API examples

Illustrative payloads for the contract. Values are placeholders.

## Login

`POST /auth/login`

Request:
```json
{"email": "asha@example.com", "password": "correct-horse-battery", "device": "pixel-8"}
```
Response:
```json
{"access_token": "<jwt>", "refresh_token": "<opaque>", "expires_in": 900}
```

## Log a cycle

`POST /cycles`

Request:
```json
{"start_date": "2026-10-03", "end_date": "2026-10-07", "flow_intensity": 3}
```
Response:
```json
{"id": "7f1c...", "start_date": "2026-10-03", "end_date": "2026-10-07", "cycle_length_days": 29, "flow_intensity": 3, "notes": null}
```

## Symptom Detective turn

`POST /conversation/turn`

Request:
```json
{"text": "I feel very tired today and have a headache", "language_hint": "en"}
```
Response:
```json
{"draft_id": "a3d2...", "transcript": "I feel very tired today and have a headache", "language": "en", "state": "needs_followup", "followup_question": "How strong is the headache, from 1 (mild) to 5 (severe)?", "extracted": [{"symptom_code": "fatigue", "severity": null, "onset": "today", "duration": null, "source_phrase": "very tired"}, {"symptom_code": "headache", "severity": null, "onset": "today", "duration": null, "source_phrase": "headache"}], "escalation_message": null}
```

## Confirm a draft

`POST /conversation/drafts/{id}/confirm`

Request:
```json
(no body)
```
Response:
```json
{"saved_symptom_ids": ["c1...", "c2..."], "guidance": [{"type": "general_wellness", "text": "...", "source_ids": [], "record_ids": []}]}
```

## Twin what-if

`POST /twin/simulate`

Request:
```json
{"changes": [{"variable": "sleep_hours", "delta": 1.0}], "horizon_days": 14}
```
Response:
```json
{"scenario_id": "5b...", "is_hypothetical": true, "assumptions": ["Relationships estimated from your own 62 days of records", "Changes stay within your observed range"], "factors_considered": ["sleep_hours", "stress_level"], "disclaimer": "Hypothetical scenario based on associations in your own data. Not a prediction and not a biological simulation.", "...": "series omitted"}
```

## Error envelope (all endpoints)

`any failing request`

Request:
```json
-
```
Response:
```json
{"error": {"code": "consent_required", "message": "Consent for ml_processing is required.", "request_id": "9d3e..."}}
```
