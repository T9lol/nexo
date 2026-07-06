"""Portfolio module REST API (``/api/v1/portfolio``).

Read-only, public endpoints projecting the live engine snapshot into Portfolio
views. Standardized envelopes; currency basis documented in ``meta``.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path, Query

from api.config import Settings, get_settings
from api.currency import currency_meta
from api.errors import NotFoundError
from api.schemas import ErrorResponse, SuccessResponse, success
from api.v1 import derivations
from api.v1.dependencies import get_provider

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.get(
    "/summary",
    summary="Portfolio summary",
    response_model=SuccessResponse,
)
def get_summary(
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    rate = settings.usd_myr_rate
    return success(
        derivations.portfolio_summary(provider.snapshot(), rate),
        meta=currency_meta(rate),
    )


@router.get(
    "/holdings",
    summary="Holdings",
    response_model=SuccessResponse,
)
def get_holdings(
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    rate = settings.usd_myr_rate
    return success(
        derivations.holdings(provider.snapshot(), rate), meta=currency_meta(rate)
    )


@router.get(
    "/allocation",
    summary="Portfolio allocation",
    response_model=SuccessResponse,
)
def get_allocation(
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    rate = settings.usd_myr_rate
    return success(
        derivations.allocation(provider.snapshot(), rate), meta=currency_meta(rate)
    )


@router.get(
    "/value-history",
    summary="Portfolio value history",
    response_model=SuccessResponse,
)
def get_value_history(
    limit: int | None = Query(
        default=None, ge=1, le=500, description="Return only the most recent N points."
    ),
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    return success(
        derivations.value_history(provider.snapshot(), limit=limit),
        meta=currency_meta(settings.usd_myr_rate),
    )


@router.get(
    "/assets/{symbol}",
    summary="Asset details",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse, "description": "Unknown symbol."}},
)
def get_asset_details(
    symbol: str = Path(..., min_length=1, max_length=16, description="Asset symbol, e.g. BTC."),
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    rate = settings.usd_myr_rate
    data = derivations.asset_details(provider.snapshot(), symbol, rate)
    if data is None:
        raise NotFoundError(f"Unknown asset symbol: {symbol!r}", code="not_found")
    return success(data, meta=currency_meta(rate))
