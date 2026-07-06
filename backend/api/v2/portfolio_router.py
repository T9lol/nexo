"""Portfolio API (``/api/v2/portfolio``): the user's paper portfolio + PnL."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.config import Settings, get_settings
from api.currency import currency_meta
from api.schemas import SuccessResponse, success
from api.v2 import portfolio_service
from api.v2.deps import get_current_user, get_db
from db.models import User

router = APIRouter(prefix="/api/v2/portfolio", tags=["portfolio-v2"])


@router.get("", summary="Paper portfolio", response_model=SuccessResponse)
def get_portfolio(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    data = portfolio_service.portfolio(db, user.id)
    return success(data, meta=currency_meta(settings.usd_myr_rate))
