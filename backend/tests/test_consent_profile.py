from sqlalchemy import text

from tests.helpers import signup

API = "/api/v1"


async def test_consents_listed_for_all_purposes(client):
    acc = await signup(client, consents=[{"purpose": "health_tracking", "granted": True}])
    r = await client.get(f"{API}/consents", headers=acc.h)
    got = {c["purpose"]: c["granted"] for c in r.json()}
    assert got == {"health_tracking": True, "ml_processing": False, "llm_external": False, "analytics": False}


async def test_health_endpoints_blocked_without_consent_then_allowed(client):
    acc = await signup(client, consents=[])
    for method, path, body in [("get", "/cycles", None), ("get", "/symptoms", None), ("get", "/lifestyle", None),
                               ("get", "/mood", None), ("get", "/cycles/stats", None),
                               ("post", "/cycles", {"start_date": "2026-01-01"})]:
        r = await getattr(client, method)(f"{API}{path}", headers=acc.h, **({"json": body} if body else {}))
        assert r.status_code == 403 and r.json()["error"]["code"] == "consent_required", path
    assert (await client.put(f"{API}/consents/health_tracking", headers=acc.h, json={"granted": True})).status_code == 200
    assert (await client.get(f"{API}/cycles", headers=acc.h)).status_code == 200


async def test_revoking_consent_blocks_again_and_is_audited(client, sessionmaker_):
    acc = await signup(client)
    assert (await client.get(f"{API}/cycles", headers=acc.h)).status_code == 200
    r = await client.put(f"{API}/consents/health_tracking", headers=acc.h, json={"granted": False})
    assert r.status_code == 200 and r.json()["granted"] is False and r.json()["revoked_at"]
    assert (await client.get(f"{API}/cycles", headers=acc.h)).status_code == 403
    async with sessionmaker_() as s:
        n = (await s.execute(text("select count(*) from audit_logs where action='consent_revoked'"))).scalar_one()
    assert n == 1


async def test_unknown_consent_purpose_rejected(client):
    acc = await signup(client)
    r = await client.put(f"{API}/consents/marketing", headers=acc.h, json={"granted": True})
    assert r.status_code == 400


async def test_consent_endpoints_need_auth(client):
    assert (await client.get(f"{API}/consents")).status_code == 401


async def test_profile_roundtrip_and_encrypted_at_rest(client, sessionmaker_):
    acc = await signup(client)
    body = {"date_of_birth": "1999-05-04", "height_cm": 162.5, "weight_kg": 55, "typical_cycle_length": 28,
            "contraceptive_use": False, "conditions_self_reported": ["PCOS"], "activity_level": "moderate",
            "dietary_prefs": ["vegetarian"], "goals": ["sleep better"]}
    r = await client.put(f"{API}/profile", headers=acc.h, json=body)
    assert r.status_code == 200 and r.json()["conditions_self_reported"] == ["PCOS"]
    got = (await client.get(f"{API}/profile", headers=acc.h)).json()
    assert got["height_cm"] == 162.5 and got["goals"] == ["sleep better"]
    async with sessionmaker_() as s:
        raw = (await s.execute(text("select conditions_self_reported from health_profiles"))).scalar_one()
    assert raw.startswith("k1:") and "PCOS" not in raw


async def test_profile_validation(client):
    acc = await signup(client)
    for bad in ({"height_cm": 10}, {"weight_kg": 1000}, {"typical_cycle_length": 5},
                {"date_of_birth": "2999-01-01"}, {"activity_level": "godlike"}):
        assert (await client.put(f"{API}/profile", headers=acc.h, json=bad)).status_code == 400, bad


async def test_profile_isolated_per_user(client):
    a, b = await signup(client), await signup(client)
    await client.put(f"{API}/profile", headers=a.h, json={"goals": ["a-goal"]})
    assert (await client.get(f"{API}/profile", headers=b.h)).json()["goals"] == []
