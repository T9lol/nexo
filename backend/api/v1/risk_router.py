"""Risk Center REST API (``/api/v1/risk``).

Read routes (overview, exposure, portfolio exposure, config, alerts) are public.
Mutations — Emergency Stop and Save Risk Settings — are JWT-ready
(``require_user``) and delegate to the engine's real control surface
(``set_trading`` / ``set_risk``); no risk logic is re-implemented.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.config import Settings, get_settings
from api.currency import currency_meta
from api.logging import get_logger
from api.schemas import ErrorResponse, SuccessResponse, success
from api.security import Principal, require_user
from api.v1 import risk_derivations
from api.v1.dependencies import get_provider

# The engine's configured position limit (fixed constant). Imported from the
# providers module (a leaf import — no cycle).
from ui.providers import MAX_POSITION

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])
logger = get_logger("risk")

_AUTH = {401: {"model": ErrorResponse, "description": "Authentication required."}}


class RiskSettings(BaseModel):
    position_limit_enabled: bool


@router.get("/overview", summary="Risk overview", response_model=SuccessResponse)
def risk_overview(
    provider=Depends(get_provider), settings: Settings = Depends(get_settings)
) -> dict[str, Any]:
    rate = settings.usd_myr_rate
    return success(
        risk_derivations.risk_overview(provider.snapshot(), MAX_POSITION, rate),
        meta=currency_meta(rate),
    )


@router.get("/exposure", summary="Current exposure", response_model=SuccessResponse)
def current_exposure(
    provider=Depends(get_provider), settings: Settings = Depends(get_settings)
) -> dict[str, Any]:
    rate = settings.usd_myr_rate
    return success(
        risk_derivations.current_exposure(provider.snapshot(), MAX_POSITION, rate),
        meta=currency_meta(rate),
    )


@router.get(
    "/portfolio-exposure", summary="Portfolio exposure", response_model=SuccessResponse
)
def portfolio_exposure(
    provider=Depends(get_provider), settings: Settings = Depends(get_settings)
) -> dict[str, Any]:
    rate = settings.usd_myr_rate
    return success(
        risk_derivations.portfolio_exposure(provider.snapshot(), rate),
        meta=currency_meta(rate),
    )


@router.get("/config", summary="Risk configuration", response_model=SuccessResponse)
def get_risk_config(provider=Depends(get_provider)) -> dict[str, Any]:
    return success(
        risk_derivations.risk_configuration(provider.snapshot(), MAX_POSITION)
    )


@router.get("/alerts", summary="Risk alerts", response_model=SuccessResponse)
def risk_alerts(provider=Depends(get_provider)) -> dict[str, Any]:
    return success(risk_derivations.risk_alerts(provider.snapshot(), MAX_POSITION))


@router.post(
    "/emergency-stop",
    summary="Emergency stop (halt trading)",
    response_model=SuccessResponse,
    responses=_AUTH,
)
def emergency_stop(
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
    _user: Principal = Depends(require_user),
) -> dict[str, Any]:
    provider.set_trading(False)  # real engine control: pause all executions
    logger.info("emergency stop", extra={"event": "risk_emergency_stop"})
    rate = settings.usd_myr_rate
    return success(
        risk_derivations.risk_overview(provider.snapshot(), MAX_POSITION, rate),
        meta=currency_meta(rate),
    )


@router.put(
    "/config",
    summary="Save risk settings",
    response_model=SuccessResponse,
    responses=_AUTH,
)
def save_risk_config(
    settings_body: RiskSettings,
    provider=Depends(get_provider),
    _user: Principal = Depends(require_user),
) -> dict[str, Any]:
    # Only the position limit is a configurable engine policy; other limits are
    # unsupported and intentionally not accepted here.
    provider.set_risk(settings_body.position_limit_enabled)
    logger.info(
        "risk settings saved",
        extra={"event": "risk_config_save"},
    )
    return success(
        risk_derivations.risk_configuration(provider.snapshot(), MAX_POSITION)
    )
