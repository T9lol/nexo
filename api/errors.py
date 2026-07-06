"""Application error types and global exception handling.

Two design goals held simultaneously:

1. ``/api/v1`` gets standardized error envelopes (:mod:`api.schemas`) for every
   failure mode — domain errors, validation errors, HTTP errors, and uncaught
   exceptions.
2. Legacy (unversioned) routes keep FastAPI's *default* error shapes so the
   existing frontend/proxy and test-suite behaviour is preserved byte-for-byte
   (e.g. ``{"detail": ...}`` on 400/422).

The handlers therefore branch on the request path.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.config import get_settings
from api.logging import get_logger
from api.schemas import error_body


class AppError(Exception):
    """Base class for domain errors that map to standardized API responses."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details
        self.headers = headers


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


# Map bare HTTP status codes to stable error codes for the v1 envelope.
_STATUS_CODE_NAMES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    503: "service_unavailable",
}


def _code_for_status(status_code: int) -> str:
    return _STATUS_CODE_NAMES.get(status_code, f"http_{status_code}")


def _is_versioned(request: Request) -> bool:
    prefix = get_settings().api_v1_prefix
    return request.url.path.startswith(prefix)


def install_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on ``app``."""

    logger = get_logger()

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error(
                exc.message,
                extra={
                    "event": "app_error",
                    "path": request.url.path,
                    "error_code": exc.code,
                    "status_code": exc.status_code,
                },
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, details=exc.details),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        # Versioned routes get the standardized envelope; legacy routes keep the
        # framework default ({"detail": ...}) so existing clients are unaffected.
        if _is_versioned(request):
            return JSONResponse(
                status_code=exc.status_code,
                content=error_body(
                    _code_for_status(exc.status_code), str(exc.detail)
                ),
                headers=getattr(exc, "headers", None),
            )
        return await http_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        if _is_versioned(request):
            return JSONResponse(
                status_code=422,
                content=error_body(
                    "validation_error",
                    "Request validation failed.",
                    details=jsonable_encoder(exc.errors()),
                ),
            )
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(Exception)
    async def _handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Last-resort safety net: never leak internals or stack traces to the
        # client. Log the full exception with structured context.
        logger.error(
            "Unhandled exception",
            extra={
                "event": "unhandled_exception",
                "path": request.url.path,
                "status_code": 500,
            },
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content=error_body("internal_error", "Internal server error."),
        )
