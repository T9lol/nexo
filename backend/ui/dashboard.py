"""FastAPI dashboard served by a pluggable state provider.

By default the dashboard is driven by the real NeXo runtime
(:class:`~ui.providers.RuntimeDashboardProvider`). Set
``NEXO_DASHBOARD_PROVIDER=mock`` to fall back to the deterministic UI-1 demo.
The ``/api/state`` schema is identical across providers, so the frontend is
unchanged.
"""

import asyncio
import logging
import os
import threading
from contextlib import asynccontextmanager, suppress
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
from api.v2.wallet_router import router as api_v2_wallet_router
from api.v2.bots_router import router as api_v2_bots_router
from api.v2.subscription_router import router as api_v2_subscription_router
from api.v2.portfolio_router import router as api_v2_portfolio_router
from api.v2.trades_router import router as api_v2_trades_router
from api.v2.risk_router import router as api_v2_risk_v2_router

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


# Keep a basic root logger available for Uvicorn/Railway even when structured
# API logging is disabled or misconfigured.
logging.basicConfig(level=logging.INFO)

STATIC_DIR = Path(__file__).parent / "static"

settings = get_settings()
configure_logging(level=settings.log_level, json_format=settings.log_json)
logger = get_logger()

# Evaluator seeding performs a small CPU-bound backtest. Defer it for the web
# process so importing the ASGI app and binding Railway's port stay immediate.
provider: DashboardProvider = build_provider(seed_evaluator=False)
# Set during lifespan startup so it binds to the active provider (respecting
# test-time monkeypatching of `provider`).
manager: ConnectionManager | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global manager
    logger.info("server starting", extra={"event": "startup_begin"})

    # These calls only start local threads/tasks and return immediately. All
    # synchronous database I/O is deferred below so ASGI lifespan can complete
    # and /ping can answer even when the database is temporarily unavailable.
    provider.start()
    manager = ConnectionManager(provider)
    manager.start()

    from api.v2.bot_worker import get_worker

    bot_worker = get_worker()
    initialization_stopped = threading.Event()

    def initialize_database_services() -> None:
        # Dev convenience: production schema migrations run in Railway's
        # pre-deploy phase, while local SQLite creates its schema here.
        if settings.database_backend == "sqlite":
            from db import init_db

            init_db()

        from api.v2.bots_service import seed_bots
        from db import SessionLocal

        with SessionLocal() as seed_session:
            seed_bots(seed_session)
            seed_session.commit()

        if not initialization_stopped.is_set():
            bot_worker.start()
            logger.info(
                "database services started", extra={"event": "services_ready"}
            )

    async def initialize_in_background() -> None:
        try:
            await asyncio.to_thread(initialize_database_services)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - liveness must not depend on the DB
            logger.exception(
                "database initialization skipped",
                extra={"event": "database_initialization_failed"},
            )

    initialization_task = asyncio.create_task(
        initialize_in_background(), name="database-initialization"
    )
    logger.info("server started", extra={"event": "startup"})
    try:
        yield
    finally:
        initialization_stopped.set()
        initialization_task.cancel()
        with suppress(asyncio.CancelledError):
            await initialization_task
        await asyncio.to_thread(bot_worker.stop)
        await manager.stop()
        await asyncio.to_thread(provider.stop)
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
    {
        "name": "wallet-v2",
        "description": "v2 wallet: balance, ledger, deposit, withdraw + admin "
        "approval (paper funds).",
    },
    {"name": "bots-v2", "description": "v2 bots: browse subscribable engine strategies."},
    {
        "name": "subscriptions-v2",
        "description": "v2 subscriptions: bind user + bot + capital; "
        "active/paused/cancelled.",
    },
    {"name": "portfolio-v2", "description": "v2 portfolio: per-user paper positions + PnL."},
    {"name": "trades-v2", "description": "v2 trades: per-user paper trade history."},
    {"name": "risk-v2", "description": "v2 risk: per-user position limits."},
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
app.include_router(api_v2_wallet_router)
app.include_router(api_v2_bots_router)
app.include_router(api_v2_subscription_router)
app.include_router(api_v2_portfolio_router)
app.include_router(api_v2_trades_router)
app.include_router(api_v2_risk_v2_router)


@app.get("/ping", tags=["health"], summary="Railway liveness probe")
def ping() -> dict[str, str]:
    """Minimal liveness route with no database or provider dependency."""

    logger.info("ping called", extra={"event": "ping", "path": "/ping"})
    return {"status": "ok"}


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

    port = int(os.environ.get("PORT", 8080))
    logger.info(
        "launching uvicorn",
        extra={"event": "server_launch", "path": f"0.0.0.0:{port}"},
    )
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run()
