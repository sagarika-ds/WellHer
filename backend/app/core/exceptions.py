"""Uniform error envelope: {"error": {"code", "message", "request_id"}}."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("app.errors")


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code, self.code, self.message = status_code, code, message


def unauthenticated(message: str = "Authentication required.") -> AppError:
    return AppError(401, "unauthenticated", message)


def forbidden(message: str = "You do not have access to this resource.") -> AppError:
    return AppError(403, "forbidden", message)


def consent_required(purpose: str) -> AppError:
    return AppError(403, "consent_required", f"Consent for {purpose} is required.")


def not_found(what: str = "Resource") -> AppError:
    return AppError(404, "not_found", f"{what} not found.")


def conflict(message: str) -> AppError:
    return AppError(409, "conflict", message)


def validation(message: str) -> AppError:
    return AppError(400, "validation_error", message)


def _envelope(request: Request, status: int, code: str, message: str, headers=None) -> JSONResponse:
    rid = getattr(request.state, "request_id", "")
    return JSONResponse(
        {"error": {"code": code, "message": message, "request_id": rid}},
        status_code=status, headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return _envelope(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        # Report field locations and rules, never the submitted values.
        parts = [f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
        return _envelope(request, 400, "validation_error", "; ".join(parts)[:500])

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        return _envelope(request, exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("unhandled error", extra={"path": request.url.path})
        return _envelope(request, 500, "internal_error", "An internal error occurred.")
