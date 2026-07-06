"""Versioned ``/api/v1`` routes.

These routes are a thin, standardized, versioned facade over the *same* provider
the legacy routes use. They add response envelopes, OpenAPI documentation, and
(on mutating control routes) JWT-ready authorization — but no new trading
business logic. Read routes are public, mirroring the legacy read surface;
control mutations require an authenticated user.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.errors import BadRequestError
from api.schemas import ErrorResponse, SuccessResponse, success
from api.security import Principal, require_user
from api.v1.dependencies import get_provider

router = APIRouter(prefix="/api/v1")

# Documented error responses reused across protected routes.
_AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Authentication required."},
}


# --- Command models (mirror the legacy control contract) -------------------


class TradingCommand(BaseModel):
    enabled: bool


class StrategyCommand(BaseModel):
    policy: str


class RiskCommand(BaseModel):
    position_limit_enabled: bool


class ModeCommand(BaseModel):
    mode: str


# --- Health ----------------------------------------------------------------


@router.get(
    "/health",
    tags=["health"],
    summary="Service health",
    response_model=SuccessResponse,
)
def health() -> dict[str, Any]:
    """Public liveness probe. Always safe to call unauthenticated."""

    return success({"status": "ok"})


@router.get(
    "/health/db",
    tags=["health"],
    summary="Database health",
    response_model=SuccessResponse,
)
def health_db() -> dict[str, Any]:
    """Report database connectivity (v2 persistence layer)."""

    from db import check_db  # lazy: no DB engine touched unless this is called

    return success(check_db())


# --- Read routes (public) --------------------------------------------------


@router.get(
    "/state",
    tags=["state"],
    summary="Current dashboard state",
    response_model=SuccessResponse,
)
def get_state(provider=Depends(get_provider)) -> dict[str, Any]:
    return success(provider.snapshot())


@router.get(
    "/trades",
    tags=["trades"],
    summary="Recent trades",
    response_model=SuccessResponse,
)
def get_trades(provider=Depends(get_provider)) -> dict[str, Any]:
    return success(provider.snapshot()["trades"])


@router.get(
    "/control",
    tags=["control"],
    summary="Current control state",
    response_model=SuccessResponse,
)
def get_control(provider=Depends(get_provider)) -> dict[str, Any]:
    return success(provider.get_control())


# --- Control mutations (require an authenticated user) ---------------------


@router.post(
    "/control/trading",
    tags=["control"],
    summary="Enable or disable trading",
    response_model=SuccessResponse,
    responses=_AUTH_RESPONSES,
)
def set_trading(
    command: TradingCommand,
    provider=Depends(get_provider),
    _user: Principal = Depends(require_user),
) -> dict[str, Any]:
    return success(provider.set_trading(command.enabled))


@router.post(
    "/control/strategy",
    tags=["control"],
    summary="Select the strategy policy",
    response_model=SuccessResponse,
    responses=_AUTH_RESPONSES,
)
def set_strategy(
    command: StrategyCommand,
    provider=Depends(get_provider),
    _user: Principal = Depends(require_user),
) -> dict[str, Any]:
    try:
        return success(provider.set_strategy(command.policy))
    except ValueError as error:
        raise BadRequestError(str(error))


@router.post(
    "/control/risk",
    tags=["control"],
    summary="Toggle the position limit",
    response_model=SuccessResponse,
    responses=_AUTH_RESPONSES,
)
def set_risk(
    command: RiskCommand,
    provider=Depends(get_provider),
    _user: Principal = Depends(require_user),
) -> dict[str, Any]:
    return success(provider.set_risk(command.position_limit_enabled))


@router.post(
    "/control/mode",
    tags=["control"],
    summary="Switch the runtime mode",
    response_model=SuccessResponse,
    responses=_AUTH_RESPONSES,
)
def set_mode(
    command: ModeCommand,
    provider=Depends(get_provider),
    _user: Principal = Depends(require_user),
) -> dict[str, Any]:
    try:
        return success(provider.set_mode(command.mode))
    except ValueError as error:
        raise BadRequestError(str(error))


# --- Authentication introspection ------------------------------------------


@router.get(
    "/auth/me",
    tags=["auth"],
    summary="Current authenticated principal",
    response_model=SuccessResponse,
    responses=_AUTH_RESPONSES,
)
def read_me(user: Principal = Depends(require_user)) -> dict[str, Any]:
    """Return the caller's identity as derived from their bearer token."""

    return success({"subject": user.subject, "roles": [r.value for r in user.roles]})
