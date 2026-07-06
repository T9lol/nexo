"""Subscription lifecycle: bind user + bot + capital, with wallet reservation.

Subscribing reserves capital from the wallet (freezes it and records a FREEZE
transaction); cancelling releases it (UNFREEZE). Status transitions:
active <-> paused, and active/paused -> cancelled. No trading logic here — the
bot worker (Phase 5) executes against active subscriptions.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from api.errors import BadRequestError, ConflictError, NotFoundError
from api.v2 import wallet_service
from db.models import (
    Bot,
    Subscription,
    SubscriptionStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
)


def _ledger(user_id: int, wallet_id: int, tx_type: str, amount: Decimal, sub_id: int) -> Transaction:
    return Transaction(
        wallet_id=wallet_id,
        user_id=user_id,
        type=tx_type,
        amount=amount,
        status=TransactionStatus.COMPLETED.value,
        reference=f"subscription:{sub_id}",
    )


def create_subscription(db: Session, user_id: int, bot_id: int, capital: Decimal) -> Subscription:
    if capital <= 0:
        raise BadRequestError("Capital must be positive.", code="bad_request")
    bot = db.get(Bot, bot_id)
    if bot is None or not bot.is_active:
        raise NotFoundError("Bot not found.", code="not_found")
    wallet = wallet_service.get_or_create_wallet(db, user_id)
    if wallet_service.available(wallet) < capital:
        raise BadRequestError(
            "Insufficient available balance to allocate capital.",
            code="insufficient_funds",
        )
    wallet.frozen_balance = wallet.frozen_balance + capital
    sub = Subscription(
        user_id=user_id,
        bot_id=bot_id,
        capital=capital,
        status=SubscriptionStatus.ACTIVE.value,
    )
    db.add(sub)
    db.flush()
    db.add(_ledger(user_id, wallet.id, TransactionType.FREEZE.value, capital, sub.id))
    db.flush()
    return sub


def _owned(db: Session, user_id: int, sub_id: int) -> Subscription:
    sub = db.get(Subscription, sub_id)
    if sub is None or sub.user_id != user_id:
        raise NotFoundError("Subscription not found.", code="not_found")
    return sub


def pause(db: Session, user_id: int, sub_id: int) -> Subscription:
    sub = _owned(db, user_id, sub_id)
    if sub.status != SubscriptionStatus.ACTIVE.value:
        raise ConflictError(f"Cannot pause a {sub.status} subscription.", code="conflict")
    sub.status = SubscriptionStatus.PAUSED.value
    db.flush()
    return sub


def resume(db: Session, user_id: int, sub_id: int) -> Subscription:
    sub = _owned(db, user_id, sub_id)
    if sub.status != SubscriptionStatus.PAUSED.value:
        raise ConflictError(f"Cannot resume a {sub.status} subscription.", code="conflict")
    sub.status = SubscriptionStatus.ACTIVE.value
    db.flush()
    return sub


def cancel(db: Session, user_id: int, sub_id: int) -> Subscription:
    sub = _owned(db, user_id, sub_id)
    if sub.status == SubscriptionStatus.CANCELLED.value:
        raise ConflictError("Subscription is already cancelled.", code="conflict")

    # Liquidate at the current simulated price and settle PnL to the wallet.
    from api.v2 import bot_worker
    from api.v2.paper_trading import replay_state

    price = Decimal(str(bot_worker.current_price()))
    state = replay_state(db, sub.id, sub.capital)
    capital = Decimal(str(sub.capital))
    pnl = state.value(price) - capital

    wallet = wallet_service.get_or_create_wallet(db, user_id)
    wallet.frozen_balance = wallet.frozen_balance - capital  # release the reservation
    db.add(_ledger(user_id, wallet.id, TransactionType.UNFREEZE.value, capital, sub.id))
    if pnl != 0:
        wallet.balance = wallet.balance + pnl  # realized + unrealized PnL
        db.add(
            Transaction(
                wallet_id=wallet.id,
                user_id=user_id,
                type=TransactionType.TRADE.value,
                amount=pnl,
                status=TransactionStatus.COMPLETED.value,
                reference=f"subscription:{sub.id}:settle",
            )
        )
    sub.status = SubscriptionStatus.CANCELLED.value
    db.flush()
    return sub
