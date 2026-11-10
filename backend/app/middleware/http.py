import re
import time
import uuid

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import request_id_ctx

REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["method", "route"])
_VALID_RID = re.compile(r"^[A-Za-z0-9\-_]{8,64}$")


class RequestMiddleware(BaseHTTPMiddleware):
    """Request ID, security headers, Prometheus metrics (route templates only: no IDs in labels)."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if _VALID_RID.match(incoming) else uuid.uuid4().hex
        request.state.request_id = rid
        token = request_id_ctx.set(rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        route = getattr(request.scope.get("route"), "path", "unmatched")
        LATENCY.labels(request.method, route).observe(time.perf_counter() - start)
        REQUESTS.labels(request.method, route, str(response.status_code)).inc()
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response
