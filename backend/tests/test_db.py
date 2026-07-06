"""Phase 1 tests: ORM models, session helpers, and the DB health endpoint."""

import unittest
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import ui.dashboard as dash
from db.base import Base
from db.models import (
    Bot,
    SubscriptionStatus,
    Subscription,
    Trade,
    Transaction,
    TransactionType,
    User,
    UserRole,
    Wallet,
)


def _session() -> Session:
    """Isolated in-memory SQLite session (StaticPool so it persists across use)."""

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class DbModelTests(unittest.TestCase):
    def test_all_eight_tables_registered(self) -> None:
        names = set(Base.metadata.tables)
        self.assertTrue(
            {
                "users", "bots", "subscriptions", "wallets",
                "transactions", "trades", "kyc", "risk_configs",
            }
            <= names
        )

    def test_user_wallet_transaction_flow(self) -> None:
        s = _session()
        user = User(email="a@test.co", hashed_password="x", role=UserRole.USER.value)
        s.add(user)
        s.flush()
        wallet = Wallet(user_id=user.id, balance=Decimal("100"), frozen_balance=Decimal("0"))
        s.add(wallet)
        s.flush()
        s.add(Transaction(
            wallet_id=wallet.id, user_id=user.id,
            type=TransactionType.DEPOSIT.value, amount=Decimal("100"),
        ))
        s.commit()

        self.assertEqual(user.wallet.balance, Decimal("100"))
        self.assertEqual(len(user.wallet.transactions), 1)
        self.assertEqual(user.wallet.transactions[0].type, "deposit")
        self.assertIsNotNone(user.created_at)

    def test_email_is_unique(self) -> None:
        s = _session()
        s.add(User(email="dup@test.co", hashed_password="x"))
        s.commit()
        s.add(User(email="dup@test.co", hashed_password="y"))
        with self.assertRaises(IntegrityError):
            s.commit()

    def test_subscription_and_trade(self) -> None:
        s = _session()
        user = User(email="b@test.co", hashed_password="x")
        s.add(user)
        s.flush()
        bot = Bot(key="A", name="Strategy A", strategy_ref="A")
        s.add(bot)
        s.flush()
        sub = Subscription(
            user_id=user.id, bot_id=bot.id, capital=Decimal("500"),
            status=SubscriptionStatus.ACTIVE.value,
        )
        s.add(sub)
        s.flush()
        s.add(Trade(
            subscription_id=sub.id, user_id=user.id, bot_id=bot.id, symbol="BTC",
            side="BUY", quantity=Decimal("1"), price=Decimal("100"), value=Decimal("100"),
        ))
        s.commit()

        self.assertEqual(len(sub.trades), 1)
        self.assertEqual(sub.trades[0].symbol, "BTC")
        self.assertEqual(sub.bot.key, "A")


class DbHealthTests(unittest.TestCase):
    def test_check_db_connected(self) -> None:
        from db import check_db

        result = check_db()
        self.assertTrue(result["connected"])
        self.assertIn(result["backend"], ("sqlite", "postgresql"))

    def test_health_db_endpoint(self) -> None:
        client = TestClient(dash.app)  # no lifespan needed; health/db skips the provider
        response = client.get("/api/v1/health/db")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertTrue(data["connected"])
        self.assertIn(data["backend"], ("sqlite", "postgresql"))


if __name__ == "__main__":
    unittest.main()
