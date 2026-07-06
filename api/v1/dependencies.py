"""Shared dependencies for versioned routes.

The provider is resolved lazily from :mod:`ui.dashboard` at request time. This
avoids a circular import (``ui.dashboard`` includes this router) and — crucially
— honours the module-level ``provider`` that tests monkeypatch, exactly like the
legacy routes do.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ui.providers import DashboardProvider


def get_provider() -> "DashboardProvider":
    """Return the active dashboard provider (same instance as legacy routes)."""

    import ui.dashboard as dashboard

    return dashboard.provider
