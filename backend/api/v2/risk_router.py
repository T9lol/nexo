"""Per-user risk config API (``/api/v2/risk``)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.logging import get_logger
from api.schemas import SuccessResponse, success
from api.v2.deps import get_current_user, get_db
from api.v2.serializers import risk_config_out
from db.models import RiskConfig, User

router = APIRouter(prefix="/api/v2/risk", tags=["risk-v2"])
logger = get_logger("risk_v2")


class RiskUpdate(BaseModel):
    position_limit_enabled: bool
    max_position: Decimal = Field(gt=0, le=Decimal("1000000"))
    daily_loss_limit: Decimal | None = Field(default=None, ge=0)


def _get_or_create(db: Session, user_id: int) -> RiskConfig:
    rc = db.scalar(select(RiskConfig).where(RiskConfig.user_id == user_id))
    if rc is None:
        rc = RiskConfig(user_id=user_id)
        db.add(rc)
        db.flush()
    return rc


@router.get("", summary="Risk configuration", response_model=SuccessResponse)
def get_risk(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rc = _get_or_create(db, user.id)
    db.commit()
    return success(risk_config_out(rc))


@router.put("", summary="Update risk configuration", response_model=SuccessResponse)
def update_risk(
    body: RiskUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rc = _get_or_create(db, user.id)
    rc.position_limit_enabled = body.position_limit_enabled
    rc.max_position = body.max_position
    rc.daily_loss_limit = body.daily_loss_limit
    db.commit()
    logger.info("risk config updated", extra={"event": "risk_v2_update"})
    return success(risk_config_out(rc))
