"""In-memory Settings state: exchange-rate management.

RM (MYR) is primary; USD is approximate. There is no live FX feed integrated, so
*automatic* mode resolves to the configured placeholder (which is also the
*fallback*). A *manual* override, when set and valid, takes precedence. State is
in-memory (not durable across restarts).
"""

from __future__ import annotations

import threading
from typing import Any

VALID_MODES = ("automatic", "manual")

_lock = threading.Lock()
_state: dict[str, Any] = {"mode": "automatic", "manual_rate": None}


def get_fx() -> dict[str, Any]:
    with _lock:
        return dict(_state)


def set_fx(mode: str, manual_rate: float | None) -> dict[str, Any]:
    """Store the FX mode/override. Invalid (<= 0) manual rates normalize to None."""

    normalized = manual_rate if (manual_rate is not None and manual_rate > 0) else None
    with _lock:
        _state["mode"] = mode
        _state["manual_rate"] = normalized
        return dict(_state)


def reset() -> None:
    with _lock:
        _state["mode"] = "automatic"
        _state["manual_rate"] = None


def resolve_rate(automatic_rate: float) -> dict[str, Any]:
    """Resolve the effective USD<->MYR rate given the configured automatic rate.

    manual (valid) -> the override; otherwise automatic, which falls back to the
    placeholder because no live feed is available.
    """

    state = get_fx()
    if state["mode"] == "manual" and state["manual_rate"] and state["manual_rate"] > 0:
        return {
            "rate": state["manual_rate"],
            "source": "manual",
            "mode": "manual",
            "live_feed_available": False,
        }
    return {
        "rate": automatic_rate,
        "source": "fallback",  # no live feed -> placeholder/fallback
        "mode": "automatic",
        "live_feed_available": False,
    }
