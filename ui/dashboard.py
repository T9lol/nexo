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

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Re-exported for backwards compatibility with existing imports/tests.
from ui.providers import (  # noqa: F401
    DashboardProvider,
    DashboardStore,
    MockDashboardProvider,
    RuntimeDashboardProvider,
    build_provider,
    utc_time,
)


STATIC_DIR = Path(__file__).parent / "static"

provider: DashboardProvider = build_provider()


@asynccontextmanager
async def lifespan(_: FastAPI):
    provider.start()
    try:
        yield
    finally:
        provider.stop()


app = FastAPI(
    title="NeXo Dashboard API",
    version="0.2.0",
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


def run() -> None:
    """Launch the dashboard through the `nexo-dashboard` console command."""
    import uvicorn

    uvicorn.run("ui.dashboard:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
