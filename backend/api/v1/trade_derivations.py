"""Pure derivations for the Trade History API views.

The provider snapshot's ``trades`` list (recorded by the engine's Analytics) is
the single source of truth. These functions filter, paginate, enrich (notional
value), look up, and CSV-serialize those trades — no trading logic is added.
"""

from __future__ import annotations

import csv
import io
from typing import Any

SIDES = ("BUY", "SELL")

# Stable column order for CSV export.
CSV_COLUMNS = ("id", "time", "strategy", "action", "symbol", "price", "amount", "value")


def _enrich(trade: dict[str, Any]) -> dict[str, Any]:
    """Add the MYR notional value (price * amount) without mutating the source."""

    price = float(trade.get("price", 0.0))
    amount = float(trade.get("amount", 0.0))
    return {**trade, "value": round(price * amount, 2)}


def filter_trades(
    trades: list[dict[str, Any]],
    *,
    symbol: str | None = None,
    side: str | None = None,
    strategy: str | None = None,
) -> list[dict[str, Any]]:
    result = trades
    if symbol:
        target = symbol.upper()
        result = [t for t in result if str(t.get("symbol", "")).upper() == target]
    if side:
        target = side.upper()
        result = [t for t in result if str(t.get("action", "")).upper() == target]
    if strategy:
        target = strategy.upper()
        result = [t for t in result if str(t.get("strategy", "")).upper() == target]
    return result


def trade_history(
    snapshot: dict[str, Any],
    *,
    symbol: str | None = None,
    side: str | None = None,
    strategy: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    filtered = filter_trades(
        snapshot.get("trades", []), symbol=symbol, side=side, strategy=strategy
    )
    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    start = (page - 1) * page_size
    page_items = [_enrich(t) for t in filtered[start : start + page_size]]
    return {
        "trades": page_items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
        "filters": {"symbol": symbol, "side": side, "strategy": strategy},
        "as_of": snapshot.get("updated_at"),
    }


def trade_details(snapshot: dict[str, Any], trade_id: str) -> dict[str, Any] | None:
    for trade in snapshot.get("trades", []):
        if str(trade.get("id")) == str(trade_id):
            return _enrich(trade)
    return None


def trades_csv(
    snapshot: dict[str, Any],
    *,
    symbol: str | None = None,
    side: str | None = None,
    strategy: str | None = None,
) -> str:
    filtered = filter_trades(
        snapshot.get("trades", []), symbol=symbol, side=side, strategy=strategy
    )
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for trade in filtered:
        writer.writerow(_enrich(trade))
    return buffer.getvalue()
