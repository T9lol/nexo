"""Standardized API success/error envelopes.

Every ``/api/v1`` response is wrapped in one of these shapes so clients can rely
on a single contract:

    success:  {"success": true,  "data": <payload>, "meta": {"api_version": "v1"}}
    error:    {"success": false, "error": {"code", "message", "details"}}

Legacy (unversioned) routes keep their original raw shapes for frontend/proxy
backwards-compatibility and are intentionally *not* wrapped.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResponseMeta(BaseModel):
    # ``extra="allow"`` so endpoints can attach context (e.g. a currency basis)
    # without every route needing a bespoke response model. Without this,
    # response_model coercion would silently drop unknown meta keys.
    model_config = ConfigDict(extra="allow")

    api_version: str = "v1"


class SuccessResponse(BaseModel):
    """Envelope for successful responses."""

    success: bool = True
    data: Any = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Envelope for error responses."""

    success: bool = False
    error: ErrorDetail


def success(data: Any, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a success-envelope dict."""

    return {
        "success": True,
        "data": data,
        "meta": meta or {"api_version": "v1"},
    }


def error_body(
    code: str, message: str, *, details: Any | None = None
) -> dict[str, Any]:
    """Build an error-envelope dict."""

    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
    }
