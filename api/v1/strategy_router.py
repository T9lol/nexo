"""Strategy Center REST API (``/api/v1/strategies``).

Read routes are public; enable/disable mutations require an authenticated user
(JWT-ready, same posture as the Sprint 1 control mutations). Enable/disable map
honestly onto the engine's single-active-strategy model:

* **enable** a strategy = activate it as a manual override (``set_strategy``).
* **disable** a strategy = clear the manual override so adaptive selection
  resumes (``set_strategy("auto")``). Disabling a strategy that is not the
  current override is an idempotent no-op — the engine has no independent
  per-strategy on/off switch, so none is fabricated.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path

from api.errors import BadRequestError, NotFoundError
from api.logging import get_logger
from api.schemas import ErrorResponse, SuccessResponse, success
from api.security import Principal, require_user
from api.v1 import strategy_derivations
from api.v1.dependencies import get_provider

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])
logger = get_logger("strategies")

_AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Authentication required."},
    404: {"model": ErrorResponse, "description": "Unknown strategy."},
}


def _resolve(provider, name: str) -> tuple[dict[str, Any], str]:
    """Return (snapshot, canonical strategy name) or raise 404."""

    snapshot = provider.snapshot()
    strategies = snapshot.get("strategies", {})
    match = strategy_derivations._match_name(strategies, name)
    if match is None:
        raise NotFoundError(f"Unknown strategy: {name!r}", code="not_found")
    return snapshot, match


@router.get("", summary="Strategy list", response_model=SuccessResponse)
def list_strategies(provider=Depends(get_provider)) -> dict[str, Any]:
    return success(strategy_derivations.strategy_list(provider.snapshot()))


@router.get(
    "/comparison", summary="Strategy comparison", response_model=SuccessResponse
)
def compare_strategies(provider=Depends(get_provider)) -> dict[str, Any]:
    return success(strategy_derivations.strategy_comparison(provider.snapshot()))


@router.get(
    "/{name}",
    summary="Strategy details",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse, "description": "Unknown strategy."}},
)
def get_strategy(
    name: str = Path(..., min_length=1, max_length=32),
    provider=Depends(get_provider),
) -> dict[str, Any]:
    data = strategy_derivations.strategy_details(provider.snapshot(), name)
    if data is None:
        raise NotFoundError(f"Unknown strategy: {name!r}", code="not_found")
    return success(data)


@router.post(
    "/{name}/enable",
    summary="Enable (activate) a strategy",
    response_model=SuccessResponse,
    responses=_AUTH_RESPONSES,
)
def enable_strategy(
    name: str = Path(..., min_length=1, max_length=32),
    provider=Depends(get_provider),
    user: Principal = Depends(require_user),
) -> dict[str, Any]:
    _snapshot, match = _resolve(provider, name)
    try:
        provider.set_strategy(match)  # manual override -> activates this strategy
    except ValueError as error:
        raise BadRequestError(str(error))
    logger.info(
        "strategy enabled",
        extra={"event": "strategy_enable", "path": match},
    )
    return success(strategy_derivations.strategy_details(provider.snapshot(), match))


@router.post(
    "/{name}/disable",
    summary="Disable (clear override for) a strategy",
    response_model=SuccessResponse,
    responses=_AUTH_RESPONSES,
)
def disable_strategy(
    name: str = Path(..., min_length=1, max_length=32),
    provider=Depends(get_provider),
    user: Principal = Depends(require_user),
) -> dict[str, Any]:
    snapshot, match = _resolve(provider, name)
    control = snapshot.get("control") or {}
    if control.get("strategy_policy") == match:
        provider.set_strategy("auto")  # clear the override; adaptive resumes
        logger.info(
            "strategy override cleared",
            extra={"event": "strategy_disable", "path": match},
        )
    # Not the active override -> nothing to disable (idempotent).
    return success(strategy_derivations.strategy_details(provider.snapshot(), match))
