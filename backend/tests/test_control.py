"""UI-4 control-contract tests: pause/resume, policy, risk, mode isolation."""

import threading
import time
import unittest

from execution import ExecutionEngine, RiskEngine
from observability import AlertSystem, Logger
from state import Analytics, Portfolio
from ui.providers import (
    MockDashboardProvider,
    RuntimeDashboardProvider,
    run_reference_backtest,
)


CONTROL_KEYS = {
    "trading_enabled",
    "strategy_policy",
    "effective_strategy",
    "manual_override",
    "position_limit_enabled",
    "mode",
    "environment",
    "allowed",
}


def runtime() -> RuntimeDashboardProvider:
    return RuntimeDashboardProvider(interval=0.01, seed=7)


def market_threads() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name == "runtime-market"]


class PauseResumeTests(unittest.TestCase):
    def test_pause_resume_is_idempotent(self) -> None:
        provider = runtime()
        first = provider.set_trading(False)
        second = provider.set_trading(False)
        self.assertFalse(first["trading_enabled"])
        self.assertEqual(first, second)
        self.assertTrue(provider.set_trading(True)["trading_enabled"])

    def test_no_fills_while_paused_but_market_keeps_ticking(self) -> None:
        provider = runtime()
        provider.set_trading(False)
        trades_before = len(provider.snapshot()["trades"])
        points_before = len(provider.snapshot()["equity_curve"])

        for _ in range(80):
            provider.tick_once()

        paused = provider.snapshot()
        self.assertEqual(len(paused["trades"]), trades_before)  # no new fills
        self.assertGreater(  # market/equity kept advancing
            len(paused["equity_curve"]), points_before
        )

        provider.set_trading(True)
        for _ in range(80):
            provider.tick_once()
        self.assertGreater(len(provider.snapshot()["trades"]), trades_before)


class StrategyPolicyTests(unittest.TestCase):
    def test_manual_override_routes_without_mutating_scores(self) -> None:
        provider = runtime()
        scores_before = dict(provider.evaluator.scores)

        control = provider.set_strategy("B")
        self.assertEqual(control["strategy_policy"], "B")
        self.assertTrue(control["manual_override"])
        # Forcing a policy must not rewrite evaluator scores.
        self.assertEqual(provider.evaluator.scores, scores_before)
        self.assertEqual(provider.snapshot()["selected_strategy"], "B")

        for _ in range(5):
            provider.tick_once()
        self.assertEqual(provider.manager.last_selected, "B")

        auto = provider.set_strategy("auto")
        self.assertFalse(auto["manual_override"])

    def test_invalid_policy_rejected(self) -> None:
        provider = runtime()
        with self.assertRaises(ValueError):
            provider.set_strategy("C")


class RiskPolicyTests(unittest.TestCase):
    def _engine(self, position_limit_enabled: bool):
        portfolio = Portfolio(quiet=True)
        analytics = Analytics(portfolio.cash)
        engine = ExecutionEngine(
            portfolio,
            RiskEngine(max_position=1, position_limit_enabled=position_limit_enabled),
            Logger(quiet=True),
            AlertSystem(quiet=True),
            analytics,
        )
        return portfolio, engine

    def _signal(self, action: str, price: float, amount: float) -> dict:
        return {
            "strategy": "t",
            "action": action,
            "symbol": "BTC",
            "price": price,
            "amount": amount,
        }

    def test_disabling_position_limit_keeps_mandatory_invariants(self) -> None:
        portfolio, engine = self._engine(position_limit_enabled=False)

        # Position cap disabled: can exceed max_position=1.
        engine.on_signal(self._signal("BUY", 100.0, 1.0))
        engine.on_signal(self._signal("BUY", 100.0, 1.0))
        self.assertEqual(portfolio.asset, 2)

        # Mandatory invariants still hold:
        engine.on_signal(self._signal("BUY", 100.0, 0.0))  # invalid amount
        engine.on_signal(self._signal("BUY", 0.0, 1.0))  # invalid price
        engine.on_signal(self._signal("SELL", 100.0, 5.0))  # short inventory
        engine.on_signal(self._signal("BUY", 100.0, 1000.0))  # would go negative

        self.assertEqual(portfolio.asset, 2)  # blocked orders had no effect
        self.assertGreaterEqual(portfolio.cash, 0.0)  # never negative cash


