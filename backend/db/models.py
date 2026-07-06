"""ORM models for the NeXo v2 SaaS domain.

Eight tables persist all user-facing state: users, bots, subscriptions, wallets,
transactions, trades, kyc, risk_configs. Enum-like fields are stored as short
strings (portable across SQLite/Postgres); the Python enums below are the
canonical value sets used by the service layer.

NeXo v2 is a **paper-trading / simulation** platform: wallet balances,
transactions, and trades are real, auditable records of *simulated* value.
"""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, func
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin

# Money is stored with 8 dp of precision (crypto-friendly) as Decimal.
_MONEY = Numeric(20, 8)


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRADE = "trade"
    FEE = "fee"
    FREEZE = "freeze"
    UNFREEZE = "unfreeze"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TradeSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class KycStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default=UserRole.USER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    wallet: Mapped["Wallet"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Bot(TimestampMixin, Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Reference to an engine strategy (e.g. "A", "B", "auto"); no new trading
    # logic — the bot delegates to the existing simulation engine.
    strategy_ref: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Wallet(TimestampMixin, Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True
    )
    balance: Mapped[Decimal] = mapped_column(_MONEY, default=Decimal("0"))
    frozen_balance: Mapped[Decimal] = mapped_column(_MONEY, default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(8), default="MYR")

    user: Mapped["User"] = relationship(back_populates="wallet")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="wallet", cascade="all, delete-orphan"
    )


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(16))
    amount: Mapped[Decimal] = mapped_column(_MONEY)
    status: Mapped[str] = mapped_column(
        String(16), default=TransactionStatus.COMPLETED.value
    )
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)

    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id"), index=True)
    capital: Mapped[Decimal] = mapped_column(_MONEY, default=Decimal("0"))
    status: Mapped[str] = mapped_column(
        String(16), default=SubscriptionStatus.ACTIVE.value
    )

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    bot: Mapped["Bot"] = relationship()
    trades: Mapped[list["Trade"]] = relationship(
        back_populates="subscription", cascade="all, delete-orphan"
    )


class Trade(TimestampMixin, Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    bot_id: Mapped[int | None] = mapped_column(ForeignKey("bots.id"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(20))
    side: Mapped[str] = mapped_column(String(4))
    quantity: Mapped[Decimal] = mapped_column(_MONEY)
    price: Mapped[Decimal] = mapped_column(_MONEY)
    value: Mapped[Decimal] = mapped_column(_MONEY)
    pnl: Mapped[Decimal] = mapped_column(_MONEY, default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(16), default="filled")
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    subscription: Mapped["Subscription"] = relationship(back_populates="trades")


class KycRecord(TimestampMixin, Base):
    __tablename__ = "kyc"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(16), default=KycStatus.PENDING.value)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    document_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


class RiskConfig(TimestampMixin, Base):
    __tablename__ = "risk_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True
    )
    position_limit_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_position: Mapped[Decimal] = mapped_column(_MONEY, default=Decimal("5"))
    daily_loss_limit: Mapped[Decimal | None] = mapped_column(_MONEY, nullable=True)
