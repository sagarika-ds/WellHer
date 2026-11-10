#!/usr/bin/env bash
# Usage: scripts/make_zip.sh <name>   -> dist-zips/<name>.zip (verified)
set -euo pipefail
NAME="${1:?usage: make_zip.sh <name>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
mkdir -p dist-zips; OUT="dist-zips/$NAME.zip"; rm -f "$OUT"
# 1. build, excluding junk and secrets
zip -rq "$OUT" . -x '.git/*' 'node_modules/*' '*/node_modules/*' '.venv/*' 'venv/*' '__pycache__/*' '*/__pycache__/*' \
  '*.pyc' '.pytest_cache/*' '*/.pytest_cache/*' '.ruff_cache/*' '*/.ruff_cache/*' '.mypy_cache/*' '.expo/*' '*/.expo/*' 'dist/*' '*/dist-bundle/*' 'dist-bundle/*' '*/coverage/*' 'coverage/*' \
  'build/*' 'mlruns/*' 'dist-zips/*' '.env' '.env.*' '*.pem' '*.key' '*.jks' '*.p12' '*.log' '.coverage' '*/.coverage' '.coverage.*' '*/.coverage.*' 'htmlcov/*' '*/htmlcov/*' '*.egg-info/*' '*/*.egg-info/*'
zip -q "$OUT" .env.example
# 2. integrity
unzip -tq "$OUT" >/dev/null && echo "integrity: OK"
# 3. forbidden content
if unzip -Z1 "$OUT" | grep -E '(^|/)(\.env|\.coverage.*|.*\.pem|.*\.key|node_modules|\.venv|__pycache__|\.pytest_cache|\.ruff_cache|dist-bundle|coverage|\.expo)(/|$)' | grep -v '\.env\.example'; then
  echo "FORBIDDEN FILES FOUND"; exit 1; fi
# 4. secret scan on extracted copy
TMP="$(mktemp -d)"; unzip -q "$OUT" -d "$TMP"
if grep -rIE '(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,})' "$TMP"; then
  echo "POSSIBLE SECRET FOUND"; rm -rf "$TMP"; exit 1; fi
echo "secret scan: clean"
echo "files: $(unzip -Z1 "$OUT" | grep -vc '/$')  size: $(du -h "$OUT" | cut -f1)"
rm -rf "$TMP"
