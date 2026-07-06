"""Admin Console REST API (``/api/v1/admin``).

Every route requires the ``admin`` role (RBAC). Real capabilities: audit logs
(from the in-memory structured-log buffer), system health, feature flags, and
maintenance mode. Subsystems with no backend (users, KYC, deposits, withdrawals)
return honest empty/unavailable states and their decision actions return 503 —
no records are ever fabricated.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel

from api.config import Settings, get_settings
from api.errors import AppError
from api.logging import get_audit_records, get_logger
from api.schemas import ErrorResponse, SuccessResponse, success
from api.security import Principal, require_admin
from api.v1 import admin_service
from api.v1.dependencies import get_provider

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
logger = get_logger("admin")

_ADMIN_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Authentication required."},
    403: {"model": ErrorResponse, "description": "Administrator role required."},
}
_STATUS_PATTERN = r"^(?i:pending|approved|rejected)$"


class MaintenanceUpdate(BaseModel):
    enabled: bool
    message: str | None = None


class DecisionRequest(BaseModel):
    decision: str  # approved | rejected


def _unavailable_list(kind: str, status: str | None = None) -> dict[str, Any]:
    return {
        "items": [],
        "count": 0,
        "available": False,
        "status": status,
        "note": f"{kind} requires a backend not available in this build; no records are stored.",
    }


def _not_available(operation: str) -> None:
    raise AppError(
        f"{operation} is not available in this build; no backend is configured.",
        code="not_available",
        status_code=503,
    )


# --- User management (honest unavailable) -----------------------------------


@router.get("/users", summary="User management", response_model=SuccessResponse, responses=_ADMIN_RESPONSES)
def list_users(_admin: Principal = Depends(require_admin)) -> dict[str, Any]:
    return success(_unavailable_list("User management"))


# --- KYC review -------------------------------------------------------------


@router.get("/kyc", summary="KYC review", response_model=SuccessResponse, responses=_ADMIN_RESPONSES)
def list_kyc(
    status: str | None = Query(default=None, pattern=_STATUS_PATTERN, description="pending | approved | rejected"),
    _admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    return success(_unavailable_list("KYC review", status=status))


@router.post(
    "/kyc/{record_id}/decision",
    summary="Approve/reject a KYC record (unavailable)",
    responses={503: {"model": ErrorResponse}, **_ADMIN_RESPONSES},
)
def decide_kyc(
    _body: DecisionRequest,
    record_id: str = Path(..., min_length=1),
    _admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    _not_available("KYC decisioning")
    return {}  # pragma: no cover


# --- Deposit / withdrawal approval ------------------------------------------


@router.get("/deposits", summary="Deposit approval", response_model=SuccessResponse, responses=_ADMIN_RESPONSES)
def list_deposits(
    status: str | None = Query(default=None, pattern=_STATUS_PATTERN),
    _admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    return success(_unavailable_list("Deposit approval", status=status))


@router.post(
    "/deposits/{deposit_id}/decision",
    summary="Approve/reject a deposit (unavailable)",
    responses={503: {"model": ErrorResponse}, **_ADMIN_RESPONSES},
)
def decide_deposit(
    _body: DecisionRequest,
    deposit_id: str = Path(..., min_length=1),
    _admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    _not_available("Deposit decisioning")
    return {}  # pragma: no cover


@router.get("/withdrawals", summary="Withdrawal approval", response_model=SuccessResponse, responses=_ADMIN_RESPONSES)
def list_withdrawals(
    status: str | None = Query(default=None, pattern=_STATUS_PATTERN),
    _admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    return success(_unavailable_list("Withdrawal approval", status=status))


@router.post(
    "/withdrawals/{withdrawal_id}/decision",
    summary="Approve/reject a withdrawal (unavailable)",
    responses={503: {"model": ErrorResponse}, **_ADMIN_RESPONSES},
)
def decide_withdrawal(
    _body: DecisionRequest,
    withdrawal_id: str = Path(..., min_length=1),
    _admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    _not_available("Withdrawal decisioning")
    return {}  # pragma: no cover


# --- Audit logs (real, from the structured-log buffer) ----------------------


@router.get("/audit-logs", summary="Audit logs", response_model=SuccessResponse, responses=_ADMIN_RESPONSES)
def audit_logs(
    limit: int | None = Query(default=100, ge=1, le=500),
    event: str | None = Query(default=None, description="Filter by event name."),
    _admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    records = get_audit_records(limit=limit, event=event)
    return success(
        {
            "logs": records,
            "count": len(records),
            "durable": False,
            "note": "Recent API events captured in memory; not durable across restarts.",
        }
    )


# --- System health (real) ---------------------------------------------------


@router.get("/system-health", summary="System health", response_model=SuccessResponse, responses=_ADMIN_RESPONSES)
def system_health(
    provider=Depends(get_provider),
    settings: Settings = Depends(get_settings),
    _admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    return success(admin_service.system_health(provider.snapshot(), settings))


# --- Feature flags (real capabilities) --------------------------------------


@router.get("/feature-flags", summary="Feature flags", response_model=SuccessResponse, responses=_ADMIN_RESPONSES)
def feature_flags(
    settings: Settings = Depends(get_settings),
    _admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    return success(admin_service.feature_flags(settings))


# --- Maintenance mode (real toggle) -----------------------------------------


@router.get("/maintenance", summary="Maintenance mode", response_model=SuccessResponse, responses=_ADMIN_RESPONSES)
def get_maintenance(_admin: Principal = Depends(require_admin)) -> dict[str, Any]:
    return success(admin_service.get_maintenance())


@router.put("/maintenance", summary="Set maintenance mode", response_model=SuccessResponse, responses=_ADMIN_RESPONSES)
def set_maintenance(
    body: MaintenanceUpdate,
    admin: Principal = Depends(require_admin),
) -> dict[str, Any]:
    state = admin_service.set_maintenance(body.enabled, body.message, admin.subject)
    logger.info(
        "maintenance mode updated",
        extra={"event": "admin_maintenance", "path": "on" if body.enabled else "off"},
    )
    return success(state)
