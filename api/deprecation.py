"""Legacy-route deprecation / migration structure.

Legacy (unversioned) ``/api/*`` routes are preserved unchanged for the frontend
proxy, but are now advertised as deprecated in favour of their ``/api/v1``
successors. This module supplies:

* :data:`LEGACY_ROUTE_MAP` — the machine-readable migration map.
* :func:`install_deprecation_middleware` — adds standards-based ``Deprecation``
  and ``Link`` (``rel="successor-version"``) response headers to legacy routes.

Only response *headers* are added; response bodies and status codes are
untouched, so no existing client behaviour changes.
"""

from __future__ import annotations

from fastapi import FastAPI, Request

# Legacy path -> versioned successor. Used for the Link header and docs.
LEGACY_ROUTE_MAP: dict[str, str] = {
    "/api/state": "/api/v1/state",
    "/api/trades": "/api/v1/trades",
    "/api/health": "/api/v1/health",
    "/api/control": "/api/v1/control",
    "/api/control/trading": "/api/v1/control/trading",
    "/api/control/strategy": "/api/v1/control/strategy",
    "/api/control/risk": "/api/v1/control/risk",
    "/api/control/mode": "/api/v1/control/mode",
}


def successor_for(path: str) -> str | None:
    return LEGACY_ROUTE_MAP.get(path)


def _is_legacy_api_path(path: str) -> bool:
    return path.startswith("/api/") and not path.startswith("/api/v1")


def install_deprecation_middleware(app: FastAPI) -> None:
    """Tag legacy ``/api/*`` responses with deprecation headers."""

    @app.middleware("http")
    async def _add_deprecation_headers(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if _is_legacy_api_path(path):
            response.headers["Deprecation"] = "true"
            successor = successor_for(path)
            if successor:
                response.headers["Link"] = (
                    f'<{successor}>; rel="successor-version"'
                )
        return response
