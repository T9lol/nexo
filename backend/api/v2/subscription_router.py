"""Subscriptions API (``/api/v2/subscriptions``): bind user + bot + capital."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.logging import get_logger
from api.schemas import SuccessResponse, success
from api.v2 import subscription_service
from api.v2.deps import get_current_user, get_db
from api.v2.serializers import subscription_out
from db.models import Subscription, User

router = APIRouter(prefix="/api/v2/subscriptions", tags=["subscriptions-v2"])
logger = get_logger("subscriptions")

_MAX_CAPITAL = Decimal("1000000000000")


class CreateSubscription(BaseModel):
    bot_id: int = Field(ge=1)
    capital: Decimal = Field(gt=0, le=_MAX_CAPITAL)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe to a bot",
    response_model=SuccessResponse,
)
def create_subscription(
    body: CreateSubscription,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    sub = subscription_service.create_subscription(db, user.id, body.bot_id, body.capital)
    db.commit()
    logger.info("subscription created", extra={"event": "subscription_create"})
    db.refresh(sub)
    return success(subscription_out(sub))


@router.get("", summary="List subscriptions", response_model=SuccessResponse)
def list_subscriptions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = db.scalars(
        select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.id.desc())
    ).all()
    return success({"subscriptions": [subscription_out(s) for s in rows], "count": len(rows)})


@router.get("/{sub_id}", summary="Subscription details", response_model=SuccessResponse)
def get_subscription(
    sub_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    sub = subscription_service._owned(db, user.id, sub_id)
    return success(subscription_out(sub))


def _apply(action, event: str, sub_id: int, user: User, db: Session) -> dict[str, Any]:
    sub = action(db, user.id, sub_id)
    db.commit()
    logger.info(f"subscription {event}", extra={"event": f"subscription_{event}"})
    db.refresh(sub)
    return success(subscription_out(sub))


@router.post("/{sub_id}/pause", summary="Pause a subscription", response_model=SuccessResponse)
def pause_subscription(
    sub_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return _apply(subscription_service.pause, "pause", sub_id, user, db)


@router.post("/{sub_id}/resume", summary="Resume a subscription", response_model=SuccessResponse)
def resume_subscription(
    sub_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return _apply(subscription_service.resume, "resume", sub_id, user, db)


@router.post(
    "/{sub_id}/cancel",
    summary="Cancel a subscription (releases capital)",
    response_model=SuccessResponse,
)
def cancel_subscription(
    sub_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return _apply(subscription_service.cancel, "cancel", sub_id, user, db)
