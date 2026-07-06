"""Backtest Center REST API (``/api/v1/backtest``).

Execution is a JWT-ready mutation (``require_user``); it runs the engine's real
deterministic reference backtest and caches the result. The status/equity-curve/
drawdown/metrics/trades/report reads are public and serve the last run.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel

from api.config import Settings, get_settings
from api.currency import currency_meta
from api.errors import BadRequestError, NotFoundError
from api.logging import get_logger
from api.schemas import ErrorResponse, SuccessResponse, success
from api.security import Principal, require_user
from api.v1 import backtest_derivations, backtest_service

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])
logger = get_logger("backtest")

_ALLOWED_POLICIES = ("auto", "A", "B")


class BacktestRequest(BaseModel):
    policy: str = "auto"
    position_limit_enabled: bool = True


def _require_session() -> dict[str, Any]:
    session = backtest_service.latest()
    if session is None:
        raise NotFoundError(
            "No backtest has been run yet. POST /api/v1/backtest/run first.",
            code="not_found",
        )
    return session


def _summary(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": session["id"],
        "status": session["status"],
        "created_at": session["created_at"],
        "config": session["config"],
    }


@router.post(
    "/run",
    summary="Run the reference backtest",
    response_model=SuccessResponse,
    responses={401: {"model": ErrorResponse, "description": "Authentication required."}},
)
def run_backtest(
    request: BacktestRequest,
    _user: Principal = Depends(require_user),
) -> dict[str, Any]:
    if request.policy not in _ALLOWED_POLICIES:
        raise BadRequestError(
            f"Unknown policy: {request.policy!r}. Allowed: {list(_ALLOWED_POLICIES)}.",
            code="bad_request",
        )
    session = backtest_service.run(request.policy, request.position_limit_enabled)
    logger.info("backtest run", extra={"event": "backtest_run", "path": request.policy})
    return success(_summary(session))


@router.get("/status", summary="Backtest status", response_model=SuccessResponse)
def backtest_status() -> dict[str, Any]:
    session = backtest_service.latest()
    if session is None:
        return success({"status": "idle", "last_run": None})
    return success({"status": session["status"], "last_run": _summary(session)})


@router.get("/equity-curve", summary="Backtest equity curve", response_model=SuccessResponse)
def backtest_equity_curve(
    limit: int | None = Query(default=None, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    result = _require_session()["result"]
    return success(
        backtest_derivations.equity_curve(result, limit=limit),
        meta=currency_meta(settings.usd_myr_rate),
    )


@router.get("/drawdown", summary="Backtest drawdown series", response_model=SuccessResponse)
def backtest_drawdown(
    limit: int | None = Query(default=None, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    result = _require_session()["result"]
    return success(
        backtest_derivations.drawdown_series(result, limit=limit),
        meta=currency_meta(settings.usd_myr_rate),
    )


@router.get("/metrics", summary="Backtest performance metrics", response_model=SuccessResponse)
def backtest_metrics(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    result = _require_session()["result"]
    return success(
        backtest_derivations.performance_metrics(result, settings.usd_myr_rate),
        meta=currency_meta(settings.usd_myr_rate),
    )


@router.get("/trades", summary="Backtest trade list", response_model=SuccessResponse)
def backtest_trades(
    limit: int | None = Query(default=None, ge=1, le=1000),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    result = _require_session()["result"]
    return success(
        backtest_derivations.trade_list(result, limit=limit),
        meta=currency_meta(settings.usd_myr_rate),
    )


@router.get(
    "/report.csv",
    summary="Export the backtest report as CSV",
    responses={
        200: {"content": {"text/csv": {}}, "description": "CSV file."},
        404: {"model": ErrorResponse, "description": "No backtest run yet."},
    },
)
def backtest_report_csv() -> Response:
    result = _require_session()["result"]
    body = backtest_derivations.report_csv(result)
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="backtest-report.csv"'},
    )
