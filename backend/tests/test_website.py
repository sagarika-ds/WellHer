"""The backend also serves the plain HTML/CSS/JS website from <repo>/frontend."""
import pytest

from app.main import FRONTEND_DIR

pytestmark = pytest.mark.skipif(not FRONTEND_DIR.is_dir(), reason="no frontend folder next to the backend")


async def test_root_serves_index_html(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "<title>WellHer</title>" in r.text


async def test_static_assets_have_correct_types(client):
    css = await client.get("/css/style.css")
    assert css.status_code == 200 and css.headers["content-type"].startswith("text/css")
    js = await client.get("/js/api.js")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]


async def test_website_files_are_revalidated_so_edits_show_up(client):
    for path in ("/", "/css/style.css", "/js/api.js"):
        assert (await client.get(path)).headers["cache-control"] == "no-cache"


async def test_api_and_ops_routes_still_win_over_the_website(client):
    assert (await client.get("/health")).json()["status"] == "ok"
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthenticated"


async def test_missing_page_uses_the_error_envelope(client):
    r = await client.get("/no-such-page.html")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


async def test_files_outside_the_frontend_folder_are_not_served(client):
    r = await client.get("/..%2Fbackend%2F.env")
    assert r.status_code == 404
    assert "JWT_SECRET" not in r.text
