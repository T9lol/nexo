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
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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

provider: DashboardProvider = build_provider()
# Set during lifespan startup so it binds to the active provider (respecting
# test-time monkeypatching of `provider`).
manager: ConnectionManager | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global manager
    provider.start()
    manager = ConnectionManager(provider)
    manager.start()
    try:
        yield
    finally:
        await manager.stop()
        provider.stop()


app = FastAPI(
    title="NeXo Dashboard API",
    version="1.1.0",
    description="Product UI over a pluggable NeXo state provider.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/state")
def get_state() -> dict[str, Any]:
    return provider.snapshot()


@app.get("/api/trades")
def get_trades() -> list[dict[str, Any]]:
    return provider.snapshot()["trades"]


@app.get("/api/health")
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


@app.get("/api/control")
def get_control() -> dict[str, Any]:
    return provider.get_control()


@app.post("/api/control/trading")
def set_trading(command: TradingCommand) -> dict[str, Any]:
    return provider.set_trading(command.enabled)


@app.post("/api/control/strategy")
def set_strategy(command: StrategyCommand) -> dict[str, Any]:
    try:
        return provider.set_strategy(command.policy)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/control/risk")
def set_risk(command: RiskCommand) -> dict[str, Any]:
    return provider.set_risk(command.position_limit_enabled)


@app.post("/api/control/mode")
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
