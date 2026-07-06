"""Settings REST API (``/api/v1/settings``).

Real where the backend supports it (currency + exchange-rate management, system
information); honest/unavailable where it does not (notification delivery, API
key issuance). RBAC: reads that make sense in a local terminal are public;
per-user surfaces require a user; the global exchange-rate override requires an
admin.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.config import Settings, get_settings
from api.currency import to_usd
from api.errors import AppError, BadRequestError
from api.logging import get_logger
from api.schemas import ErrorResponse, SuccessResponse, success
from api.security import Principal, get_current_principal, require_user
from api.security import require_admin
from api.v1 import settings_service
from api.v1.dependencies import get_provider

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])
logger = get_logger("settings")

THEME_OPTIONS = ["light", "dark", "system"]
LANGUAGE_OPTIONS = [{"code": "en", "label": "English"}]


class ExchangeRateUpdate(BaseModel):
    mode: str
    manual_rate: float | None = None


# --- Profile / preferences --------------------------------------------------


@router.get("/profile", summary="User profile", response_model=SuccessResponse)
def get_profile(
    principal: Principal | None = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Identity from the JWT when present; anonymous otherwise (no user store)."""

    return success(
        {
            "authenticated": principal is not None,
            "subject": principal.subject if principal else None,
            "roles": [r.value for r in principal.roles] if principal else [],
            "environment": settings.environment,
            "note": "No server-side user store; identity is derived from a JWT when configured.",
        }
    )


@router.get("/theme", summary="Theme options", response_model=SuccessResponse)
def get_theme() -> dict[str, Any]:
    return success(
        {
            "options": THEME_OPTIONS,
            "default": "system",
            "managed_by": "client",
            "note": "Theme is a client-side preference; it is not persisted server-side.",
        }
    )


@router.get("/language", summary="Language options", response_model=SuccessResponse)
def get_language() -> dict[str, Any]:
    return success(
        {
            "options": LANGUAGE_OPTIONS,
            "default": "en",
            "managed_by": "client",
            "note": "Only English is available; language is a client-side preference.",
        }
    )


# --- Currency & exchange rate ----------------------------------------------


@router.get("/currency", summary="Currency settings", response_model=SuccessResponse)
def get_currency(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    resolved = settings_service.resolve_rate(settings.usd_myr_rate)
    return success(
        {
            "primary": "MYR",
            "usd_myr_rate": resolved["rate"],
            "usd_is_approximate": True,
            "rate_source": resolved["source"],
            "example": {"myr": 100.0, "usd": to_usd(100.0, resolved["rate"])},
        }
    )


@router.get("/exchange-rate", summary="Exchange rate management", response_model=SuccessResponse)
def get_exchange_rate(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    fx = settings_service.get_fx()
    resolved = settings_service.resolve_rate(settings.usd_myr_rate)
    return success(
        {
            "mode": fx["mode"],
            "manual_rate": fx["manual_rate"],
            "automatic_rate": settings.usd_myr_rate,
            "fallback_rate": settings.usd_myr_rate,
            "effective_rate": resolved["rate"],
            "effective_source": resolved["source"],
            "live_feed_available": False,
            "note": "No live FX feed is integrated; automatic falls back to a placeholder rate.",
        }
    )


@router.put(
    "/exchange-rate",
    summary="Update exchange-rate settings (admin)",
    response_model=SuccessResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
def update_exchange_rate(
    body: ExchangeRateUpdate,
    settings: Settings = Depends(get_settings),
    admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    if body.mode not in settings_service.VALID_MODES:
        raise BadRequestError(
            f"Unknown mode: {body.mode!r}. Allowed: {list(settings_service.VALID_MODES)}.",
            code="bad_request",
        )
    if body.mode == "manual" and (body.manual_rate is None or body.manual_rate <= 0):
        raise BadRequestError(
            "Manual mode requires a positive manual_rate.", code="bad_request"
        )
    settings_service.set_fx(body.mode, body.manual_rate)
    logger.info("exchange rate updated", extra={"event": "settings_exchange_rate", "path": body.mode})
    return get_exchange_rate(settings)


# --- Notifications / API keys (honest unavailable) --------------------------


@router.get("/notifications", summary="Notification settings", response_model=SuccessResponse)
def get_notifications(_user: Principal = Depends(require_user)) -> dict[str, Any]:
    return success(
        {
            "delivery_available": False,
            "categories": [
                {"key": "trade_fills", "label": "Trade fills", "enabled": False},
                {"key": "risk_alerts", "label": "Risk alerts", "enabled": False},
                {"key": "system", "label": "System notifications", "enabled": False},
            ],
            "note": "Notification delivery is not available in this build; no channel is configured.",
        }
    )


@router.get("/api-keys", summary="API key management", response_model=SuccessResponse)
def list_api_keys(_user: Principal = Depends(require_user)) -> dict[str, Any]:
    return success(
        {
            "keys": [],
            "management_available": False,
            "note": "API key issuance requires a backend not available in this build; "
            "secrets are never generated, displayed, or stored.",
        }
    )


@router.post(
    "/api-keys",
    summary="Create API key (unavailable)",
    responses={503: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
def create_api_key(_user: Principal = Depends(require_user)) -> dict[str, Any]:
    raise AppError(
        "API key issuance is not available in this build; no secret is generated or stored.",
        code="not_available",
        status_code=503,
    )


# --- System information (real) ---------------------------------------------


@router.get("/system-info", summary="System information", response_model=SuccessResponse)
def get_system_info(
    provider=Depends(get_provider), settings: Settings = Depends(get_settings)
) -> dict[str, Any]:
    snapshot = provider.snapshot()
    control = snapshot.get("control") or {}
    return success(
        {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "api_version": "v1",
            "environment": control.get("environment") or settings.environment,
            "mode": control.get("mode") or snapshot.get("mode"),
            "status": snapshot.get("status"),
            "backend_healthy": True,
        }
    )
