"""Pure derivations for Backtest Center views.

Input is a backtest *result* — the dict produced by the engine's
``run_reference_backtest`` (equity curve, trades, portfolio). These functions
derive the equity curve, drawdown series, performance metrics, trade list, and a
CSV report. No trading logic is re-implemented.

Metrics honesty: Total Return, Max Drawdown, and Total Trades are derived from
the real equity/trade series. CAGR, Sharpe Ratio, and Win Rate are reported as
``None`` — they need calendar duration, annualized returns, or per-trade realized
PnL respectively, none of which the fixed synthetic reference backtest provides.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from api.currency import money

CSV_COLUMNS = ("id", "time", "strategy", "action", "symbol", "price", "amount", "value")


def _enrich(trade: dict[str, Any]) -> dict[str, Any]:
    price = float(trade.get("price", 0.0))
    amount = float(trade.get("amount", 0.0))
    return {**trade, "value": round(price * amount, 2)}


def _values(result: dict[str, Any]) -> list[float]:
    return [float(pt.get("value", 0.0)) for pt in result.get("equity_curve", [])]


def equity_curve(result: dict[str, Any], *, limit: int | None = None) -> dict[str, Any]:
    curve = result.get("equity_curve", [])
    if limit is not None:
        curve = curve[-limit:]
    points = [
        {"time": pt.get("time"), "value": round(float(pt.get("value", 0.0)), 2)}
        for pt in curve
    ]
    return {"points": points, "count": len(points)}


def drawdown_series(result: dict[str, Any], *, limit: int | None = None) -> dict[str, Any]:
    curve = result.get("equity_curve", [])
    if limit is not None:
        curve = curve[-limit:]
    points: list[dict[str, Any]] = []
    peak: float | None = None
    for pt in curve:
        value = float(pt.get("value", 0.0))
        peak = value if peak is None else max(peak, value)
        dd_pct = round((value - peak) / peak * 100, 4) if peak else 0.0
        points.append(
            {
                "time": pt.get("time"),
                "value": round(value, 2),
                "drawdown_percent": dd_pct,
                "drawdown_value": round(value - peak, 2),
            }
        )
    return {"points": points, "count": len(points)}


def _max_drawdown(values: list[float]) -> tuple[float, float]:
    peak: float | None = None
    worst_pct = 0.0
    worst_value = 0.0
    for value in values:
        peak = value if peak is None else max(peak, value)
        if peak:
            dd = (value - peak) / peak * 100
            if dd < worst_pct:
                worst_pct = dd
                worst_value = value - peak
    return round(worst_pct, 4), round(worst_value, 2)


def _total_return(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    initial, final = values[0], values[-1]
    amount = final - initial
    percent = (amount / initial * 100) if initial else 0.0
    return round(amount, 2), round(percent, 4)


def performance_metrics(result: dict[str, Any], rate: float) -> dict[str, Any]:
    values = _values(result)
    trades = result.get("trades", [])
    total_amount, total_pct = _total_return(values)
    mdd_pct, mdd_value = _max_drawdown(values)
    initial = values[0] if values else 0.0
    final = values[-1] if values else 0.0

    return {
        # Real, derived from the equity/trade series:
        "total_return": {**money(total_amount, rate), "percent": total_pct},
        "max_drawdown": {"percent": mdd_pct, "value": money(mdd_value, rate)},
        "total_trades": len(trades),
        # Not derivable from the fixed synthetic replay (honest nulls):
        "cagr": None,
        "sharpe_ratio": None,
        "win_rate": None,
        "metrics_tracked": {
            "total_return": True,
            "max_drawdown": True,
            "total_trades": True,
            "cagr": False,
            "sharpe_ratio": False,
            "win_rate": False,
        },
        "notes": {
            "cagr": "Requires calendar duration; the reference backtest is not calendar-timed.",
            "sharpe_ratio": "Requires annualized returns; not applicable to the fixed-history replay.",
            "win_rate": "Requires per-trade realized PnL, which the engine does not track.",
        },
        "initial_equity": money(initial, rate),
        "final_equity": money(final, rate),
        "pnl": money(round(final - initial, 2), rate),
    }


def trade_list(result: dict[str, Any], *, limit: int | None = None) -> dict[str, Any]:
    trades = result.get("trades", [])
    if limit is not None:
        trades = trades[:limit]
    enriched = [_enrich(t) for t in trades]
    return {"trades": enriched, "count": len(enriched)}


def report_csv(result: dict[str, Any]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for trade in result.get("trades", []):
        writer.writerow(_enrich(trade))
    return buffer.getvalue()
