"""Bot catalog: the engine strategies exposed as subscribable bots.

Bots are thin references to existing engine strategies (``auto``/``A``/``B``) —
no new trading logic. Seeding is idempotent.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Bot

# key -> engine strategy reference. Mirrors the engine's STRATEGY_POLICIES.
BOT_SEED = [
    {
        "key": "auto",
        "name": "Adaptive (Auto)",
        "strategy_ref": "auto",
        "description": "Adaptive reward-weighted selection across engine strategies.",
    },
    {
        "key": "A",
        "name": "Strategy A",
        "strategy_ref": "A",
        "description": "NeXo engine strategy A.",
    },
    {
        "key": "B",
        "name": "Strategy B",
        "strategy_ref": "B",
        "description": "NeXo engine strategy B.",
    },
]


def seed_bots(db: Session) -> None:
    """Ensure the catalog bots exist. Idempotent; caller commits."""

    for spec in BOT_SEED:
        if db.scalar(select(Bot).where(Bot.key == spec["key"])) is None:
            db.add(Bot(is_active=True, **spec))
