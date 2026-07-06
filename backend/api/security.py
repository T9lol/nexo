"""JWT-ready authentication and User/Admin authorization abstractions.

This module provides the *structure* for authenticated, role-aware routes
without inventing any users, credentials, tokens, or persistence:

* :class:`Role` / :class:`Principal` — the identity model.
* :data:`bearer_scheme` — an OpenAPI-documented bearer scheme (non-erroring).
* :func:`decode_access_token` — verifies a JWT with the configured secret.
* :func:`get_current_principal` / :func:`require_user` / :func:`require_admin`
  — FastAPI dependencies for optional auth, user-level, and admin-level gates.

Because no ``NEXO_JWT_SECRET`` is configured by default, protected routes reject
every request with 401. That is intentional and honest: the platform is ready to
enforce authentication the instant an identity provider issues tokens, but this
service neither mints nor stores them.
"""

from __future__ import annotations

from enum import Enum

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from api.config import Settings, get_settings
from api.errors import ForbiddenError, UnauthorizedError

_WWW_AUTH = {"WWW-Authenticate": "Bearer"}


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"


class Principal(BaseModel):
    """An authenticated caller derived from a verified token."""

    subject: str
    roles: list[Role] = []

    def has_role(self, role: Role) -> bool:
        return role in self.roles


# ``auto_error=False`` so missing credentials yield ``None`` (handled by our
# dependencies) instead of FastAPI raising its own 403 with a non-standard shape.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="JWT bearer token issued by a configured identity provider.",
)


def decode_access_token(token: str, settings: Settings) -> Principal:
    """Verify a JWT and return the :class:`Principal` it represents.

    Raises :class:`UnauthorizedError` when auth is not configured or the token
    is missing/invalid/expired. No tokens are ever issued here.
    """

    if not settings.auth_configured:
        raise UnauthorizedError(
            "Authentication is not configured.",
            code="auth_not_configured",
            headers=_WWW_AUTH,
        )

    import jwt  # PyJWT; imported lazily so the module loads without it.

    options = {"verify_aud": settings.jwt_audience is not None}
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options=options,
        )
    except Exception as error:  # noqa: BLE001 - any decode failure => 401
        raise UnauthorizedError(
            "Invalid or expired token.",
            code="invalid_token",
            headers=_WWW_AUTH,
        ) from error

    subject = str(payload.get("sub") or "").strip()
    if not subject:
        raise UnauthorizedError(
            "Token is missing a subject claim.",
            code="invalid_token",
            headers=_WWW_AUTH,
        )

    raw_roles = payload.get("roles") or []
    roles: list[Role] = []
    if isinstance(raw_roles, (list, tuple)):
        for value in raw_roles:
            try:
                roles.append(Role(value))
            except ValueError:
                # Unknown roles are ignored rather than failing the request.
                continue
    return Principal(subject=subject, roles=roles)


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Principal | None:
    """Optional authentication: returns ``None`` for anonymous callers."""

    if credentials is None:
        return None
    return decode_access_token(credentials.credentials, settings)


async def require_user(
    principal: Principal | None = Depends(get_current_principal),
) -> Principal:
    """User-level gate. Rejects anonymous callers with 401."""

    if principal is None:
        raise UnauthorizedError(
            "Authentication required.",
            code="unauthorized",
            headers=_WWW_AUTH,
        )
    return principal


async def require_admin(
    principal: Principal = Depends(require_user),
) -> Principal:
    """Admin-level gate. Requires the ``admin`` role."""

    if not principal.has_role(Role.ADMIN):
        raise ForbiddenError(
            "Administrator role required.",
            code="forbidden",
        )
    return principal
