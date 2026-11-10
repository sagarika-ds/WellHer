"""Generate docs from the single-source spec files.

Run from repo root:  python tools/gen_docs/generate.py
Outputs: docs/architecture/diagrams/*.md|*.mmd, docs/architecture/README.md,
         docs/api/endpoints.md, docs/api/openapi.yaml, docs/api/examples.md, docs/db/schema.md
"""
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from api_spec import ERROR_CODES, EXAMPLES, ML, SCHEMAS, E
from db_spec import GROUPS, IMPLEMENTED, NORMALIZATION_NOTES
from diagrams_a import DIAGRAMS_A
from diagrams_b import DIAGRAMS_B

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = DIAGRAMS_A + DIAGRAMS_B
STATUS_NOTE = ("> **Status:** see the per-diagram implementation status below and `docs/status/STATUS.md`. "
               "Diagrams describe the planned system; only what is marked *Implemented* is built.")
IMPL = {
    1: "Partial: mobile app (tracking + privacy), backend, PostgreSQL, Redis, ARQ worker implemented. ML engine logic, Qdrant, S3, MLflow not yet.",
    2: "Implemented (ZIP 3): navigation, auth/session lifecycle, TanStack Query, forms, calendar, bar chart, theme. Native health/audio/notification bridges not yet.",
    3: "Implemented for the ZIP 2 scope (middleware, routers, dependencies, services, repositories, events, worker). `integrations/` (ml_client, storage, push) pending.",
    4: "Skeleton only (`/health`). Models arrive in ZIP 4.",
    5: "Not started (ZIP 4).", 6: "Not started (ZIP 4).", 7: "Not started (ZIP 5). Only the `symptom_logs.source` column and ontology codes exist.",
    8: "Not started (ZIP 4).", 9: "Partial: `timeline_events` read model is written on every record change; aggregation/comparison/summaries not yet.",
    10: "Not started (ZIP 5).", 11: "Not started (ZIP 6).", 12: "Not started (ZIP 6).", 13: "Not started (ZIP 5).",
    14: "Not started (ZIP 5).",
    15: "Partial: Argon2, JWT + rotating refresh with reuse detection, denylist, RBAC, ownership, consent gating, AES-GCM field encryption, append-only audit, egress gate, export and erasure are implemented and tested. Mobile token storage (keychain) added in ZIP 3. KMS envelope keys, TLS termination, S3/Qdrant purge pending.",
    16: "Not started (ZIP 5).",
    17: "13 of 41 tables migrated (Alembic 0001). The diagram shows the full design.",
    18: "Implemented and tested end to end (backend + the mobile client against a live backend); matches the code.",
    19: "Partial: steps 5-6 (single transactional write + `record.confirmed` event with pipeline tracking) are implemented; other steps are not.",
    20: "Configuration written (Compose, nginx, Prometheus, CI); not executed in the authoring sandbox.",
}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def diagram_docs() -> None:
    out = ROOT / "docs/architecture/diagrams"
    for d in DIAGRAMS:
        write(out / f"{d['slug']}.mmd", d["mermaid"])
        md = [f"# Diagram {d['n']}: {d['title']}", "", f"> **Implementation status:** {IMPL[d['n']]}", "",
              "## Diagram source (Mermaid)", "", "```mermaid", d["mermaid"], "```", "",
              "## Components", ""]
        md += [f"- **{n}**: {t}" for n, t in d["components"]]
        md += ["", "## Data flow", "", d["flow"], "", "## Technologies and why they were selected", ""]
        md += [f"- **{n}**: {t}" for n, t in d["tech"]]
        md += ["", "## Communication with other modules", "", d["comms"], "",
               "## Security considerations", "", d["security"], "",
               "## Real-world execution example", "", d["example"]]
        write(out / f"{d['slug']}.md", "\n".join(md))
    idx = ["# Architecture diagrams", "", STATUS_NOTE, "",
           "Each diagram has an editable `.mmd` source and a `.md` document with components, data flow, "
           "technologies, communication, security and a worked example. Render `.md` files on GitHub/VS Code "
           "(Mermaid preview) or paste `.mmd` into https://mermaid.live.", "",
           "| # | Diagram | Implementation status | Doc | Source |", "|---|---|---|---|---|"]
    idx += [f"| {d['n']} | {d['title']} | {IMPL[d['n']]} | [{d['slug']}.md](diagrams/{d['slug']}.md) | [.mmd](diagrams/{d['slug']}.mmd) |"
            for d in DIAGRAMS]
    write(ROOT / "docs/architecture/README.md", "\n".join(idx))


def type_to_schema(t: str) -> dict:
    t = t.strip()
    nullable = False
    if t.endswith("|null"):
        t, nullable = t[:-5], True
    m = re.match(r"list\[(.+)\]$", t)
    if m:
        inner = m.group(1)
        items = {"$ref": f"#/components/schemas/{inner}"} if inner in SCHEMAS else {"type": "object"} if inner.startswith("{") else {"type": "string"}
        s = {"type": "array", "items": items}
    elif t in SCHEMAS:
        s = {"$ref": f"#/components/schemas/{t}"}
    else:
        base = t.split("(")[0].split("{")[0]
        mp = {"str": {"type": "string"}, "int": {"type": "integer"}, "float": {"type": "number"},
              "bool": {"type": "boolean"}, "date": {"type": "string", "format": "date"},
              "datetime": {"type": "string", "format": "date-time"}, "uuid": {"type": "string", "format": "uuid"},
              "obj": {"type": "object"}}
        s = dict(mp.get(base, {"type": "string"}))
        if "(" in t and base in ("str", "int", "float", "bool"):
            s["description"] = t[t.index("("):]
    if nullable and "$ref" not in s:
        s["nullable"] = True
    return s


