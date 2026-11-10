import re
import sys
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.deps import AuthContext, require_role
from app.core.exceptions import register_exception_handlers
from tests.helpers import signup

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "gen_docs"))


@pytest.fixture
async def rbac_client():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/admin-only")
    async def admin_only(auth: AuthContext = Depends(require_role("admin"))):
        return {"ok": True}

    @app.get("/any-role")
    async def any_role(auth: AuthContext = Depends(require_role("user", "admin"))):
        return {"ok": True}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c


async def test_role_based_access(rbac_client, client, sessionmaker_):
    acc = await signup(client)
    assert (await rbac_client.get("/admin-only")).status_code == 401
    r = await rbac_client.get("/admin-only", headers=acc.h)
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"
    assert (await rbac_client.get("/any-role", headers=acc.h)).status_code == 200
    async with sessionmaker_() as s:
        await s.execute(text("update users set role='admin'"))
        await s.commit()
    assert (await rbac_client.get("/admin-only", headers=acc.h)).status_code == 200


async def test_invalid_role_rejected_by_database(sessionmaker_, client):
    from sqlalchemy.exc import IntegrityError
    await signup(client)
    async with sessionmaker_() as s:
        with pytest.raises(IntegrityError):
            await s.execute(text("update users set role='superuser'"))


async def test_deactivated_user_loses_access(client, sessionmaker_):
    acc = await signup(client)
    async with sessionmaker_() as s:
        await s.execute(text("update users set is_active=false"))
        await s.commit()
    assert (await client.get("/api/v1/auth/me", headers=acc.h)).status_code == 401
    r = await client.post("/api/v1/auth/login", json={"email": acc.email, "password": "Tr1cky-Horse-Battery-9"})
    assert r.status_code == 401


async def test_health_ready_metrics(client):
    assert (await client.get("/health")).json()["service"] == "backend"
    r = await client.get("/ready")
    assert r.status_code == 200 and r.json() == {"postgres": "ok", "redis": "ok"}
    m = await client.get("/metrics")
    assert m.status_code == 200 and "http_requests_total" in m.text


async def test_metrics_labels_use_route_templates_not_ids(client):
    acc = await signup(client)
    cid = (await client.post("/api/v1/cycles", headers=acc.h, json={"start_date": "2026-01-01"})).json()["id"]
    await client.delete(f"/api/v1/cycles/{cid}", headers=acc.h)
    text_ = (await client.get("/metrics")).text
    assert 'route="/cycles/{item_id}"' in text_  # template, not the concrete path
    assert cid not in text_ and acc.user_id not in text_


async def test_error_envelope_and_request_id(client):
    r = await client.get("/api/v1/does-not-exist", headers={"X-Request-ID": "client-supplied-12345"})
    assert r.status_code == 404
    e = r.json()["error"]
    assert e["code"] == "not_found" and e["request_id"] == "client-supplied-12345"
    assert r.headers["x-request-id"] == "client-supplied-12345"
    r = await client.get("/api/v1/does-not-exist", headers={"X-Request-ID": "bad id with spaces!!"})
    assert re.fullmatch(r"[0-9a-f]{32}", r.json()["error"]["request_id"])  # invalid id replaced, not echoed
    assert (await client.post("/api/v1/auth/login", content="{broken", headers={"content-type": "application/json"})).status_code == 400
    assert (await client.delete("/api/v1/auth/me")).status_code == 405


async def test_unhandled_exception_is_hidden(client, monkeypatch):
    from httpx import ASGITransport

    from app.main import app

    async def boom(*a, **k):
        raise RuntimeError("secret internal detail /etc/passwd")
    monkeypatch.setattr("app.services.auth.AuthService.login", boom)
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://t") as c:
        r = await c.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "x"})
    assert r.status_code == 500 and "secret" not in r.text and r.json()["error"]["code"] == "internal_error"


async def test_security_headers(client):
    r = await client.get("/api/v1/consents")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["cache-control"] == "no-store"


async def test_openapi_matches_contract_for_implemented_groups(client):
    """Every implemented operation must exist in the design contract and vice versa (for ZIP 2 groups)."""
    from api_spec import E
    groups = {"Auth", "Profile", "Consent", "Cycles", "Symptoms", "Lifestyle", "Mood", "Vault"}
    contract = {(m, "/api/v1" + re.sub(r"\{id\}", "{item_id}", p)) for g, m, p, *_ in E if g in groups}
    spec = (await client.get("/openapi.json")).json()
    impl = {(m.upper(), p) for p, v in spec["paths"].items() for m in v
            if p.startswith("/api/v1")}
    assert impl - contract == set(), f"implemented but not in contract: {impl - contract}"
    assert contract - impl == set(), f"in contract but not implemented: {contract - impl}"


async def test_openapi_documents_real_error_shape(client):
    """Validation errors are 400 + the error envelope; FastAPI's default 422/HTTPValidationError must not be advertised."""
    spec = (await client.get("/openapi.json")).json()
    assert "HTTPValidationError" not in spec["components"]["schemas"] and "ErrorEnvelope" in spec["components"]["schemas"]
    post = spec["paths"]["/api/v1/auth/login"]["post"]["responses"]
    assert "422" not in post and "400" in post
    assert post["400"]["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorEnvelope")
