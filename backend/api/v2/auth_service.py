"""Auth primitives: password hashing, access-token minting, refresh tokens.

Access tokens are stateless JWTs (verified by the existing ``api.security``
layer). Refresh tokens are opaque random strings; only their SHA-256 hash is
stored server-side (see ``db.models.RefreshToken``) so they can be rotated and
revoked.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from api.config import Settings
from api.errors import AppError

# bcrypt hashes at most 72 bytes; truncate consistently to avoid backend errors.
_BCRYPT_MAX = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:_BCRYPT_MAX], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:_BCRYPT_MAX], hashed.encode("utf-8"))
    except ValueError:
        return False


def _require_secret(settings: Settings) -> None:
    if not settings.jwt_secret:
        raise AppError(
            "Authentication is not configured (JWT_SECRET missing).",
            code="auth_not_configured",
            status_code=503,
        )


def create_access_token(subject: int | str, roles: list[str], settings: Settings) -> tuple[str, int]:
    """Return ``(jwt, expires_in_seconds)`` for a short-lived access token."""

    _require_secret(settings)
    now = datetime.now(timezone.utc)
    ttl_seconds = settings.jwt_access_ttl_minutes * 60
    payload = {
        "sub": str(subject),
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, ttl_seconds


def hash_refresh(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_refresh_token(settings: Settings) -> tuple[str, str, datetime]:
    """Return ``(raw_token, token_hash, expires_at)``. Only the hash is stored."""

    raw = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_ttl_days)
    return raw, hash_refresh(raw), expires_at


def as_aware_utc(value: datetime) -> datetime:
    """Normalize a possibly-naive datetime (SQLite) to aware UTC (Postgres)."""

    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
