# Diagram 11: Adaptive Wellness Planner Workflow

> **Implementation status:** Not started (ZIP 6).

## Diagram source (Mermaid)

```mermaid
flowchart TB
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
    ADAPT --> SLOT
```

## Components

- **Schedule parser**: LLM only converts free text to time blocks; output is shown for confirmation.
- **Rule library**: Curated, referenced suggestions (movement, hydration, wind-down, meals). No cycle-phase restrictions.
- **Slot filler**: Deterministic algorithm placing activities in free time within duration/buffer constraints.
- **Feedback + preference learning**: Accept/skip/reject updates per-activity weights.
- **Adaptation**: Re-plans the rest of the day when data or schedule changes.

## Data flow

Parse -> confirm -> generate candidates from recent data and preferences -> place into free slots -> user acts on items -> feedback updates weights -> next plan reflects them.

## Technologies and why they were selected

- **Deterministic scheduler (Python)**: Testable and predictable; LLM is not trusted with timing.
- **Simple weighted preference model**: Works with tiny feedback volumes.

## Communication with other modules

Core planner module; ML engine for parsing and optional ranking; reads memory preferences.

## Security considerations

Schedule text is personal data: egress gate applies; stored encrypted.

## Real-world execution example

'College 9-4, dance 6pm' -> free windows 4-6pm and after 7:30pm; plan places a 20-min walk at 4:15pm, hydration reminders, and a wind-down at 10pm.
