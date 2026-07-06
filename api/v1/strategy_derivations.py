"""Pure derivations for the Strategy Center API views.

Projects the live evaluator/manager state (via the provider snapshot) into
strategy views. No trading logic is duplicated — only presentation.

The engine runs a single *active* strategy at a time, chosen either adaptively
(``auto``) or by manual override (``A``/``B``). The evaluator tracks a reward
``score``, a ``weight``, an ``adaptive`` selection metric, and an observation
count. It does **not** compute per-strategy PnL, win rate, or drawdown, so those
metrics are reported as ``None`` (with a ``metrics_tracked`` map) rather than
fabricated. ``total_trades`` is counted from the retained trade window.
"""

from __future__ import annotations

from typing import Any


def _round(value: Any, digits: int) -> float:
    return round(float(value), digits)


def _strategy_view(
    name: str, item: dict[str, Any], *, snapshot: dict[str, Any], active_name: Any
) -> dict[str, Any]:
    trades = snapshot.get("trades", [])
    total_trades = sum(1 for t in trades if str(t.get("strategy")) == name)
    score = _round(item.get("score", 0.0), 2)
    return {
        "name": name,
        "active": name == active_name,
        "score": score,
        "adaptive_score": _round(item.get("adaptive", 0.0), 2),
        "weight": _round(item.get("weight", 1.0), 4),
        "observations": int(item.get("updates", 0)),
        "metrics": {
            # Real, engine-tracked:
            "score": score,
            "total_trades": total_trades,  # over the retained trade window
            # Not tracked per-strategy by the engine (honest nulls):
            "pnl": None,
            "win_rate": None,
            "drawdown": None,
        },
        "metrics_tracked": {
            "score": True,
            "total_trades": True,
            "pnl": False,
            "win_rate": False,
            "drawdown": False,
        },
    }


def _match_name(strategies: dict[str, Any], name: str) -> str | None:
    target = name.strip().upper()
    return next((n for n in strategies if n.upper() == target), None)


def strategy_list(snapshot: dict[str, Any]) -> dict[str, Any]:
    strategies = snapshot.get("strategies", {})
    active = snapshot.get("selected_strategy")
    control = snapshot.get("control") or {}
    items = [
        _strategy_view(name, item, snapshot=snapshot, active_name=active)
        for name, item in strategies.items()
    ]
    items.sort(key=lambda s: s["name"])
    return {
        "strategies": items,
        "count": len(items),
        "active": active,
        "policy": control.get("strategy_policy"),
        "trading_enabled": control.get("trading_enabled"),
        "as_of": snapshot.get("updated_at"),
    }


def strategy_details(snapshot: dict[str, Any], name: str) -> dict[str, Any] | None:
    strategies = snapshot.get("strategies", {})
    match = _match_name(strategies, name)
    if match is None:
        return None
    control = snapshot.get("control") or {}
    view = _strategy_view(
        match, strategies[match], snapshot=snapshot, active_name=snapshot.get("selected_strategy")
    )
    view["is_manual_override"] = control.get("strategy_policy") == match
    view["policy"] = control.get("strategy_policy")
    view["trading_enabled"] = control.get("trading_enabled")
    view["as_of"] = snapshot.get("updated_at")
    return view


def strategy_comparison(snapshot: dict[str, Any]) -> dict[str, Any]:
    data = strategy_list(snapshot)
    items = data["strategies"]
    best = max(items, key=lambda s: s["adaptive_score"], default=None)
    data["best_by_adaptive_score"] = best["name"] if best else None
    return data
