import unittest

from execution import ExecutionEngine, RiskEngine
from observability import AlertSystem, Logger
from state import Analytics, Portfolio


class ExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.portfolio = Portfolio()
        self.analytics = Analytics(self.portfolio.cash)
        self.execution = ExecutionEngine(
            self.portfolio,
            RiskEngine(max_position=1),
            Logger(),
            AlertSystem(),
            self.analytics,
        )

    def test_successful_buy_updates_state_and_analytics(self) -> None:
        self.execution.on_signal(
            {
                "strategy": "test",
                "action": "BUY",
                "symbol": "BTC",
                "price": 100.0,
                "amount": 1.0,
            }
        )

        self.assertEqual(self.portfolio.cash, 9_900)
        self.assertEqual(self.portfolio.asset, 1)
        self.assertEqual(len(self.analytics.trades), 1)

    def test_position_limit_blocks_second_buy(self) -> None:
        signal = {
            "strategy": "test",
            "action": "BUY",
            "symbol": "BTC",
            "price": 100.0,
            "amount": 1.0,
        }
        self.execution.on_signal(signal)
        self.execution.on_signal(signal)

        self.assertEqual(self.portfolio.asset, 1)
        self.assertEqual(len(self.analytics.trades), 1)


if __name__ == "__main__":
    unittest.main()
