"""Users API (``/api/v2/users``): self profile and admin user listing."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.schemas import SuccessResponse, success
from api.v2.deps import get_current_user, get_db, require_admin_user
from api.v2.schemas import UserOut
from db.models import User

router = APIRouter(prefix="/api/v2/users", tags=["users-v2"])


@router.get("/me", summary="Current user profile", response_model=SuccessResponse)
def get_me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return success(UserOut.model_validate(user).model_dump())


@router.get("", summary="List users (admin)", response_model=SuccessResponse)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    total = db.scalar(select(func.count()).select_from(User)) or 0
    rows = db.scalars(
        select(User).order_by(User.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return success(
        {
            "users": [UserOut.model_validate(u).model_dump() for u in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size if page_size else 0,
            },
        }
    )
