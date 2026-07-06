"""Shared v2 dependencies: DB-backed current-user and admin RBAC."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from api.errors import ForbiddenError, UnauthorizedError
from api.security import Principal, Role, require_user
from db import get_db
from db.models import User

__all__ = ["get_db", "get_current_user", "require_admin_user"]


def get_current_user(
    principal: Principal = Depends(require_user),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated principal to a live DB user."""

    try:
        user_id = int(principal.subject)
    except (TypeError, ValueError):
        raise UnauthorizedError("Invalid token subject.", code="invalid_token")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive.", code="unauthorized")
    return user


def require_admin_user(user: User = Depends(get_current_user)) -> User:
    """Admin RBAC enforced against the database role (source of truth)."""

    if user.role != Role.ADMIN.value:
        raise ForbiddenError("Administrator role required.", code="forbidden")
    return user
