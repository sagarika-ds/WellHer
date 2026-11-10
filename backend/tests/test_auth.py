from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import text

from app.core.config import get_settings
from tests.helpers import PASSWORD, signup

A = "/api/v1/auth"


async def test_register_creates_user_without_leaking_secrets(client, sessionmaker_):
    r = await client.post(f"{A}/register", json={"email": "Asha@Example.com", "password": PASSWORD,
                                                  "display_name": "  Asha  "})
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"id", "email", "display_name", "role"} and body["role"] == "user"
    assert body["display_name"] == "Asha"
    async with sessionmaker_() as s:
        row = (await s.execute(text("select password_hash from users"))).scalar_one()
        assert row.startswith("$argon2id$") and PASSWORD not in row
        n_consent = (await s.execute(text("select count(*) from user_consents where granted"))).scalar_one()
        assert n_consent == 0  # nothing is granted unless the user chose it
        assert (await s.execute(text("select count(*) from ai_settings"))).scalar_one() == 1
        assert (await s.execute(text("select count(*) from health_profiles"))).scalar_one() == 1


async def test_duplicate_email_case_insensitive(client):
    await signup(client, "dup@example.com")
    r = await client.post(f"{A}/register", json={"email": "DUP@example.com", "password": PASSWORD,
                                                  "display_name": "x"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "conflict"


@pytest.mark.parametrize("payload", [
    {"email": "w1@example.com", "password": "short", "display_name": "x"},
    {"email": "w2@example.com", "password": "aaaaaaaaaaaaaaaa", "display_name": "x"},
    {"email": "janedoe@example.com", "password": "janedoe-is-my-name-1", "display_name": "x"},
    {"email": "not-an-email", "password": PASSWORD, "display_name": "x"},
    {"email": "w3@example.com", "password": PASSWORD, "display_name": "   "},
    {"email": "w4@example.com", "password": PASSWORD, "display_name": "x",
     "consents": [{"purpose": "sell_my_data", "granted": True}]},
])
async def test_register_validation(client, payload):
    r = await client.post(f"{A}/register", json=payload)
    assert r.status_code == 400 and r.json()["error"]["code"] == "validation_error"
    assert PASSWORD not in r.text  # submitted values are never echoed back


async def test_login_success_and_me(client):
    acc = await signup(client)
    r = await client.get(f"{A}/me", headers=acc.h)
    assert r.status_code == 200 and r.json()["email"] == acc.email


async def test_login_failures_are_indistinguishable(client):
    await signup(client, "known@example.com")
    bad_pw = await client.post(f"{A}/login", json={"email": "known@example.com", "password": "nope-nope-nope"})
    no_user = await client.post(f"{A}/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"})
    assert bad_pw.status_code == no_user.status_code == 401
    assert bad_pw.json()["error"]["message"] == no_user.json()["error"]["message"]
    assert bad_pw.json()["error"]["code"] == no_user.json()["error"]["code"]


async def test_login_rate_limit_then_lockout_even_with_correct_password(client):
    await signup(client, "rl@example.com")
    for _ in range(5):
        r = await client.post(f"{A}/login", json={"email": "rl@example.com", "password": "wrong-wrong-1"})
        assert r.status_code == 401
    r = await client.post(f"{A}/login", json={"email": "rl@example.com", "password": PASSWORD})
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"


async def test_successful_login_resets_counter(client):
    await signup(client, "reset@example.com")
    for _ in range(3):
        await client.post(f"{A}/login", json={"email": "reset@example.com", "password": "wrong-wrong-1"})
    assert (await client.post(f"{A}/login", json={"email": "reset@example.com", "password": PASSWORD})).status_code == 200
    for _ in range(4):
        r = await client.post(f"{A}/login", json={"email": "reset@example.com", "password": "wrong-wrong-1"})
        assert r.status_code == 401


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer garbage"}, {"Authorization": "Basic abc"},
                                     {"Authorization": "Bearer "}])
async def test_protected_route_requires_valid_token(client, headers):
    r = await client.get(f"{A}/me", headers=headers)
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthenticated"


