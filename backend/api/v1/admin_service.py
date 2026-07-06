"""Admin Console state and derivations.

Real, honest capabilities only:
* **Maintenance mode** — an in-memory toggle plus safe enforcement middleware.
* **Feature flags** — a read of genuine system capabilities (auth/CORS configured,
  which subsystems are available), not persisted user-defined toggles.
* **System health** — derived from the live snapshot.

Subsystems with no backend (user management, KYC, deposits, withdrawals) are
handled in the router as honest empty/unavailable states — never fabricated.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.config import Settings
from api.schemas import error_body

# --- Maintenance mode -------------------------------------------------------

_lock = threading.Lock()
_maintenance: dict[str, Any] = {
    "enabled": False,
    "message": None,
    "updated_at": None,
    "updated_by": None,
}


def get_maintenance() -> dict[str, Any]:
    with _lock:
        return dict(_maintenance)


def set_maintenance(
    enabled: bool, message: str | None, actor: str | None
) -> dict[str, Any]:
    with _lock:
        _maintenance["enabled"] = bool(enabled)
        _maintenance["message"] = message
        _maintenance["updated_at"] = datetime.now(timezone.utc).isoformat()
        _maintenance["updated_by"] = actor
        return dict(_maintenance)


def is_maintenance_enabled() -> bool:
    with _lock:
        return bool(_maintenance["enabled"])


def reset_maintenance() -> None:
    with _lock:
        _maintenance.update(enabled=False, message=None, updated_at=None, updated_by=None)


# Paths that stay reachable during maintenance so admins can recover, health
# checks work, and docs load.
_EXEMPT_PREFIXES = (
    "/ping",
    "/api/v1/admin",
    "/api/v1/health",
    "/api/health",
    "/api/v1/auth",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/static",
    "/favicon",
)


def install_maintenance_middleware(app: FastAPI) -> None:
    """Return 503 for non-exempt requests while maintenance mode is enabled."""

    @app.middleware("http")
    async def _maintenance_gate(request: Request, call_next):
        if is_maintenance_enabled():
            path = request.url.path
            if path != "/" and not any(path.startswith(p) for p in _EXEMPT_PREFIXES):
                state = get_maintenance()
                return JSONResponse(
                    status_code=503,
                    content=error_body(
                        "maintenance",
                        state.get("message") or "The platform is in maintenance mode.",
                    ),
                )
        return await call_next(request)


# --- Feature flags (real capabilities) --------------------------------------


def feature_flags(settings: Settings) -> dict[str, Any]:
    """Report genuine system capabilities as read-only flags.

    These reflect what the build actually supports; they are not persisted,
    user-defined toggles (maintenance mode has its own dedicated endpoint).
    """

    flags = [
        {"key": "authentication_configured", "enabled": settings.auth_configured},
        {"key": "cors_enabled", "enabled": bool(settings.cors_origins)},
        {"key": "request_logging", "enabled": settings.log_requests},
        {"key": "maintenance_mode", "enabled": is_maintenance_enabled()},
        # Subsystems with no backend in this build:
        {"key": "user_management", "enabled": False},
        {"key": "kyc_review", "enabled": False},
        {"key": "deposit_approval", "enabled": False},
        {"key": "withdrawal_approval", "enabled": False},
        {"key": "notification_delivery", "enabled": False},
        {"key": "api_key_management", "enabled": False},
    ]
    return {
        "flags": flags,
        "editable": False,
        "note": "Flags reflect real system capabilities and are read-only in this build.",
    }


# --- System health (from the live snapshot) ---------------------------------


def system_health(snapshot: dict[str, Any], settings: Settings) -> dict[str, Any]:
    control = snapshot.get("control") or {}
    return {
        "healthy": True,
        "status": snapshot.get("status", "unknown"),
        "mode": control.get("mode") or snapshot.get("mode"),
        "environment": control.get("environment") or settings.environment,
        "trading_enabled": control.get("trading_enabled"),
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "maintenance": get_maintenance(),
        "updated_at": snapshot.get("updated_at"),
    }