class ModeIsolationTests(unittest.TestCase):
    def test_backtest_isolated_and_no_leaked_threads(self) -> None:
        provider = runtime()
        provider.start()
        provider.start()  # idempotent - must not spawn a second thread
        self.assertEqual(len(market_threads()), 1)
        time.sleep(0.05)

        live_cash = provider.portfolio.cash
        live_asset = provider.portfolio.asset

        backtest = provider.set_mode("backtest")
        self.assertEqual(backtest["mode"], "backtest")
        snap = provider.snapshot()
        self.assertEqual(snap["mode"], "backtest review")
        self.assertGreaterEqual(len(snap["equity_curve"]), 2)
        # Live market thread stopped during backtest; live state untouched.
        self.assertEqual(len(market_threads()), 0)
        self.assertEqual(provider.portfolio.cash, live_cash)
        self.assertEqual(provider.portfolio.asset, live_asset)

        provider.set_mode("live")
        self.assertEqual(provider.snapshot()["control"]["mode"], "live")
        self.assertEqual(len(market_threads()), 1)  # exactly one, resumed

        provider.stop()
        self.assertEqual(len(market_threads()), 0)  # cleaned up

    def test_mode_switch_is_idempotent(self) -> None:
        provider = runtime()
        self.assertEqual(provider.set_mode("live")["mode"], "live")  # already live
        self.assertEqual(len(market_threads()), 0)  # no thread spawned

    def test_reference_backtest_is_deterministic(self) -> None:
        first = run_reference_backtest("auto", True)
        second = run_reference_backtest("auto", True)
        self.assertEqual(first["portfolio"], second["portfolio"])
        self.assertEqual(
            [p["value"] for p in first["equity_curve"]],
            [p["value"] for p in second["equity_curve"]],
        )

    def test_invalid_mode_rejected(self) -> None:
        provider = runtime()
        with self.assertRaises(ValueError):
            provider.set_mode("paper")


class ProviderParityTests(unittest.TestCase):
    def providers(self):
        return [runtime(), MockDashboardProvider(seed=7)]

    def test_control_contract_parity(self) -> None:
        for provider in self.providers():
            with self.subTest(provider=type(provider).__name__):
                self.assertEqual(set(provider.get_control()), CONTROL_KEYS)
                self.assertFalse(provider.set_trading(False)["trading_enabled"])
                self.assertEqual(provider.set_strategy("B")["strategy_policy"], "B")
                self.assertFalse(
                    provider.set_risk(False)["position_limit_enabled"]
                )
                self.assertEqual(provider.set_mode("backtest")["mode"], "backtest")
                self.assertEqual(provider.snapshot()["mode"], "backtest review")
                self.assertIn("control", provider.snapshot())
                self.assertEqual(provider.set_mode("live")["mode"], "live")
                with self.assertRaises(ValueError):
                    provider.set_strategy("Z")
                with self.assertRaises(ValueError):
                    provider.set_mode("q")
                provider.stop()


class ConcurrencyTests(unittest.TestCase):
    def test_concurrent_commands_serialize_without_error(self) -> None:
        provider = runtime()
        errors: list[Exception] = []

        def hammer() -> None:
            try:
                for i in range(40):
                    provider.set_trading(i % 2 == 0)
                    provider.set_strategy(("auto", "A", "B")[i % 3])
                    provider.set_risk(i % 2 == 0)
            except Exception as exc:  # pragma: no cover - failure path
                errors.append(exc)

        threads = [threading.Thread(target=hammer) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        self.assertEqual(errors, [])
        control = provider.get_control()
        self.assertIn(control["strategy_policy"], ("auto", "A", "B"))
        self.assertIn(control["trading_enabled"], (True, False))


if __name__ == "__main__":
    unittest.main()
