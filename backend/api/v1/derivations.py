"""Pure derivations for the Dashboard and Portfolio API views.

Every function here takes a provider *snapshot* (the canonical read model of the
live trading engine/state) plus the FX rate, and returns a JSON-serializable
view. They contain **no trading business logic** — only presentation-level
aggregation (currency conversion, allocation percentages, windowed PnL over the
real equity history, grouping/filtering). The snapshot is the single source of
truth; these functions never mutate it.

The engine tracks cash + a single traded asset + a valuation history. It does
*not* track per-lot cost basis, so per-asset ``average_cost`` / ``unrealized_pnl``
are reported as ``None`` rather than fabricated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.currency import money


def _round2(value: float) -> float:
    return round(float(value), 2)


def _percent(part: float, whole: float) -> float:
    """Share of ``whole`` as a percentage, guarding divide-by-zero."""

    if not whole:
        return 0.0
    return round(part / whole * 100.0, 2)


def _parse_time(raw: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _period_start(now: datetime, period: str) -> datetime:
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        return midnight.replace(day=1)
    return midnight  # "day"


def windowed_pnl(
    equity_curve: list[dict[str, Any]],
    period: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """PnL over the current UTC day/month, derived from the real equity series.

    Baseline is the last valuation strictly before the window opens (the prior
    "close"); if the whole history falls inside the window (e.g. a freshly
    started session), the earliest available point is used. ``baseline_at``
    reports which point anchored the calculation so the window is transparent.
    """

    points = [
        (t, float(pt["value"]))
        for pt in equity_curve
        if (t := _parse_time(pt.get("time"))) is not None and "value" in pt
    ]
    if not points:
        return {"amount": 0.0, "percent": 0.0, "baseline": 0.0, "baseline_at": None}

    now = now or datetime.now(timezone.utc)
    start = _period_start(now, period)
    current_time, current_value = points[-1]

    before = [p for p in points if p[0] < start]
    if before:
        baseline_time, baseline_value = before[-1]
    else:
        within = [p for p in points if p[0] >= start]
        baseline_time, baseline_value = within[0] if within else points[-1]

    amount = _round2(current_value - baseline_value)
    return {
        "amount": amount,
        "percent": _percent(amount, baseline_value),
        "baseline": _round2(baseline_value),
        "baseline_at": baseline_time.isoformat(),
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


def dashboard_summary(
    snapshot: dict[str, Any], rate: float, *, now: datetime | None = None
) -> dict[str, Any]:
    portfolio = snapshot.get("portfolio", {})
    control = snapshot.get("control", {})
    equity = float(portfolio.get("equity", 0.0))
    curve = snapshot.get("equity_curve", [])

    today = windowed_pnl(curve, "day", now=now)
    month = windowed_pnl(curve, "month", now=now)
    inception = float(portfolio.get("pnl", 0.0))

    return {
        "total_assets": money(equity, rate),
        "today_pnl": {**money(today["amount"], rate), "percent": today["percent"]},
        "monthly_pnl": {**money(month["amount"], rate), "percent": month["percent"]},
        "inception_pnl": money(inception, rate),
        "active_strategy": snapshot.get("selected_strategy"),
        "system_status": {
            "status": snapshot.get("status"),
            "mode": control.get("mode") or snapshot.get("mode"),
            "trading_enabled": control.get("trading_enabled"),
            "environment": control.get("environment"),
            "updated_at": snapshot.get("updated_at"),
        },
    }


def equity_curve(
    snapshot: dict[str, Any], *, limit: int | None = None
) -> dict[str, Any]:
    curve = snapshot.get("equity_curve", [])
    if limit is not None:
        curve = curve[-limit:]
    points = [
        {"time": pt.get("time"), "value": _round2(pt.get("value", 0.0))}
        for pt in curve
    ]
    return {"points": points, "count": len(points), "as_of": snapshot.get("updated_at")}


def recent_trades(
    snapshot: dict[str, Any], *, limit: int | None = None
) -> dict[str, Any]:
    trades = snapshot.get("trades", [])
    if limit is not None:
        trades = trades[:limit]
    return {"trades": trades, "count": len(trades), "as_of": snapshot.get("updated_at")}


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------


def portfolio_summary(snapshot: dict[str, Any], rate: float) -> dict[str, Any]:
    portfolio = snapshot.get("portfolio", {})
    market = snapshot.get("market", {})
    cash = float(portfolio.get("cash", 0.0))
    asset = float(portfolio.get("asset", 0.0))
    price = float(market.get("price", 0.0))
    equity = float(portfolio.get("equity", 0.0))
    invested = _round2(asset * price)
    pnl = float(portfolio.get("pnl", 0.0))

    return {
        "total_value": money(equity, rate),
        "cash": money(cash, rate),
        "invested": money(invested, rate),
        "inception_pnl": {**money(pnl, rate), "percent": _percent(pnl, equity - pnl)},
        "holdings_count": 1 if asset else 0,
        "as_of": snapshot.get("updated_at"),
    }


def _asset_position(
    snapshot: dict[str, Any], rate: float
) -> dict[str, Any] | None:
    """The single non-cash position, or ``None`` when flat."""

    portfolio = snapshot.get("portfolio", {})
    market = snapshot.get("market", {})
    asset = float(portfolio.get("asset", 0.0))
    if not asset:
        return None
    price = float(market.get("price", 0.0))
    equity = float(portfolio.get("equity", 0.0))
    market_value = _round2(asset * price)
    return {
        "symbol": market.get("symbol"),
        "quantity": asset,
        "price": money(price, rate),
        "market_value": money(market_value, rate),
        "allocation_percent": _percent(market_value, equity),
        # Not tracked by the engine (no per-lot cost basis is maintained).
        "average_cost": None,
        "unrealized_pnl": None,
    }


def holdings(snapshot: dict[str, Any], rate: float) -> dict[str, Any]:
    position = _asset_position(snapshot, rate)
    positions = [position] if position is not None else []
    return {
        "holdings": positions,
        "count": len(positions),
        "as_of": snapshot.get("updated_at"),
    }


def allocation(snapshot: dict[str, Any], rate: float) -> dict[str, Any]:
    portfolio = snapshot.get("portfolio", {})
    market = snapshot.get("market", {})
    cash = float(portfolio.get("cash", 0.0))
    asset = float(portfolio.get("asset", 0.0))
    price = float(market.get("price", 0.0))
    equity = float(portfolio.get("equity", 0.0))
    asset_value = _round2(asset * price)

    slices = [
        {
            "label": "Cash",
            "symbol": "CASH",
            "value": money(cash, rate),
            "percent": _percent(cash, equity),
        },
        {
            "label": market.get("symbol"),
            "symbol": market.get("symbol"),
            "value": money(asset_value, rate),
            "percent": _percent(asset_value, equity),
        },
    ]
    return {
        "total": money(equity, rate),
        "allocation": slices,
        "as_of": snapshot.get("updated_at"),
    }


def value_history(
    snapshot: dict[str, Any], *, limit: int | None = None
) -> dict[str, Any]:
    # Portfolio total value over time is the same real series as the equity
    # curve; framed here as portfolio value history.
    return equity_curve(snapshot, limit=limit)


def asset_details(
    snapshot: dict[str, Any], symbol: str, rate: float
) -> dict[str, Any] | None:
    """Details for one traded symbol, or ``None`` if it is not a known symbol."""

    market = snapshot.get("market", {})
    known_symbol = str(market.get("symbol", ""))
    requested = symbol.strip().upper()
    if not known_symbol or requested != known_symbol.upper():
        return None

    portfolio = snapshot.get("portfolio", {})
    asset = float(portfolio.get("asset", 0.0))
    price = float(market.get("price", 0.0))
    equity = float(portfolio.get("equity", 0.0))
    market_value = _round2(asset * price)
    trades = [
        trade
        for trade in snapshot.get("trades", [])
        if str(trade.get("symbol", "")).upper() == requested
    ]

    return {
        "symbol": known_symbol,
        "price": money(price, rate),
        "quantity": asset,
        "market_value": money(market_value, rate),
        "allocation_percent": _percent(market_value, equity),
        "average_cost": None,
        "unrealized_pnl": None,
        "recent_trades": trades,
        "as_of": snapshot.get("updated_at"),
    }
