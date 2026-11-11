"""Core backend (ZIP 2): auth, consent, audit, encrypted records, privacy, event pipeline."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import app.events.handlers  # noqa: F401  (registers handlers)
from app.api.deps import get_redis
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.redis import close_redis
from app.db.session import dispose_engine, get_session
from app.events.bus import close_pool
from app.middleware.http import RequestMiddleware

VERSION = "0.2.0"

# The website (plain HTML/CSS/JS) lives in <repo>/frontend, next to this backend folder.
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


class WebsiteFiles(StaticFiles):
    """Static files with `Cache-Control: no-cache`: the browser re-checks every file on each load,
    so an edited page or script is picked up at once (unchanged files still come back as a quick 304)."""

    async def get_response(self, path: str, scope):  # type: ignore[override]
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()  # fails fast on missing/invalid secrets
    configure_logging(settings.log_level)
    logging.getLogger("app").info("starting backend %s env=%s", VERSION, settings.app_env)
    yield
    await close_pool()
    await close_redis()
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Women's Wellness: Core Backend", version=VERSION, lifespan=lifespan)
    app.add_middleware(RequestMiddleware)
    if settings.cors_origin_list:
        app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list,
                           allow_methods=["*"], allow_headers=["*"], allow_credentials=False)
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    def custom_openapi() -> dict:
        """Document the real error shape: validation errors are 400 + error envelope, not FastAPI's 422."""
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        comps = schema.setdefault("components", {}).setdefault("schemas", {})
        comps.pop("HTTPValidationError", None)
        comps.pop("ValidationError", None)
        comps["ErrorEnvelope"] = {
            "type": "object", "required": ["error"],
            "properties": {"error": {
                "type": "object", "required": ["code", "message", "request_id"],
                "properties": {"code": {"type": "string"}, "message": {"type": "string"},
                               "request_id": {"type": "string"}},
            }},
        }
        for ops in schema["paths"].values():
            for op in ops.values():
                responses = op.get("responses", {})
                if "422" in responses:
                    del responses["422"]
                    responses["400"] = {"description": "Validation error", "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/ErrorEnvelope"}}}}
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    @app.get("/health", tags=["Ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "backend", "version": VERSION}

    @app.get("/ready", tags=["Ops"])
    async def ready(response: Response, s: AsyncSession = Depends(get_session),
                    r: Redis = Depends(get_redis)) -> dict[str, str]:
        checks = {}
        try:
            await s.execute(text("select 1"))
            checks["postgres"] = "ok"
        except Exception:
            checks["postgres"] = "down"
        try:
            await r.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "down"
        if "down" in checks.values():
            response.status_code = 503
        return checks

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Serve the website from the same server as the API, so the browser needs no CORS.
    # Mounted LAST: the API, /docs, /health etc. are matched first; any other path is looked up as a file.
    # html=True makes "/" return index.html.
    # Skipped when the folder is absent (e.g. in the backend-only Docker image).
    if FRONTEND_DIR.is_dir():
        app.mount("/", WebsiteFiles(directory=FRONTEND_DIR, html=True), name="website")

    return app


app = create_app()
