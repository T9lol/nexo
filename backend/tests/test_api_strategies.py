"""Unit + HTTP tests for the Strategy Center API."""

import os
import unittest

import jwt
from fastapi.testclient import TestClient

import ui.dashboard as dash
from api.config import get_settings
from api.v1 import strategy_derivations
from ui.providers import MockDashboardProvider

SECRET = "backend-sprint-3-secret-key-0123456789"


def _bearer(**claims: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {jwt.encode(claims, SECRET, algorithm='HS256')}"}


def _snapshot() -> dict:
    return {
        "updated_at": "2026-07-06T09:00:00+00:00",
        "selected_strategy": "A",
        "control": {"strategy_policy": "A", "trading_enabled": True},
        "strategies": {
            "A": {"score": 30.0, "weight": 1.05, "updates": 12, "adaptive": 31.5},
            "B": {"score": 24.0, "weight": 0.98, "updates": 9, "adaptive": 23.5},
        },
        "trades": [
            {"id": "t1", "strategy": "A", "symbol": "BTC", "action": "BUY"},
            {"id": "t2", "strategy": "A", "symbol": "BTC", "action": "SELL"},
            {"id": "t3", "strategy": "B", "symbol": "BTC", "action": "BUY"},
        ],
    }


class StrategyDerivationTests(unittest.TestCase):
    def test_list_sorted_with_active_and_metrics(self) -> None:
        data = strategy_derivations.strategy_list(_snapshot())
        self.assertEqual([s["name"] for s in data["strategies"]], ["A", "B"])
        self.assertEqual(data["active"], "A")
        a = data["strategies"][0]
        self.assertTrue(a["active"])
        self.assertEqual(a["metrics"]["score"], 30.0)
        self.assertEqual(a["metrics"]["total_trades"], 2)  # two A trades
        # Untracked per-strategy metrics are honest nulls.
        self.assertIsNone(a["metrics"]["pnl"])
        self.assertIsNone(a["metrics"]["win_rate"])
        self.assertIsNone(a["metrics"]["drawdown"])
        self.assertFalse(a["metrics_tracked"]["pnl"])

    def test_details_case_insensitive_and_override_flag(self) -> None:
        data = strategy_derivations.strategy_details(_snapshot(), "b")
        self.assertEqual(data["name"], "B")
        self.assertFalse(data["is_manual_override"])  # policy is A
        self.assertEqual(data["metrics"]["total_trades"], 1)

    def test_details_unknown_is_none(self) -> None:
        self.assertIsNone(strategy_derivations.strategy_details(_snapshot(), "ZZZ"))

    def test_comparison_picks_best_adaptive(self) -> None:
        data = strategy_derivations.strategy_comparison(_snapshot())
        self.assertEqual(data["best_by_adaptive_score"], "A")  # 31.5 > 23.5


class StrategyApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original = dash.provider
        dash.provider = MockDashboardProvider(seed=7, interval=3600)
        self._ctx = TestClient(dash.app)
        self.client = self._ctx.__enter__()

    def tearDown(self) -> None:
        self._ctx.__exit__(None, None, None)
        dash.provider.stop()
        dash.provider = self._original
        os.environ.pop("NEXO_JWT_SECRET", None)
        get_settings.cache_clear()

    def _enable_auth(self) -> None:
        os.environ["NEXO_JWT_SECRET"] = SECRET
        get_settings.cache_clear()

    def test_list(self) -> None:
        body = self.client.get("/api/v1/strategies").json()
        self.assertTrue(body["success"])
        self.assertGreaterEqual(body["data"]["count"], 2)

    def test_details_and_404(self) -> None:
        self.assertEqual(self.client.get("/api/v1/strategies/A").status_code, 200)
        response = self.client.get("/api/v1/strategies/NOPE")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")

    def test_comparison(self) -> None:
        body = self.client.get("/api/v1/strategies/comparison").json()
        self.assertIn("best_by_adaptive_score", body["data"])

    def test_enable_requires_auth(self) -> None:
        response = self.client.post("/api/v1/strategies/A/enable")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_enable_then_disable_authorized(self) -> None:
        self._enable_auth()
        enabled = self.client.post(
            "/api/v1/strategies/A/enable", headers=_bearer(sub="op", roles=["user"])
        )
        self.assertEqual(enabled.status_code, 200)
        self.assertTrue(enabled.json()["data"]["active"])
        self.assertTrue(enabled.json()["data"]["is_manual_override"])

        disabled = self.client.post(
            "/api/v1/strategies/A/disable", headers=_bearer(sub="op", roles=["user"])
        )
        self.assertEqual(disabled.status_code, 200)
        self.assertFalse(disabled.json()["data"]["is_manual_override"])

    def test_enable_unknown_strategy_404(self) -> None:
        self._enable_auth()
        response = self.client.post(
            "/api/v1/strategies/NOPE/enable", headers=_bearer(sub="op", roles=["user"])
        )
        self.assertEqual(response.status_code, 404)

    def test_documented_in_openapi(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/strategies",
            "/api/v1/strategies/comparison",
            "/api/v1/strategies/{name}",
            "/api/v1/strategies/{name}/enable",
            "/api/v1/strategies/{name}/disable",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
