"""Authentication API (``/api/v2/auth``): register, login, refresh, logout, me.

Access = stateless JWT; refresh = opaque, DB-stored (hashed), rotated on every
use and revocable on logout.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import Settings, get_settings
from api.errors import ConflictError, UnauthorizedError
from api.logging import get_logger
from api.schemas import SuccessResponse, success
from api.v2 import auth_service
from api.v2.deps import get_current_user, get_db
from api.v2.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    UserOut,
)
from db.models import RefreshToken, RiskConfig, User, UserRole, Wallet

router = APIRouter(prefix="/api/v2/auth", tags=["auth-v2"])
logger = get_logger("auth")

_WWW_AUTH = {"WWW-Authenticate": "Bearer"}


def _issue_tokens(db: Session, user: User, settings: Settings) -> dict[str, Any]:
    access, expires_in = auth_service.create_access_token(user.id, [user.role], settings)
    raw, token_hash, expires_at = auth_service.create_refresh_token(settings)
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at, revoked=False))
    db.commit()
    return {
        "access_token": access,
        "refresh_token": raw,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": UserOut.model_validate(user).model_dump(),
    }


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    response_model=SuccessResponse,
)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise ConflictError("Email is already registered.", code="conflict")
    user = User(
        email=email,
        hashed_password=auth_service.hash_password(body.password),
        role=UserRole.USER.value,
        is_active=True,
    )
    db.add(user)
    db.flush()
    # Provision the user's paper wallet and default risk config.
    db.add(Wallet(user_id=user.id))
    db.add(RiskConfig(user_id=user.id))
    db.commit()
    db.refresh(user)
    logger.info("user registered", extra={"event": "auth_register"})
    return success(UserOut.model_validate(user).model_dump())


@router.post("/login", summary="Log in", response_model=SuccessResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not auth_service.verify_password(body.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password.", code="invalid_credentials", headers=_WWW_AUTH)
    if not user.is_active:
        raise UnauthorizedError("Account is inactive.", code="inactive", headers=_WWW_AUTH)
    logger.info("user login", extra={"event": "auth_login"})
    return success(_issue_tokens(db, user, settings))


@router.post("/refresh", summary="Rotate tokens", response_model=SuccessResponse)
def refresh(
    body: RefreshRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == auth_service.hash_refresh(body.refresh_token))
    )
    now = datetime.now(timezone.utc)
    if record is None or record.revoked or auth_service.as_aware_utc(record.expires_at) <= now:
        raise UnauthorizedError("Invalid or expired refresh token.", code="invalid_token", headers=_WWW_AUTH)
    # Rotate: revoke the presented token, then issue a fresh pair.
    record.revoked = True
    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        db.commit()
        raise UnauthorizedError("User not found or inactive.", code="unauthorized", headers=_WWW_AUTH)
    return success(_issue_tokens(db, user, settings))


@router.post("/logout", summary="Revoke a refresh token", response_model=SuccessResponse)
def logout(body: LogoutRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == auth_service.hash_refresh(body.refresh_token))
    )
    if record is not None and not record.revoked:
        record.revoked = True
        db.commit()
    return success({"revoked": True})


@router.get("/me", summary="Current user", response_model=SuccessResponse)
def me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return success(UserOut.model_validate(user).model_dump())
