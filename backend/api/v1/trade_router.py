"""Trade History REST API (``/api/v1/trade-history``).

Read-only, public. Filtering (symbol / side / strategy), pagination, per-trade
lookup, and CSV export over the engine's recorded trades. (The simple
``/api/v1/trades`` list from Sprint 1 is left untouched; this is the richer
Trade History module.)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path, Query, Response

from api.config import Settings, get_settings
from api.currency import currency_meta
from api.errors import NotFoundError
from api.schemas import ErrorResponse, SuccessResponse, success
from api.v1 import trade_derivations
from api.v1.dependencies import get_provider

router = APIRouter(prefix="/api/v1/trade-history", tags=["trade-history"])

# Case-insensitive buy/sell validation -> automatic 422 on anything else.
_SIDE_PATTERN = r"^(?i:buy|sell)$"


@router.get("", summary="Trade history (filtered, paginated)", response_model=SuccessResponse)
def get_trade_history(
    symbol: str | None = Query(default=None, description="Filter by asset symbol."),
    side: str | None = Query(default=None, pattern=_SIDE_PATTERN, description="Filter by side: buy or sell."),
    strategy: str | None = Query(default=None, description="Filter by strategy name."),
    page: int = Query(default=1, ge=1, description="1-based page number."),
    page_size: int = Query(default=20, ge=1, le=200, description="Rows per page."),
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    data = trade_derivations.trade_history(
        provider.snapshot(),
        symbol=symbol,
        side=side,
        strategy=strategy,
        page=page,
        page_size=page_size,
    )
    return success(data, meta=currency_meta(settings.usd_myr_rate))


@router.get(
    "/export.csv",
    summary="Export trade history as CSV",
    responses={200: {"content": {"text/csv": {}}, "description": "CSV file."}},
)
def export_trade_history_csv(
    symbol: str | None = Query(default=None, description="Filter by asset symbol."),
    side: str | None = Query(default=None, pattern=_SIDE_PATTERN, description="Filter by side: buy or sell."),
    strategy: str | None = Query(default=None, description="Filter by strategy name."),
    provider=Depends(get_provider),
) -> Response:
    body = trade_derivations.trades_csv(
        provider.snapshot(), symbol=symbol, side=side, strategy=strategy
    )
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="trade-history.csv"'},
    )


@router.get(
    "/{trade_id}",
    summary="Trade details",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse, "description": "Unknown trade id."}},
)
def get_trade_details(
    trade_id: str = Path(..., min_length=1, max_length=64),
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    data = trade_derivations.trade_details(provider.snapshot(), trade_id)
    if data is None:
        raise NotFoundError(f"Unknown trade id: {trade_id!r}", code="not_found")
    return success(data, meta=currency_meta(settings.usd_myr_rate))
