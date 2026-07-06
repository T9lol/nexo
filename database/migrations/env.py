"""Alembic environment for NeXo v2.

Resolves the database URL from ``DATABASE_URL`` (falling back to the app config's
SQLite default) and targets the ORM metadata in ``db.models``. ``render_as_batch``
is enabled so migrations also apply cleanly on SQLite.
"""

from __future__ import annotations

import os
import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# Make the backend package importable regardless of how alembic is invoked.
_BACKEND = pathlib.Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from api.config import get_settings  # noqa: E402
from db.base import Base  # noqa: E402
from db import models  # noqa: E402,F401 - register tables on Base.metadata

config = context.config
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:  # noqa: BLE001 - logging config is best-effort
        pass

target_metadata = Base.metadata


def _database_url() -> str:
    return os.getenv("DATABASE_URL") or get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_database_url(), poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
