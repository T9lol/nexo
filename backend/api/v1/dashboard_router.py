"""Dashboard module REST API (``/api/v1/dashboard``).

Read-only, public endpoints that project the live engine snapshot into the
Dashboard views. Standardized envelopes; currency basis documented in ``meta``.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from api.config import Settings, get_settings
from api.currency import currency_meta
from api.schemas import SuccessResponse, success
from api.v1 import derivations
from api.v1.dependencies import get_provider

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    summary="Dashboard summary",
    response_model=SuccessResponse,
)
def get_summary(
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Total assets (RM primary, approx USD), today's/monthly PnL, active
    strategy, and system status."""

    rate = settings.usd_myr_rate
    data = derivations.dashboard_summary(provider.snapshot(), rate)
    return success(data, meta=currency_meta(rate))


@router.get(
    "/equity-curve",
    summary="Equity curve",
    response_model=SuccessResponse,
)
def get_equity_curve(
    limit: int | None = Query(
        default=None, ge=1, le=500, description="Return only the most recent N points."
    ),
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    data = derivations.equity_curve(provider.snapshot(), limit=limit)
    return success(data, meta=currency_meta(settings.usd_myr_rate))


@router.get(
    "/trades",
    summary="Recent trades",
    response_model=SuccessResponse,
)
def get_recent_trades(
    limit: int | None = Query(
        default=None, ge=1, le=500, description="Return only the most recent N trades."
    ),
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    data = derivations.recent_trades(provider.snapshot(), limit=limit)
    return success(data, meta=currency_meta(settings.usd_myr_rate))
