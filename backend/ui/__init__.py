"""Web dashboard for NeXo."""

from typing import Any

__all__ = ["app"]


def __getattr__(name: str) -> Any:
    """Load the ASGI app lazily so ``python -m ui.dashboard`` runs once."""

    if name == "app":
        from .dashboard import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
