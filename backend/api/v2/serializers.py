"""JSON serializers for v2 domain records (Decimal -> float for the API)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from db.models import Transaction, Wallet


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
