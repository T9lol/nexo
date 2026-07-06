"""Engine, session factory, and DB helpers.

The engine is built from ``settings.database_url`` (SQLite locally, PostgreSQL in
production). Creating the engine does not open a connection, so importing this
module has no side effects on a database.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from api.config import get_settings
from db.base import Base
from db import models  # noqa: F401 - registers all tables on Base.metadata


def _make_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)


_engine: Engine = _make_engine(get_settings().database_url)
SessionLocal = sessionmaker(
    bind=_engine, autoflush=False, expire_on_commit=False, class_=Session
)


def get_engine() -> Engine:
    return _engine


def configure(url: str) -> None:
    """Rebind the engine/session to a new URL (used by tests)."""

    global _engine
    _engine = _make_engine(url)
    SessionLocal.configure(bind=_engine)


def init_db() -> None:
    """Create all tables (dev/test convenience; production uses Alembic)."""

    Base.metadata.create_all(_engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a scoped session."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_db() -> dict[str, object]:
    """Lightweight connectivity probe for health checks."""

    settings = get_settings()
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        connected = True
    except Exception:  # noqa: BLE001 - report unreachable rather than raising
        connected = False
    return {"connected": connected, "backend": settings.database_backend}
