"""Wallet API (``/api/v2/wallet``): balance, ledger, deposit, withdraw + admin approval.

Paper funds; every balance change is a real, auditable transaction record.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.currency import currency_meta
from api.config import Settings, get_settings
from api.logging import get_logger
from api.schemas import SuccessResponse, success
from api.v2 import wallet_service
from api.v2.deps import get_current_user, get_db, require_admin_user
from api.v2.serializers import transaction_out, wallet_out
from db.models import Transaction, TransactionStatus, TransactionType, User

router = APIRouter(prefix="/api/v2/wallet", tags=["wallet-v2"])
logger = get_logger("wallet")

_MAX_AMOUNT = Decimal("1000000000000")


class AmountRequest(BaseModel):
    amount: Decimal = Field(gt=0, le=_MAX_AMOUNT)
    reference: str | None = Field(default=None, max_length=120)


def _meta(settings: Settings) -> dict[str, Any]:
    return currency_meta(settings.usd_myr_rate)


@router.get("", summary="Wallet balance", response_model=SuccessResponse)
def get_wallet(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    wallet = wallet_service.get_or_create_wallet(db, user.id)
    db.commit()
    return success(wallet_out(wallet), meta=_meta(settings))


@router.get("/transactions", summary="Transaction ledger", response_model=SuccessResponse)
def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    base = select(Transaction).where(Transaction.user_id == user.id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(Transaction.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return success(
        {
            "transactions": [transaction_out(t) for t in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if page_size else 0,
            },
        }
    )


@router.post("/deposit", summary="Deposit (paper funds)", response_model=SuccessResponse)
def deposit(
    body: AmountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    wallet, tx = wallet_service.deposit(db, user.id, body.amount, body.reference)
    db.commit()
    logger.info("wallet deposit", extra={"event": "wallet_deposit"})
    return success({"wallet": wallet_out(wallet), "transaction": transaction_out(tx)}, meta=_meta(settings))


@router.post("/withdraw", summary="Request a withdrawal", response_model=SuccessResponse)
def withdraw(
    body: AmountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    wallet, tx = wallet_service.request_withdrawal(db, user.id, body.amount, body.reference)
    db.commit()
    logger.info("wallet withdrawal requested", extra={"event": "wallet_withdraw_request"})
    return success({"wallet": wallet_out(wallet), "transaction": transaction_out(tx)}, meta=_meta(settings))


# --- Admin withdrawal approval ---------------------------------------------


@router.get(
    "/withdrawals/pending",
    summary="List pending withdrawals (admin)",
    response_model=SuccessResponse,
)
def list_pending_withdrawals(
    _admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = db.scalars(
        select(Transaction)
        .where(
            Transaction.type == TransactionType.WITHDRAWAL.value,
            Transaction.status == TransactionStatus.PENDING.value,
        )
        .order_by(Transaction.id)
    ).all()
    return success({"withdrawals": [transaction_out(t) for t in rows], "count": len(rows)})


@router.post(
    "/withdrawals/{tx_id}/approve",
    summary="Approve a withdrawal (admin)",
    response_model=SuccessResponse,
)
def approve_withdrawal(
    tx_id: int = Path(..., ge=1),
    _admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    wallet, tx = wallet_service.approve_withdrawal(db, tx_id)
    db.commit()
    logger.info("wallet withdrawal approved", extra={"event": "wallet_withdraw_approve"})
    return success({"wallet": wallet_out(wallet), "transaction": transaction_out(tx)}, meta=_meta(settings))


@router.post(
    "/withdrawals/{tx_id}/reject",
    summary="Reject a withdrawal (admin)",
    response_model=SuccessResponse,
)
def reject_withdrawal(
    tx_id: int = Path(..., ge=1),
    _admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    wallet, tx = wallet_service.reject_withdrawal(db, tx_id)
    db.commit()
    logger.info("wallet withdrawal rejected", extra={"event": "wallet_withdraw_reject"})
    return success({"wallet": wallet_out(wallet), "transaction": transaction_out(tx)}, meta=_meta(settings))
