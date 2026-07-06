"""Trades API (``/api/v2/trades``): the user's persisted paper trades."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.errors import NotFoundError
from api.schemas import SuccessResponse, success
from api.v2.deps import get_current_user, get_db
from api.v2.serializers import trade_out
from db.models import Trade, User

router = APIRouter(prefix="/api/v2/trades", tags=["trades-v2"])

_SIDE_PATTERN = r"^(?i:buy|sell)$"


@router.get("", summary="List trades (filter + paginate)", response_model=SuccessResponse)
def list_trades(
    subscription_id: int | None = Query(default=None, ge=1),
    side: str | None = Query(default=None, pattern=_SIDE_PATTERN),
    symbol: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(Trade).where(Trade.user_id == user.id)
    if subscription_id is not None:
        stmt = stmt.where(Trade.subscription_id == subscription_id)
    if side is not None:
        stmt = stmt.where(Trade.side == side.upper())
    if symbol is not None:
        stmt = stmt.where(Trade.symbol == symbol.upper())

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Trade.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return success(
        {
            "trades": [trade_out(t) for t in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if page_size else 0,
            },
        }
    )


@router.get("/{trade_id}", summary="Trade details", response_model=SuccessResponse)
def get_trade(
    trade_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    trade = db.get(Trade, trade_id)
    if trade is None or trade.user_id != user.id:
        raise NotFoundError("Trade not found.", code="not_found")
    return success(trade_out(trade))
