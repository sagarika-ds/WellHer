
from app.core.context import RequestContext
from app.repositories.identity import UserRepo
from app.services.egress import EgressGate, scrub_text
from tests.helpers import signup

API = "/api/v1"
CTX = RequestContext(None, "127.0.0.1", "pytest", "rid-test-0001")
CONTEXT = {"cycle_summary": {"next": "2026-12-01", "note": "mail asha.rao@example.com"},
           "patterns": ["headache around day 1"], "secret_blob": "do-not-send"}


async def _user(sessionmaker_, acc):
    async with sessionmaker_() as s:
        return await UserRepo(s).get(__import__("uuid").UUID(acc.user_id))


async def _prepare(sessionmaker_, acc, provider, text="hello", context=None):
    user = await _user(sessionmaker_, acc)
    async with sessionmaker_() as s:
        return await EgressGate(s).prepare(user, provider, text, CONTEXT if context is None else context,
                                           RequestContext(user.id, "127.0.0.1", "pytest", "rid-test-0001"))


async def _settings(client, acc, **over):
    body = {"personalization_enabled": True, "external_llm_allowed": False, "context_allowlist": [],
            "chat_retention_days": 30, **over}
    r = await client.put(f"{API}/privacy/ai-settings", headers=acc.h, json=body)
    assert r.status_code == 200, r.text


def test_scrub_removes_identifiers_but_keeps_dates_and_numbers():
    class U:
        display_name = "Asha Rao"
        email = "asha.rao@example.com"
    out = scrub_text("Hi Asha, mail asha.rao@example.com or call +91 98765 43210. Period on 2026-11-07, slept 7.5h, "
                     "cycle 28 days. Rao family.", U())
    assert "[email]" in out and "[phone]" in out and out.count("[name]") == 2
    assert "2026-11-07" in out and "7.5h" in out and "28 days" in out
    assert "98765" not in out and "example.com" not in out


async def test_local_provider_drops_context_without_ml_consent(client, sessionmaker_):
    acc = await signup(client, consents=[{"purpose": "health_tracking", "granted": True}])
    await _settings(client, acc, context_allowlist=["cycle_summary", "patterns"])
    d = await _prepare(sessionmaker_, acc, "local", text="I am Asha, mail asha.rao@example.com")
    assert d.allowed and d.context == {}  # allowlisted, but ml_processing consent missing -> nothing sent
    assert "Asha" not in d.text and "example.com" not in d.text


async def test_context_limited_to_allowlist_and_scrubbed(client, sessionmaker_):
    acc = await signup(client, email="asha.rao@example.com")
    await _settings(client, acc, context_allowlist=["cycle_summary"])
    d = await _prepare(sessionmaker_, acc, "local")
    assert d.allowed and set(d.context) == {"cycle_summary"}
    assert d.context["cycle_summary"]["next"] == "2026-12-01"
    assert "example.com" not in str(d.context) and "[email]" in str(d.context)
    assert "do-not-send" not in str(d.context) and "patterns" not in d.context


async def test_hosted_blocked_without_llm_external_consent(client, sessionmaker_):
    acc = await signup(client, consents=[{"purpose": "health_tracking", "granted": True},
                                         {"purpose": "ml_processing", "granted": True}])
    d = await _prepare(sessionmaker_, acc, "hosted")
    assert not d.allowed and d.reason == "consent_llm_external_not_granted" and d.text is None


async def test_hosted_blocked_when_disabled_in_ai_settings(client, sessionmaker_):
    acc = await signup(client)  # all consents granted
    d = await _prepare(sessionmaker_, acc, "hosted")
    assert not d.allowed and d.reason == "external_llm_disabled_in_ai_settings"


async def test_hosted_allowed_only_when_both_and_revocation_blocks_again(client, sessionmaker_):
    acc = await signup(client)
    await _settings(client, acc, external_llm_allowed=True, context_allowlist=["patterns"])
    d = await _prepare(sessionmaker_, acc, "hosted")
    assert d.allowed and set(d.context) == {"patterns"}
    await client.put(f"{API}/consents/llm_external", headers=acc.h, json={"granted": False})
    d2 = await _prepare(sessionmaker_, acc, "hosted")
    assert not d2.allowed and d2.reason == "consent_llm_external_not_granted"


async def test_unknown_provider_blocked(client, sessionmaker_):
    acc = await signup(client)
    assert (await _prepare(sessionmaker_, acc, "some-random-api")).reason == "unknown_provider"


async def test_every_decision_audited_without_payload(client, sessionmaker_):
    from sqlalchemy import text
    acc = await signup(client, email="asha.rao@example.com")
    await _settings(client, acc, context_allowlist=["cycle_summary"])
    await _prepare(sessionmaker_, acc, "local", text="private sentence 12345")
    await _prepare(sessionmaker_, acc, "hosted")
    async with sessionmaker_() as s:
        rows = (await s.execute(text("select action, outcome, details::text from audit_logs "
                                     "where action like 'egress_%' order by occurred_at"))).all()
    assert [(r[0], r[1]) for r in rows] == [("egress_allowed", "success"), ("egress_blocked", "blocked")]
    assert "private sentence" not in "".join(r[2] for r in rows) and "2026-12-01" not in "".join(r[2] for r in rows)
    assert "cycle_summary" in rows[0][2]
