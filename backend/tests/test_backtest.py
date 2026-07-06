import unittest
from contextlib import redirect_stdout
from io import StringIO

from backtest import BacktestEngine, PRICE_HISTORY
from core import EventBus
from execution import ExecutionEngine, RiskEngine
from observability import AlertSystem, Logger
from state import Analytics, Portfolio
from strategies import StrategyA


class BacktestTests(unittest.TestCase):
    def test_strategy_a_has_expected_deterministic_result(self) -> None:
        bus = EventBus()
        portfolio = Portfolio()
        analytics = Analytics(portfolio.cash)
        execution = ExecutionEngine(
            portfolio,
            RiskEngine(max_position=5),
            Logger(),
            AlertSystem(),
            analytics,
        )
        bus.subscribe("MARKET_PRICE", StrategyA(bus).on_price)
        bus.subscribe("SIGNAL", execution.on_signal)
        bus.subscribe("MARKET_PRICE", portfolio.on_market_price)
        backtest = BacktestEngine(bus)
        backtest.load_data(PRICE_HISTORY)

        with redirect_stdout(StringIO()):
            final_price = backtest.run()

        self.assertEqual(final_price, 102)
        self.assertEqual(portfolio.asset, 3)
        self.assertEqual(len(analytics.trades), 11)
        self.assertEqual(analytics.pnl(portfolio, final_price), 30)


if __name__ == "__main__":
    unittest.main()
