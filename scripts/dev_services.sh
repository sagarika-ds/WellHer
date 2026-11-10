#!/usr/bin/env bash
# Start local PostgreSQL 16 + Redis WITHOUT Docker (Ubuntu/Debian, run as root or with sudo).
# Used for local development and by the test suite in environments that have no Docker daemon.
set -euo pipefail
pg_lsclusters | grep -q online || pg_ctlcluster 16 main start
for i in $(seq 1 20); do pg_isready -q && break; sleep 0.5; done
redis-cli ping >/dev/null 2>&1 || redis-server --daemonize yes --port 6379 >/dev/null
for i in $(seq 1 20); do redis-cli ping >/dev/null 2>&1 && break; sleep 0.3; done
role_exists=$(su postgres -c "psql -tAc \"select 1 from pg_roles where rolname='wellness'\"" || true)
[ "$role_exists" = "1" ] || su postgres -c "psql -c \"create role wellness login password 'testpw' createdb\"" >/dev/null
for db in wellness_test wellness_gen; do
  [ "$(su postgres -c "psql -tAc \"select 1 from pg_database where datname='$db'\"")" = "1" ] || \
    su postgres -c "psql -c 'create database $db owner wellness'" >/dev/null
  su postgres -c "psql -d $db -c 'create extension if not exists citext; create extension if not exists pgcrypto;'" >/dev/null 2>&1
done
echo "services up: postgres $(pg_isready | cut -d- -f2-) / redis $(redis-cli ping)"
