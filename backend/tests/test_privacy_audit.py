import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.helpers import PASSWORD, signup

API = "/api/v1"
USER_TABLES = ["health_profiles", "refresh_tokens", "user_consents", "ai_settings", "cycle_records",
               "symptom_logs", "lifestyle_records", "mood_records", "timeline_events", "pipeline_runs"]


async def _seed(client, acc):
    await client.post(f"{API}/cycles", headers=acc.h, json={"start_date": "2026-01-01", "notes": "n-" + acc.email})
    await client.post(f"{API}/symptoms", headers=acc.h, json={
        "logged_at": "2026-01-02T08:00:00+00:00", "symptom_code": "headache", "severity": 2})
    await client.post(f"{API}/lifestyle", headers=acc.h, json={"date": "2026-01-02", "sleep_hours": 7})
    await client.post(f"{API}/mood", headers=acc.h, json={"logged_at": "2026-01-02T20:00:00+00:00", "mood_score": 3})


async def test_ai_settings_defaults_and_update(client):
    acc = await signup(client)
    d = (await client.get(f"{API}/privacy/ai-settings", headers=acc.h)).json()
    assert d == {"personalization_enabled": True, "external_llm_allowed": False,
                 "context_allowlist": [], "chat_retention_days": 30}
    body = {"personalization_enabled": False, "external_llm_allowed": False,
            "context_allowlist": ["patterns", "cycle_summary", "patterns"], "chat_retention_days": 7}
    r = await client.put(f"{API}/privacy/ai-settings", headers=acc.h, json=body)
    assert r.status_code == 200 and r.json()["context_allowlist"] == ["cycle_summary", "patterns"]
    assert (await client.put(f"{API}/privacy/ai-settings", headers=acc.h,
                             json={**body, "context_allowlist": ["home_address"]})).status_code == 400
    assert (await client.put(f"{API}/privacy/ai-settings", headers=acc.h,
                             json={**body, "chat_retention_days": 9999})).status_code == 400


async def test_cannot_enable_external_llm_without_consent(client):
    acc = await signup(client, consents=[{"purpose": "health_tracking", "granted": True}])
    body = {"personalization_enabled": True, "external_llm_allowed": True, "context_allowlist": [], "chat_retention_days": 30}
    r = await client.put(f"{API}/privacy/ai-settings", headers=acc.h, json=body)
    assert r.status_code == 403 and r.json()["error"]["code"] == "consent_required"
    await client.put(f"{API}/consents/llm_external", headers=acc.h, json={"granted": True})
    assert (await client.put(f"{API}/privacy/ai-settings", headers=acc.h, json=body)).status_code == 200


async def test_access_history_is_own_and_ordered(client):
    a, b = await signup(client), await signup(client)
    await client.get(f"{API}/cycles", headers=a.h)
    await client.get(f"{API}/cycles", headers=b.h)
    ha = (await client.get(f"{API}/privacy/access-history", headers=a.h)).json()
    actions = [(x["action"], x["resource"]) for x in ha]
    assert ("read", "cycle_records") in actions and ("login", "session") in actions
    assert ha[0]["timestamp"] >= ha[-1]["timestamp"]
    hb = (await client.get(f"{API}/privacy/access-history", headers=b.h)).json()
    assert len([x for x in hb if x["action"] == "read"]) == 1  # B sees only B's single read
    assert len([x for x in ha if x["action"] == "read"]) == 1


async def test_audit_never_stores_health_values(client, sessionmaker_):
    acc = await signup(client)
    await client.post(f"{API}/cycles", headers=acc.h, json={"start_date": "2026-01-01", "notes": "SENSITIVE-NOTE"})
    await client.get(f"{API}/cycles", headers=acc.h)
    async with sessionmaker_() as s:
        dump = (await s.execute(text("select string_agg(row_to_json(a)::text, ' ') from audit_logs a"))).scalar_one()
    assert "SENSITIVE-NOTE" not in dump and PASSWORD not in dump


