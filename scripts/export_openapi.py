"""Write the REAL OpenAPI document of the running backend code to docs/api/openapi.implemented.json.
Usage (from repo root, with the backend env vars set):  python scripts/export_openapi.py"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://unused")
os.environ.setdefault("JWT_SECRET", "export-only-" + "x" * 40)
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=")

from app.main import app  # noqa: E402

out = ROOT / "docs/api/openapi.implemented.json"
spec = app.openapi()
out.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
n = sum(len(v) for v in spec["paths"].values())
print(f"wrote {out.relative_to(ROOT)}: {len(spec['paths'])} paths, {n} operations")
