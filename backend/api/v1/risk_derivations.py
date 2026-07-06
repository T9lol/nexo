"""Pure derivations for Risk Center views.

Projects the live snapshot plus the engine's configured ``max_position`` into
risk views. The engine's only configurable risk policy is the position limit
(``position_limit_enabled``); ``max_position`` is a fixed constant. Additional
limits (daily loss, drawdown, stop loss, take profit) are not implemented by the
engine and are reported as unsupported rather than fabricated.
"""

from __future__ import annotations

from typing import Any

from api.currency import money


def _percent(part: float, whole: float) -> float:
    if not whole:
        return 0.0
    return round(part / whole * 100.0, 2)


def _position_state(snapshot: dict[str, Any]) -> dict[str, float]:
    portfolio = snapshot.get("portfolio", {})
    market = snapshot.get("market", {})
    asset = float(portfolio.get("asset", 0.0))
    price = float(market.get("price", 0.0))
    return {
        "asset": asset,
        "price": price,
        "equity": float(portfolio.get("equity", 0.0)),
        "cash": float(portfolio.get("cash", 0.0)),
        "exposure_value": round(asset * price, 2),
    }


def risk_overview(
    snapshot: dict[str, Any], max_position: float, rate: float
) -> dict[str, Any]:
    control = snapshot.get("control") or {}
    state = _position_state(snapshot)
    limit_enabled = bool(control.get("position_limit_enabled"))
    return {
        "trading_enabled": control.get("trading_enabled"),
        "position_limit_enabled": limit_enabled,
        "max_position": max_position,
        "current_position": state["asset"],
        "position_utilization_percent": _percent(state["asset"], max_position),
        "exposure": {
            "value": money(state["exposure_value"], rate),
            "percent": _percent(state["exposure_value"], state["equity"]),
        },
        "limit_breached": limit_enabled and state["asset"] >= max_position,
        "environment": control.get("environment"),
        "as_of": snapshot.get("updated_at"),
    }


def current_exposure(
    snapshot: dict[str, Any], max_position: float, rate: float
) -> dict[str, Any]:
    market = snapshot.get("market", {})
    state = _position_state(snapshot)
    return {
        "symbol": market.get("symbol"),
        "position": state["asset"],
        "price": money(state["price"], rate),
        "exposure_value": money(state["exposure_value"], rate),
        "exposure_percent": _percent(state["exposure_value"], state["equity"]),
        "max_position": max_position,
        "position_utilization_percent": _percent(state["asset"], max_position),
        "as_of": snapshot.get("updated_at"),
    }


def portfolio_exposure(snapshot: dict[str, Any], rate: float) -> dict[str, Any]:
    market = snapshot.get("market", {})
    state = _position_state(snapshot)
    equity = state["equity"]
    return {
        "total": money(equity, rate),
        "exposures": [
            {
                "label": "Cash",
                "symbol": "CASH",
                "value": money(state["cash"], rate),
                "percent": _percent(state["cash"], equity),
            },
            {
                "label": market.get("symbol"),
                "symbol": market.get("symbol"),
                "value": money(state["exposure_value"], rate),
                "percent": _percent(state["exposure_value"], equity),
            },
        ],
        "as_of": snapshot.get("updated_at"),
    }


# Limits the engine does not implement. Reported as unsupported, never faked.
_UNSUPPORTED_LIMITS = ("daily_loss_limit", "max_drawdown_limit", "stop_loss", "take_profit")


def risk_configuration(snapshot: dict[str, Any], max_position: float) -> dict[str, Any]:
    control = snapshot.get("control") or {}
    return {
        "position_limit_enabled": bool(control.get("position_limit_enabled")),
        "max_position": max_position,  # read-only engine constant
        "editable": ["position_limit_enabled"],
        "read_only": ["max_position"],
        "unsupported": list(_UNSUPPORTED_LIMITS),
        "as_of": snapshot.get("updated_at"),
    }


def risk_alerts(snapshot: dict[str, Any], max_position: float) -> dict[str, Any]:
    """Current risk indicators derived from real state.

    The engine does not retain a persistent alert log, so ``history_available``
    is False and only currently-true conditions are reported (no fabrication).
    """

    control = snapshot.get("control") or {}
    state = _position_state(snapshot)
    limit_enabled = bool(control.get("position_limit_enabled"))
    alerts: list[dict[str, Any]] = []

    if limit_enabled and state["asset"] >= max_position:
        alerts.append(
            {
                "level": "warning",
                "code": "position_limit_reached",
                "message": f"Position is at the limit ({max_position:g}).",
            }
        )
    if control.get("trading_enabled") is False:
        alerts.append(
            {
                "level": "info",
                "code": "trading_paused",
                "message": "Trading is paused (emergency stop or manual pause).",
            }
        )
    if not limit_enabled:
        alerts.append(
            {
                "level": "info",
                "code": "position_limit_disabled",
                "message": "Position-limit policy is disabled.",
            }
        )

    return {
        "alerts": alerts,
        "count": len(alerts),
        "history_available": False,
        "as_of": snapshot.get("updated_at"),
    }