async def test_failed_login_is_audited(client, sessionmaker_):
    await signup(client, "aud@example.com")
    await client.post(f"{API}/auth/login", json={"email": "aud@example.com", "password": "wrong-wrong-12"})
    async with sessionmaker_() as s:
        n = (await s.execute(text("select count(*) from audit_logs where action='login' and outcome='failure'"))).scalar_one()
    assert n == 1


async def test_audit_log_is_append_only(client, sessionmaker_):
    await signup(client)
    async with sessionmaker_() as s:
        with pytest.raises(DBAPIError, match="append-only"):
            await s.execute(text("update audit_logs set action='tampered'"))
        await s.rollback()
        with pytest.raises(DBAPIError, match="append-only"):
            await s.execute(text("delete from audit_logs"))
        await s.rollback()
        with pytest.raises(DBAPIError, match="append-only"):
            await s.execute(text("update audit_logs set user_id = gen_random_uuid()"))
        await s.rollback()
        # the one permitted mutation: anonymisation by nulling user_id
        await s.execute(text("update audit_logs set user_id = null"))
        await s.commit()


async def test_export_contains_only_own_data(client):
    a, b = await signup(client, "a@example.com"), await signup(client, "b@example.com")
    await _seed(client, a)
    await client.post(f"{API}/cycles", headers=b.h, json={"start_date": "2026-05-05", "notes": "B-ONLY"})
    r = await client.post(f"{API}/privacy/export", headers=a.h)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["user"]["email"] == "a@example.com"
    assert len(d["cycles"]) == 1 and d["cycles"][0]["notes"] == "n-a@example.com"  # decrypted for the owner
    assert len(d["symptoms"]) == 1 and len(d["lifestyle"]) == 1 and len(d["mood"]) == 1
    assert "B-ONLY" not in r.text and "b@example.com" not in r.text
    assert "password" not in r.text.lower().replace("password_reset", "")


async def test_delete_account_requires_correct_password_and_confirm(client):
    acc = await signup(client)
    r = await client.request("DELETE", f"{API}/privacy/account", headers=acc.h, json={"password": "wrong", "confirm": "DELETE"})
    assert r.status_code == 403
    r = await client.request("DELETE", f"{API}/privacy/account", headers=acc.h, json={"password": PASSWORD, "confirm": "yes"})
    assert r.status_code == 400
    assert (await client.get(f"{API}/auth/me", headers=acc.h)).status_code == 200  # still there


async def test_delete_account_erases_everything_and_anonymises_audit(client, sessionmaker_):
    a, b = await signup(client, "gone@example.com"), await signup(client, "stay@example.com")
    await _seed(client, a)
    await _seed(client, b)
    r = await client.request("DELETE", f"{API}/privacy/account", headers=a.h, json={"password": PASSWORD, "confirm": "DELETE"})
    assert r.status_code == 204
    async with sessionmaker_() as s:
        assert (await s.execute(text("select count(*) from users where email='gone@example.com'"))).scalar_one() == 0
        for t in USER_TABLES:
            n = (await s.execute(text(f"select count(*) from {t} where user_id = :u"), {"u": a.user_id})).scalar_one()
            assert n == 0, t
        assert (await s.execute(text("select count(*) from cycle_records"))).scalar_one() == 1  # B's data intact
        orphan = (await s.execute(text("select count(*) from audit_logs where user_id is null"))).scalar_one()
        assert orphan >= 2
        ref = (await s.execute(text("select details->>'ref' from audit_logs where action='account_deleted'"))).scalar_one()
        assert ref and a.user_id not in ref
        leaked = (await s.execute(text("select count(*) from audit_logs where details::text ilike '%gone@example.com%'"))).scalar_one()
        assert leaked == 0
    # old tokens and credentials are useless
    assert (await client.get(f"{API}/auth/me", headers=a.h)).status_code == 401
    assert (await client.post(f"{API}/auth/refresh", json={"refresh_token": a.refresh})).status_code == 401
    assert (await client.post(f"{API}/auth/login", json={"email": "gone@example.com", "password": PASSWORD})).status_code == 401
    # the email can be registered again as a brand-new, empty account
    again = await signup(client, "gone@example.com")
    assert (await client.get(f"{API}/cycles", headers=again.h)).json() == []