def api_docs() -> None:
    # sanity: every referenced schema exists
    for g, m, p, a, s, req, resp in E:
        for name in (req, resp):
            if name:
                base = re.match(r"list\[(.+)\]$", name)
                base = base.group(1) if base else name
                assert base in SCHEMAS, f"unknown schema {base} used by {m} {p}"
    md = ["# API contracts (design stage)", "",
          "Base path `/api/v1`. All bodies are JSON. Errors use the envelope in the last section. "
          "These are **contracts, not implementations**; status per endpoint is in `docs/status/STATUS.md`.", "",
          "Auth legend: `none` public; `JWT` valid access token and ownership; `JWT+consent:<purpose>` additionally "
          "requires that consent purpose to be granted (otherwise 403 `consent_required`).", ""]
    groups: dict[str, list] = {}
    for row in E:
        groups.setdefault(row[0], []).append(row)
    for g, rows in groups.items():
        md += [f"## {g}", "", "| Method | Path | Auth | Request schema | Response schema | Summary |", "|---|---|---|---|---|---|"]
        md += [f"| {m} | `{p}` | {a} | {req or '-'} | {resp or 'file'} | {s} |" for _, m, p, a, s, req, resp in rows]
        md.append("")
    md += ["## Internal ML engine contracts (service-token auth, private network only)", "",
           "| Method | Path | Purpose |", "|---|---|---|"] + [f"| {m} | `{p}` | {s} |" for m, p, s in ML] + [""]
    md += ["## Error envelope and codes", "", "```json", '{"error": {"code": "string", "message": "string", "request_id": "string"}}', "```", "",
           "| HTTP | code | Meaning |", "|---|---|---|"] + [f"| {h} | {c} | {t} |" for h, c, t in ERROR_CODES] + [""]
    md += ["## Schemas", ""]
    for name, fields in SCHEMAS.items():
        md += [f"### {name}", "", "| Field | Type |", "|---|---|"] + [f"| {k} | `{v}` |" for k, v in fields.items()] + [""]
    write(ROOT / "docs/api/endpoints.md", "\n".join(md))

    ex = ["# API examples", "", "Illustrative payloads for the contract. Values are placeholders.", ""]
    for title, call, req, resp in EXAMPLES:
        ex += [f"## {title}", "", f"`{call}`", "", "Request:", "```json", req, "```", "Response:", "```json", resp, "```", ""]
    write(ROOT / "docs/api/examples.md", "\n".join(ex))

    comps = {n: {"type": "object", "properties": {k: type_to_schema(v) for k, v in f.items()}} for n, f in SCHEMAS.items()}
    paths: dict = {}
    err_ref = {"description": "Error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}}
    for g, m, p, a, s, req, resp in E:
        op = {"tags": [g], "summary": s, "operationId": f"{m.lower()}_{re.sub(r'[^a-z0-9]+', '_', p.lower()).strip('_')}",
              "responses": {"default": err_ref}}
        if a == "none":
            op["security"] = []
        else:
            op["security"] = [{"bearerAuth": []}]
            if "consent:" in a:
                op["description"] = f"Requires consent purpose `{a.split('consent:')[1]}`."
        if req:
            op["requestBody"] = {"required": True, "content": {"application/json": {"schema": type_to_schema(req)}}}
        if resp is None:
            op["responses"]["200"] = {"description": "PDF file", "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}}
        else:
            op["responses"]["200"] = {"description": "OK", "content": {"application/json": {"schema": type_to_schema(resp)}}}
        params = re.findall(r"\{(\w+)\}", p)
        if params:
            op["parameters"] = [{"name": n, "in": "path", "required": True, "schema": {"type": "string"}} for n in params]
        paths.setdefault(p, {})[m.lower()] = op
    spec = {"openapi": "3.0.3",
            "info": {"title": "Women's Wellness Core API", "version": "0.1.0-design",
                     "description": "Design-stage contract generated from tools/gen_docs/api_spec.py. Not yet implemented."},
            "servers": [{"url": "/api/v1"}], "paths": paths,
            "components": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}}, "schemas": comps}}
    write(ROOT / "docs/api/openapi.yaml", yaml.safe_dump(spec, sort_keys=False, width=100))


def db_docs() -> None:
    md = ["# Database schema (design stage)", "",
          "PostgreSQL 16 via SQLAlchemy 2.0 + Alembic. **Conventions** (apply to every table unless noted): UUID `id` primary key; "
          "`created_at`/`updated_at` timestamptz; user-owned tables carry `user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE` "
          "with an index on `(user_id, <time column> DESC)`; `(enc)` marks application-level AES-GCM encrypted columns.", "",
          "See [diagram 17](../architecture/diagrams/17-complete-database-er-diagram.md) for relationships.", ""]
    total = 0
    for g, tables in GROUPS:
        md += [f"## {g}", "", "| Table | State | Purpose | Columns / constraints |", "|---|---|---|---|"]
        for n, p, c in tables:
            md.append(f"| `{n}` | {'**migrated (0001)**' if n in IMPLEMENTED else 'design'} | {p} | {c} |")
            total += 1
        md.append("")
    md += ["## Design notes", ""] + [f"- {n}" for n in NORMALIZATION_NOTES] + ["", f"Total tables in design: **{total}**; migrated so far: **{len(IMPLEMENTED)}**."]
    write(ROOT / "docs/db/schema.md", "\n".join(md))
    print("tables:", total)


if __name__ == "__main__":
    diagram_docs()
    api_docs()
    db_docs()
    print("diagrams:", len(DIAGRAMS), "endpoints:", len(E), "schemas:", len(SCHEMAS), "ml endpoints:", len(ML))
