"""Wallet ledger operations (paper funds, real double-entry-style records).

Every balance change is accompanied by a ``Transaction`` row. Operations mutate
and ``flush`` within the caller's session but do **not** commit — the router
commits on success, so any raised error leaves the session to roll back cleanly.

Model:
* deposit  → balance += amount, transaction(completed)
* withdraw → freeze amount (frozen_balance += amount), transaction(pending)
* approve  → balance -= amount, unfreeze, transaction(approved)
* reject   → unfreeze, transaction(rejected); balance unchanged
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.errors import BadRequestError, ConflictError, NotFoundError
from db.models import (
    Transaction,
    TransactionStatus,
    TransactionType,
    Wallet,
)


def get_or_create_wallet(db: Session, user_id: int) -> Wallet:
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == user_id))
    if wallet is None:
        wallet = Wallet(
            user_id=user_id, balance=Decimal("0"), frozen_balance=Decimal("0")
        )
        db.add(wallet)
        db.flush()
    return wallet


def available(wallet: Wallet) -> Decimal:
    return wallet.balance - wallet.frozen_balance


def deposit(
    db: Session, user_id: int, amount: Decimal, reference: str | None = None
) -> tuple[Wallet, Transaction]:
    if amount <= 0:
        raise BadRequestError("Deposit amount must be positive.", code="bad_request")
    wallet = get_or_create_wallet(db, user_id)
    wallet.balance = wallet.balance + amount
    tx = Transaction(
        wallet_id=wallet.id,
        user_id=user_id,
        type=TransactionType.DEPOSIT.value,
        amount=amount,
        status=TransactionStatus.COMPLETED.value,
        reference=reference,
    )
    db.add(tx)
    db.flush()
    return wallet, tx


def request_withdrawal(
    db: Session, user_id: int, amount: Decimal, reference: str | None = None
) -> tuple[Wallet, Transaction]:
    if amount <= 0:
        raise BadRequestError("Withdrawal amount must be positive.", code="bad_request")
    wallet = get_or_create_wallet(db, user_id)
    if available(wallet) < amount:
        raise BadRequestError(
            "Insufficient available balance.", code="insufficient_funds"
        )
    wallet.frozen_balance = wallet.frozen_balance + amount
    tx = Transaction(
        wallet_id=wallet.id,
        user_id=user_id,
        type=TransactionType.WITHDRAWAL.value,
        amount=amount,
        status=TransactionStatus.PENDING.value,
        reference=reference,
    )
    db.add(tx)
    db.flush()
    return wallet, tx


def _pending_withdrawal(db: Session, tx_id: int) -> Transaction:
    tx = db.get(Transaction, tx_id)
    if tx is None or tx.type != TransactionType.WITHDRAWAL.value:
        raise NotFoundError("Withdrawal request not found.", code="not_found")
    if tx.status != TransactionStatus.PENDING.value:
        raise ConflictError("Withdrawal is not pending.", code="conflict")
    return tx


def approve_withdrawal(db: Session, tx_id: int) -> tuple[Wallet, Transaction]:
    tx = _pending_withdrawal(db, tx_id)
    wallet = db.get(Wallet, tx.wallet_id)
    wallet.balance = wallet.balance - tx.amount
    wallet.frozen_balance = wallet.frozen_balance - tx.amount
    tx.status = TransactionStatus.APPROVED.value
    db.flush()
    return wallet, tx


def reject_withdrawal(db: Session, tx_id: int) -> tuple[Wallet, Transaction]:
    tx = _pending_withdrawal(db, tx_id)
    wallet = db.get(Wallet, tx.wallet_id)
    wallet.frozen_balance = wallet.frozen_balance - tx.amount  # release the hold
    tx.status = TransactionStatus.REJECTED.value
    db.flush()
    return wallet, tx
