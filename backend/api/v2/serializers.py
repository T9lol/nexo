"""JSON serializers for v2 domain records (Decimal -> float for the API)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from db.models import Bot, RiskConfig, Subscription, Trade, Transaction, Wallet


def _num(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def wallet_out(wallet: Wallet) -> dict[str, Any]:
    return {
        "balance": _num(wallet.balance),
        "frozen_balance": _num(wallet.frozen_balance),
        "available": _num(wallet.balance - wallet.frozen_balance),
        "currency": wallet.currency,
    }


def transaction_out(tx: Transaction) -> dict[str, Any]:
    return {
        "id": tx.id,
        "user_id": tx.user_id,
        "type": tx.type,
        "amount": _num(tx.amount),
        "status": tx.status,
        "reference": tx.reference,
        "created_at": _iso(tx.created_at),
    }


def bot_out(bot: Bot) -> dict[str, Any]:
    return {
        "id": bot.id,
        "key": bot.key,
        "name": bot.name,
        "description": bot.description,
        "strategy_ref": bot.strategy_ref,
        "is_active": bot.is_active,
    }


def subscription_out(sub: Subscription) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": sub.id,
        "bot_id": sub.bot_id,
        "capital": _num(sub.capital),
        "status": sub.status,
        "created_at": _iso(sub.created_at),
    }
    if sub.bot is not None:
        out["bot"] = {"key": sub.bot.key, "name": sub.bot.name}
    return out


def trade_out(t: Trade) -> dict[str, Any]:
    return {
        "id": t.id,
        "subscription_id": t.subscription_id,
        "bot_id": t.bot_id,
        "symbol": t.symbol,
        "side": t.side,
        "quantity": _num(t.quantity),
        "price": _num(t.price),
        "value": _num(t.value),
        "pnl": _num(t.pnl),
        "status": t.status,
        "executed_at": _iso(t.executed_at),
    }


def risk_config_out(rc: RiskConfig) -> dict[str, Any]:
    return {
        "position_limit_enabled": rc.position_limit_enabled,
        "max_position": _num(rc.max_position),
        "daily_loss_limit": _num(rc.daily_loss_limit),
    }
