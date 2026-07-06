"""Pure paper-trading state: reconstruct a subscription's cash/position from its
persisted trades (weighted-average cost). Shared by the bot worker, the portfolio
view, and subscription settlement so there is one source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Trade, TradeSide


def _dec(value: object) -> Decimal:
    return Decimal(str(value))


@dataclass
class PaperState:
    cash: Decimal
    position: Decimal
    avg_cost: Decimal

    def value(self, price: Decimal) -> Decimal:
        return self.cash + self.position * price


def replay_state(session: Session, subscription_id: int, capital: object) -> PaperState:
    """Rebuild {cash, position, avg_cost} by replaying the subscription's trades."""

    cash = _dec(capital)
    position = Decimal("0")
    avg_cost = Decimal("0")
    trades = session.scalars(
        select(Trade).where(Trade.subscription_id == subscription_id).order_by(Trade.id)
    ).all()
    for t in trades:
        qty = _dec(t.quantity)
        price = _dec(t.price)
        value = qty * price
        if t.side == TradeSide.BUY.value:
            total_cost = avg_cost * position + value
            position += qty
            avg_cost = total_cost / position if position > 0 else Decimal("0")
            cash -= value
        else:  # SELL
            cash += value
            position -= qty
            if position <= 0:
                position = Decimal("0")
                avg_cost = Decimal("0")
    return PaperState(cash=cash, position=position, avg_cost=avg_cost)
