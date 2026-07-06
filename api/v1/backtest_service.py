"""Backtest execution session store.

Runs the engine's real, deterministic reference backtest and caches the most
recent result in memory so the status/equity-curve/drawdown/metrics/trades/report
endpoints can serve it. This stores only the *result* of the engine computation —
no trading logic lives here, and the isolated backtest never touches live state.
"""

from __future__ import annotations

import threading
import uuid
from typing import Any

_lock = threading.Lock()
_last: dict[str, Any] | None = None


def run(policy: str, position_limit_enabled: bool) -> dict[str, Any]:
    """Execute the reference backtest and store it as the latest session."""

    # Lazy import avoids a module-load cycle (ui.dashboard -> routers -> here).
    from ui.providers import run_reference_backtest, utc_time

    result = run_reference_backtest(
        policy=policy, position_limit_enabled=position_limit_enabled
    )
    equity_curve = result.get("equity_curve", [])
    session = {
        "id": uuid.uuid4().hex[:12],
        "status": "completed",
        "created_at": utc_time(),
        "config": {
            "policy": policy,
            "position_limit_enabled": position_limit_enabled,
            # Fixed by the reference engine; surfaced so clients know the basis.
            "initial_capital": equity_curve[0]["value"] if equity_curve else None,
            "symbol": result.get("market", {}).get("symbol"),
            "data_points": len(equity_curve),
            "note": (
                "Reference backtest over a fixed price history. Initial capital, "
                "symbol, and date range are fixed by the engine and not configurable."
            ),
        },
        "result": result,
    }
    with _lock:
        global _last
        _last = session
    return session


def latest() -> dict[str, Any] | None:
    with _lock:
        return _last


def reset() -> None:
    """Clear the stored session (used by tests for isolation)."""

    with _lock:
        global _last
        _last = None
