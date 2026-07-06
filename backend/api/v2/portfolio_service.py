"""Per-user portfolio aggregation from persisted paper trades."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.v2 import bot_worker
from api.v2.paper_trading import replay_state
from db.models import Bot, Subscription, SubscriptionStatus


def _f(value: Decimal) -> float:
    return float(round(value, 2))


def _subscription_view(session: Session, sub: Subscription, price: Decimal) -> dict[str, Any]:
    state = replay_state(session, sub.id, sub.capital)
    capital = Decimal(str(sub.capital))
    value = state.value(price)
    pnl = value - capital
    bot = session.get(Bot, sub.bot_id)
    return {
        "subscription_id": sub.id,
        "bot": bot.key if bot is not None else None,
        "status": sub.status,
        "capital": _f(capital),
        "cash": _f(state.cash),
        "position": _f(state.position),
        "value": _f(value),
        "pnl": _f(pnl),
        "pnl_percent": _f(pnl / capital * 100) if capital else 0.0,
    }


def portfolio(session: Session, user_id: int) -> dict[str, Any]:
    price = Decimal(str(bot_worker.current_price()))
    subs = session.scalars(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_(
                [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.PAUSED.value]
            ),
        )
    ).all()
    positions = [_subscription_view(session, s, price) for s in subs]
    total_capital = sum((Decimal(str(p["capital"])) for p in positions), Decimal("0"))
    total_value = sum((Decimal(str(p["value"])) for p in positions), Decimal("0"))
    total_pnl = total_value - total_capital
    return {
        "symbol": "BTC",
        "price": _f(price),
        "total_capital": _f(total_capital),
        "total_value": _f(total_value),
        "total_pnl": _f(total_pnl),
        "pnl_percent": _f(total_pnl / total_capital * 100) if total_capital else 0.0,
        "open_positions": len(positions),
        "positions": positions,
    }
