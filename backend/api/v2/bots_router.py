"""Bots API (``/api/v2/bots``): browse the subscribable engine strategies."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.errors import NotFoundError
from api.schemas import SuccessResponse, success
from api.v2.deps import get_current_user, get_db
from api.v2.serializers import bot_out
from db.models import Bot, User

router = APIRouter(prefix="/api/v2/bots", tags=["bots-v2"])


@router.get("", summary="List bots", response_model=SuccessResponse)
def list_bots(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = db.scalars(select(Bot).where(Bot.is_active).order_by(Bot.id)).all()
    return success({"bots": [bot_out(b) for b in rows], "count": len(rows)})


@router.get("/{bot_id}", summary="Bot details", response_model=SuccessResponse)
def get_bot(
    bot_id: int = Path(..., ge=1),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    bot = db.get(Bot, bot_id)
    if bot is None:
        raise NotFoundError("Bot not found.", code="not_found")
    return success(bot_out(bot))
