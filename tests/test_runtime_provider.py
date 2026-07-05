import os
import unittest

from ui.providers import (
    RuntimeDashboardProvider,
    build_provider,
    MockDashboardProvider,
    DashboardStore,
)


SCHEMA_KEYS = {
    "status",
    "mode",
    "updated_at",
    "market",
    "portfolio",
    "selected_strategy",
    "strategies",
    "trades",
    "equity_curve",
    "control",
}


class RuntimeProviderTests(unittest.TestCase):
    def make(self) -> RuntimeDashboardProvider:
        # A deterministic feed; do not start the background thread so ticks
        # are driven explicitly and the test stays reproducible.
        return RuntimeDashboardProvider(interval=0.01, seed=7)

    def test_snapshot_matches_existing_schema(self) -> None:
        provider = self.make()
        state = provider.snapshot()

        self.assertEqual(SCHEMA_KEYS, set(state))
        self.assertEqual(state["status"], "live")
        self.assertEqual(state["mode"], "UI-4 runtime")
        self.assertIn("price", state["market"])
        self.assertEqual(
            {"cash", "asset", "equity", "pnl"}, set(state["portfolio"])
        )
        self.assertEqual({"A", "B"}, set(state["strategies"]))
        for stats in state["strategies"].values():
            self.assertEqual(
                {"score", "weight", "updates", "adaptive"}, set(stats)
            )

    def test_adaptive_score_matches_evaluator_selection_metric(self) -> None:
        provider = self.make()
        for _ in range(40):
            provider.tick_once()

        strategies = provider.snapshot()["strategies"]
        for name, stats in strategies.items():
            self.assertEqual(
                stats["adaptive"],
                round(provider.evaluator.weighted_score(name), 2),
            )

    def test_ticks_drive_equity_curve_and_trades(self) -> None:
        provider = self.make()
        start_points = len(provider.snapshot()["equity_curve"])

        for _ in range(60):
            provider.tick_once()

        state = provider.snapshot()
        # Equity curve grew (and is capped).
        self.assertGreater(len(state["equity_curve"]), start_points)
        self.assertLessEqual(len(state["equity_curve"]), provider.max_points)
        # Trades were enriched with UI fields the runtime does not store.
        self.assertTrue(state["trades"], "expected at least one executed trade")
        trade = state["trades"][0]
        self.assertEqual(
            {"id", "time", "strategy", "action", "symbol", "price", "amount"},
            set(trade),
        )
        # Newest-first ordering.
        self.assertEqual(state["trades"], sorted(
            state["trades"], key=lambda t: t["id"], reverse=True
        ))

    def test_trade_count_matches_runtime_analytics(self) -> None:
        provider = self.make()
        for _ in range(80):
            provider.tick_once()

        state = provider.snapshot()
        # Every UI trade corresponds to a real analytics trade; UI never invents
        # or mutates executed trades.
        self.assertLessEqual(len(state["trades"]), len(provider.analytics.trades))
        self.assertEqual(
            provider._recorded, len(provider.analytics.trades)
        )

    def test_reported_pnl_tracks_real_portfolio(self) -> None:
        provider = self.make()
        for _ in range(50):
            provider.tick_once()

        state = provider.snapshot()
        price = provider.portfolio.last_price
        expected = round(provider.analytics.pnl(provider.portfolio, price), 2)
        self.assertEqual(state["portfolio"]["pnl"], expected)


class ProviderFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = os.environ.get("NEXO_DASHBOARD_PROVIDER")

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop("NEXO_DASHBOARD_PROVIDER", None)
        else:
            os.environ["NEXO_DASHBOARD_PROVIDER"] = self._saved

    def test_default_is_runtime(self) -> None:
        os.environ.pop("NEXO_DASHBOARD_PROVIDER", None)
        self.assertIsInstance(build_provider(), RuntimeDashboardProvider)

    def test_mock_opt_in(self) -> None:
        os.environ["NEXO_DASHBOARD_PROVIDER"] = "mock"
        self.assertIsInstance(build_provider(), MockDashboardProvider)

    def test_explicit_name_overrides_env(self) -> None:
        os.environ["NEXO_DASHBOARD_PROVIDER"] = "runtime"
        self.assertIsInstance(build_provider("mock"), MockDashboardProvider)

    def test_mock_provider_wraps_store(self) -> None:
        provider = MockDashboardProvider(seed=42)
        self.assertIsInstance(provider.store, DashboardStore)
        self.assertEqual(provider.snapshot()["mode"], "UI-1 simulation")


if __name__ == "__main__":
    unittest.main()
