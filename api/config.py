"""Centralized, environment-driven API configuration.

All runtime knobs are read once from the process environment and cached. Nothing
here has side effects, so it is safe to import from anywhere (routes, tests,
tooling). Defaults are conservative and match the existing local-terminal
deployment: no cross-origin access and no configured JWT secret (authentication
is *ready* but inert until an identity provider is wired in).
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, Field

# Environment variable names are namespaced with ``NEXO_`` to avoid collisions.
ENV_PREFIX = "NEXO_"


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(f"{ENV_PREFIX}{name}")
    if value is None:
        return default
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list[str]:
    raw = _env(name)
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings(BaseModel):
    """Immutable snapshot of API configuration."""

    app_name: str = "NeXo API"
    app_version: str = "1.1.0"
    environment: str = "local"

    api_v1_prefix: str = "/api/v1"

    # CORS is an explicit allowlist. It is intentionally empty by default: the
    # frontend talks to the backend through a same-origin dev/proxy, so no
    # cross-origin access is granted unless origins are configured. A wildcard
    # ("*") is never used.
    cors_origins: list[str] = Field(default_factory=list)
    cors_allow_credentials: bool = False

    log_level: str = "INFO"
    log_json: bool = True
    # Per-request access logging is opt-in to keep test/CLI output clean.
    log_requests: bool = False

    # --- JWT-ready authentication (no tokens are issued by this service) ------
    # When ``jwt_secret`` is unset, protected routes reject every request with
    # 401 because no token can be verified. This is honest: the abstraction is
    # in place, but there is no login/persistence to authenticate against yet.
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_audience: str | None = None
    jwt_issuer: str | None = None

    @property
    def auth_configured(self) -> bool:
        return bool(self.jwt_secret)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings snapshot.

    Cached so configuration is read once per process. Tests that mutate the
    environment should call ``get_settings.cache_clear()``.
    """

    return Settings(
        app_name=_env("APP_NAME", "NeXo API") or "NeXo API",
        app_version=_env("APP_VERSION", "1.1.0") or "1.1.0",
        environment=_env("ENV", "local") or "local",
        api_v1_prefix=_env("API_V1_PREFIX", "/api/v1") or "/api/v1",
        cors_origins=_env_list("CORS_ORIGINS"),
        cors_allow_credentials=_env_bool("CORS_ALLOW_CREDENTIALS", False),
        log_level=_env("LOG_LEVEL", "INFO") or "INFO",
        log_json=_env_bool("LOG_JSON", True),
        log_requests=_env_bool("LOG_REQUESTS", False),
        jwt_secret=_env("JWT_SECRET") or None,
        jwt_algorithm=_env("JWT_ALGORITHM", "HS256") or "HS256",
        jwt_audience=_env("JWT_AUDIENCE") or None,
        jwt_issuer=_env("JWT_ISSUER") or None,
    )