async def test_expired_token_rejected(client):
    acc = await signup(client)
    s = get_settings()
    t = jwt.encode({"sub": acc.user_id, "role": "user", "sid": acc.user_id, "jti": "j1", "typ": "access",
                    "exp": int((datetime.now(UTC) - timedelta(seconds=5)).timestamp())},
                   s.jwt_secret, algorithm="HS256")
    r = await client.get(f"{A}/me", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 401


async def test_refresh_rotates_and_old_token_is_dead(client):
    acc = await signup(client)
    r = await client.post(f"{A}/refresh", json={"refresh_token": acc.refresh})
    assert r.status_code == 200
    new = r.json()
    assert new["refresh_token"] != acc.refresh
    assert (await client.get(f"{A}/me", headers={"Authorization": f"Bearer {new['access_token']}"})).status_code == 200


async def test_refresh_token_reuse_revokes_entire_session(client):
    acc = await signup(client)
    new = (await client.post(f"{A}/refresh", json={"refresh_token": acc.refresh})).json()
    # attacker replays the OLD token
    replay = await client.post(f"{A}/refresh", json={"refresh_token": acc.refresh})
    assert replay.status_code == 401
    # the legitimate newest refresh token and access token are now dead too
    assert (await client.post(f"{A}/refresh", json={"refresh_token": new["refresh_token"]})).status_code == 401
    assert (await client.get(f"{A}/me", headers={"Authorization": f"Bearer {new['access_token']}"})).status_code == 401


async def test_refresh_with_unknown_token(client):
    r = await client.post(f"{A}/refresh", json={"refresh_token": "x" * 64})
    assert r.status_code == 401


async def test_expired_refresh_token(client, sessionmaker_):
    acc = await signup(client)
    async with sessionmaker_() as s:
        await s.execute(text("update refresh_tokens set expires_at = now() - interval '1 minute'"))
        await s.commit()
    assert (await client.post(f"{A}/refresh", json={"refresh_token": acc.refresh})).status_code == 401


async def test_logout_kills_access_and_refresh(client):
    acc = await signup(client)
    assert (await client.post(f"{A}/logout", headers=acc.h)).status_code == 200
    assert (await client.get(f"{A}/me", headers=acc.h)).status_code == 401
    assert (await client.post(f"{A}/refresh", json={"refresh_token": acc.refresh})).status_code == 401


async def test_logout_only_affects_that_session(client):
    a1 = await signup(client, "two@example.com")
    r = await client.post(f"{A}/login", json={"email": "two@example.com", "password": PASSWORD})
    a2 = r.json()
    await client.post(f"{A}/logout", headers=a1.h)
    assert (await client.get(f"{A}/me", headers={"Authorization": f"Bearer {a2['access_token']}"})).status_code == 200


@pytest.fixture
def captured_resets(monkeypatch):
    sent = []

    async def fake(email, token):
        sent.append((email, token))
    monkeypatch.setattr("app.services.auth.send_password_reset", fake)
    return sent


async def test_forgot_password_does_not_reveal_accounts(client, captured_resets):
    await signup(client, "real@example.com")
    r1 = await client.post(f"{A}/forgot-password", json={"email": "real@example.com"})
    r2 = await client.post(f"{A}/forgot-password", json={"email": "nobody@example.com"})
    assert r1.status_code == r2.status_code == 202 and r1.json() == r2.json()
    assert [e for e, _ in captured_resets] == ["real@example.com"]


async def test_password_reset_flow(client, captured_resets):
    acc = await signup(client, "flow@example.com")
    await client.post(f"{A}/forgot-password", json={"email": "flow@example.com"})
    token = captured_resets[0][1]
    new_pw = "Another-Strong-Pass-77"
    assert (await client.post(f"{A}/reset-password", json={"token": token, "new_password": new_pw})).status_code == 200
    # old sessions are dead; old password fails; new works
    assert (await client.get(f"{A}/me", headers=acc.h)).status_code == 401
    assert (await client.post(f"{A}/refresh", json={"refresh_token": acc.refresh})).status_code == 401
    assert (await client.post(f"{A}/login", json={"email": "flow@example.com", "password": PASSWORD})).status_code == 401
    assert (await client.post(f"{A}/login", json={"email": "flow@example.com", "password": new_pw})).status_code == 200
    # single use
    again = await client.post(f"{A}/reset-password", json={"token": token, "new_password": "Yet-Another-Pass-88"})
    assert again.status_code == 400 and again.json()["error"]["code"] == "invalid_reset_token"


async def test_reset_token_expiry_and_garbage(client, captured_resets, sessionmaker_):
    await signup(client, "exp@example.com")
    await client.post(f"{A}/forgot-password", json={"email": "exp@example.com"})
    async with sessionmaker_() as s:
        await s.execute(text("update password_reset_tokens set expires_at = now() - interval '1 minute'"))
        await s.commit()
    r = await client.post(f"{A}/reset-password", json={"token": captured_resets[0][1], "new_password": "Zzz-Strong-Pass-99"})
    assert r.status_code == 400
    r = await client.post(f"{A}/reset-password", json={"token": "g" * 40, "new_password": "Zzz-Strong-Pass-99"})
    assert r.status_code == 400


async def test_reset_tokens_stored_hashed(client, captured_resets, sessionmaker_):
    await signup(client, "hash@example.com")
    await client.post(f"{A}/forgot-password", json={"email": "hash@example.com"})
    async with sessionmaker_() as s:
        stored = (await s.execute(text("select token_hash from password_reset_tokens"))).scalar_one()
    assert stored != captured_resets[0][1] and len(stored) == 64


async def test_refresh_tokens_stored_hashed(client, sessionmaker_):
    acc = await signup(client)
    async with sessionmaker_() as s:
        stored = (await s.execute(text("select token_hash from refresh_tokens"))).scalar_one()
    assert stored != acc.refresh and len(stored) == 64
