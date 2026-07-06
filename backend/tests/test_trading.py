"""Phase 5 tests: bot worker execution, portfolio, trades, risk, settlement."""

import unittest

from api.v2 import bot_worker
from tests.support import ApiTestBase


class _FakeMarket:
    """Deterministic scripted price sequence (replaces the seeded feed)."""

    def __init__(self, prices):
        self.prices = list(prices)
        self.i = 0
        self.price = prices[0]

    def step(self) -> float:
        price = self.prices[min(self.i, len(self.prices) - 1)]
        self.i += 1
        self.price = price
        return price


class TradingTestBase(ApiTestBase):
    def setUp(self) -> None:
        super().setUp()
        bot_worker.reset_worker()
        self.worker = bot_worker.get_worker()

    def tearDown(self) -> None:
        bot_worker.reset_worker()
        super().tearDown()

    def _script(self, prices) -> None:
        self.worker._market = _FakeMarket(prices)

    def _subscribe_bot_a(self, capital=1000):
        access = self.token()
        self.client.post("/api/v2/wallet/deposit", json={"amount": capital}, headers=self.auth(access))
        bots = self.client.get("/api/v2/bots", headers=self.auth(access)).json()["data"]["bots"]
        bot_a = next(b for b in bots if b["key"] == "A")
        sub = self.client.post(
            "/api/v2/subscriptions", json={"bot_id": bot_a["id"], "capital": capital}, headers=self.auth(access)
        ).json()["data"]
        return access, sub["id"]

    def _tick(self):
        with self.Session() as session:
            return self.worker.tick_once(session)


class BotWorkerTests(TradingTestBase):
    def test_worker_executes_buy_then_sell(self) -> None:
        access, _sub = self._subscribe_bot_a(1000)
        self._script([99.0, 102.0])  # StrategyA: BUY <100, SELL >101
        self._tick()  # buy 1 @ 99
        self._tick()  # sell 1 @ 102

        trades = self.client.get("/api/v2/trades", headers=self.auth(access)).json()["data"]
        self.assertEqual(trades["pagination"]["total"], 2)
        sides = [t["side"] for t in trades["trades"]]
        self.assertIn("BUY", sides)
        self.assertIn("SELL", sides)
        # Realized PnL on the sell: (102 - 99) * 1 = 3
        sell = next(t for t in trades["trades"] if t["side"] == "SELL")
        self.assertEqual(sell["pnl"], 3.0)

    def test_worker_only_trades_active_subscriptions(self) -> None:
        access, sub_id = self._subscribe_bot_a(1000)
        self.client.post(f"/api/v2/subscriptions/{sub_id}/pause", headers=self.auth(access))
        self._script([99.0, 99.0])
        self._tick()
        self._tick()
        trades = self.client.get("/api/v2/trades", headers=self.auth(access)).json()["data"]
        self.assertEqual(trades["pagination"]["total"], 0)  # paused -> no trades

    def test_position_limit_blocks_buys(self) -> None:
        access, _sub = self._subscribe_bot_a(100000)
        # Tighten the risk limit to max 2 units.
        self.client.put(
            "/api/v2/risk",
            json={"position_limit_enabled": True, "max_position": 2},
            headers=self.auth(access),
        )
        self._script([99.0, 99.0, 99.0, 99.0])  # would buy every tick
        for _ in range(4):
            self._tick()
        portfolio = self.client.get("/api/v2/portfolio", headers=self.auth(access)).json()["data"]
        self.assertEqual(portfolio["positions"][0]["position"], 2.0)  # capped at 2


class PortfolioTests(TradingTestBase):
    def test_portfolio_reflects_open_position(self) -> None:
        access, _sub = self._subscribe_bot_a(1000)
        self._script([99.0])
        self._tick()  # buy 1 @ 99 -> cash 901, position 1
        data = self.client.get("/api/v2/portfolio", headers=self.auth(access)).json()["data"]
        pos = data["positions"][0]
        self.assertEqual(pos["cash"], 901.0)
        self.assertEqual(pos["position"], 1.0)
        # value = cash + position * current_price (99) = 901 + 99 = 1000
        self.assertEqual(pos["value"], 1000.0)
        self.assertEqual(data["price"], 99.0)


class SettlementTests(TradingTestBase):
    def test_cancel_settles_profit_to_wallet(self) -> None:
        access, sub_id = self._subscribe_bot_a(1000)
        self._script([99.0, 102.0])
        self._tick()  # buy @ 99
        self._tick()  # sell @ 102 -> realized +3, cash 1003, position 0
        # Cancel liquidates at current price (102) and settles.
        self.client.post(f"/api/v2/subscriptions/{sub_id}/cancel", headers=self.auth(access))
        wallet = self.client.get("/api/v2/wallet", headers=self.auth(access)).json()["data"]
        self.assertEqual(wallet["frozen_balance"], 0)
        # balance = original 1000 + PnL 3 = 1003; all available.
        self.assertEqual(wallet["available"], 1003.0)


class RiskConfigTests(ApiTestBase):
    def test_get_default_and_update(self) -> None:
        access = self.token()
        default = self.client.get("/api/v2/risk", headers=self.auth(access)).json()["data"]
        self.assertTrue(default["position_limit_enabled"])
        self.assertEqual(default["max_position"], 5.0)

        updated = self.client.put(
            "/api/v2/risk",
            json={"position_limit_enabled": False, "max_position": 10, "daily_loss_limit": 250},
            headers=self.auth(access),
        ).json()["data"]
        self.assertFalse(updated["position_limit_enabled"])
        self.assertEqual(updated["max_position"], 10.0)
        self.assertEqual(updated["daily_loss_limit"], 250.0)

    def test_risk_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/api/v2/risk").status_code, 401)

    def test_update_validates_max_position(self) -> None:
        access = self.token()
        r = self.client.put(
            "/api/v2/risk",
            json={"position_limit_enabled": True, "max_position": 0},
            headers=self.auth(access),
        )
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
