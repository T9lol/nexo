"""FastAPI dashboard served by a pluggable state provider.

By default the dashboard is driven by the real NeXo runtime
(:class:`~ui.providers.RuntimeDashboardProvider`). Set
``NEXO_DASHBOARD_PROVIDER=mock`` to fall back to the deterministic UI-1 demo.
The ``/api/state`` schema is identical across providers, so the frontend is
unchanged.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# API platform layer (Backend Sprint 1). Wired additively; legacy routes,
# WebSocket behaviour, CLI, and trading-engine behaviour are unchanged.
from api.config import get_settings
from api.deprecation import install_deprecation_middleware
from api.errors import install_exception_handlers
from api.logging import configure_logging, get_logger
from api.v1 import router as api_v1_router
from api.v1.dashboard_router import router as api_v1_dashboard_router
from api.v1.portfolio_router import router as api_v1_portfolio_router
from api.v1.strategy_router import router as api_v1_strategy_router
from api.v1.trade_router import router as api_v1_trade_router
from api.v1.backtest_router import router as api_v1_backtest_router
from api.v1.risk_router import router as api_v1_risk_router
from api.v1.settings_router import router as api_v1_settings_router
from api.v1.admin_router import router as api_v1_admin_router
from api.v1.admin_service import install_maintenance_middleware
from api.v2.auth_router import router as api_v2_auth_router
from api.v2.users_router import router as api_v2_users_router

# Re-exported for backwards compatibility with existing imports/tests.
from ui.providers import (  # noqa: F401
    DashboardProvider,
    DashboardStore,
    MockDashboardProvider,
    RuntimeDashboardProvider,
    build_provider,
    utc_time,
)
from ui.ws import ConnectionManager, stream


STATIC_DIR = Path(__file__).parent / "static"

settings = get_settings()
configure_logging(level=settings.log_level, json_format=settings.log_json)
logger = get_logger()

provider: DashboardProvider = build_provider()
# Set during lifespan startup so it binds to the active provider (respecting
# test-time monkeypatching of `provider`).
manager: ConnectionManager | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global manager
    # Dev convenience: create tables on SQLite so the app is runnable without a
    # migration step. Production (PostgreSQL) relies on Alembic migrations.
    if settings.database_backend == "sqlite":
        from db import init_db

        init_db()
    provider.start()
    manager = ConnectionManager(provider)
    manager.start()
    logger.info("dashboard started", extra={"event": "startup"})
    try:
        yield
    finally:
        await manager.stop()
        provider.stop()
        logger.info("dashboard stopped", extra={"event": "shutdown"})


OPENAPI_TAGS = [
    {"name": "health", "description": "Public liveness probes."},
    {"name": "state", "description": "Read-only portfolio/market state."},
    {"name": "trades", "description": "Recent trade activity."},
    {"name": "control", "description": "Runtime control commands."},
    {
        "name": "dashboard",
        "description": "Dashboard module: summary, equity curve, recent trades.",
    },
    {
        "name": "portfolio",
        "description": "Portfolio module: summary, holdings, allocation, value "
        "history, asset details.",
    },
    {
        "name": "strategies",
        "description": "Strategy Center: list, details, comparison, enable/disable.",
    },
    {
        "name": "trade-history",
        "description": "Trade History: filtering, pagination, details, CSV export.",
    },
    {
        "name": "backtest",
        "description": "Backtest Center: run, status, equity curve, drawdown, "
        "metrics, trades, report export.",
    },
    {
        "name": "risk",
        "description": "Risk Center: overview, exposure, configuration, alerts, "
        "emergency stop, save settings.",
    },
    {
        "name": "settings",
        "description": "Settings: profile, theme, language, currency, exchange "
        "rate, notifications, API keys, system info.",
    },
    {
        "name": "admin",
        "description": "Admin Console (RBAC admin): users, KYC, deposits, "
        "withdrawals, audit logs, system health, feature flags, maintenance.",
    },
    {
        "name": "auth",
        "description": "JWT-ready authentication introspection. NeXo does not "
        "issue tokens; routes are enforced once an identity provider is "
        "configured.",
    },
    {
        "name": "auth-v2",
        "description": "v2 auth: register, login, refresh-token rotation, logout.",
    },
    {"name": "users-v2", "description": "v2 users: self profile and admin listing."},
]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "NeXo backend API. Versioned routes live under `/api/v1` with "
        "standardized success/error envelopes and JWT-ready authorization. "
        "Unversioned `/api/*` routes are preserved for backwards compatibility "
        "and marked deprecated."
    ),
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- API platform wiring ---------------------------------------------------
# CORS is an explicit, config-driven allowlist (never a wildcard). It is empty
# by default because the frontend talks to the backend over a same-origin proxy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_maintenance_middleware(app)
install_deprecation_middleware(app)
install_exception_handlers(app)
app.include_router(api_v1_router)
app.include_router(api_v1_dashboard_router)
app.include_router(api_v1_portfolio_router)
app.include_router(api_v1_strategy_router)
app.include_router(api_v1_trade_router)
app.include_router(api_v1_backtest_router)
app.include_router(api_v1_risk_router)
app.include_router(api_v1_settings_router)
app.include_router(api_v1_admin_router)
# --- v2 SaaS API (per-user, DB-backed) ---
app.include_router(api_v2_auth_router)
app.include_router(api_v2_users_router)


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


# --- Legacy (unversioned) routes -------------------------------------------
# Preserved unchanged for the frontend proxy. Superseded by /api/v1 and marked
# deprecated in OpenAPI; responses also carry Deprecation/Link headers via
# api.deprecation middleware.


@app.get("/api/state", deprecated=True)
def get_state() -> dict[str, Any]:
    return provider.snapshot()


@app.get("/api/trades", deprecated=True)
def get_trades() -> list[dict[str, Any]]:
    return provider.snapshot()["trades"]


@app.get("/api/health", deprecated=True)
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws")
async def ws_state(websocket: WebSocket) -> None:
    """Canonical real-time state stream. Control stays on HTTP POST routes."""
    if manager is None:  # pragma: no cover - startup guard
        await websocket.close(code=1013)
        return
    await stream(websocket, manager)


# --- UI-4 control commands (explicit, validated, idempotent) ---------------


class TradingCommand(BaseModel):
    enabled: bool


class StrategyCommand(BaseModel):
    policy: str


class RiskCommand(BaseModel):
    position_limit_enabled: bool


class ModeCommand(BaseModel):
    mode: str


@app.get("/api/control", deprecated=True)
def get_control() -> dict[str, Any]:
    return provider.get_control()


@app.post("/api/control/trading", deprecated=True)
def set_trading(command: TradingCommand) -> dict[str, Any]:
    return provider.set_trading(command.enabled)


@app.post("/api/control/strategy", deprecated=True)
def set_strategy(command: StrategyCommand) -> dict[str, Any]:
    try:
        return provider.set_strategy(command.policy)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/control/risk", deprecated=True)
def set_risk(command: RiskCommand) -> dict[str, Any]:
    return provider.set_risk(command.position_limit_enabled)


@app.post("/api/control/mode", deprecated=True)
def set_mode(command: ModeCommand) -> dict[str, Any]:
    try:
        return provider.set_mode(command.mode)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


def run() -> None:
    """Launch the dashboard through the `nexo-dashboard` console command."""
    import uvicorn

    uvicorn.run("ui.dashboard:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
