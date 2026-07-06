"""Unit + HTTP tests for the Backtest Center API."""

import os
import unittest

import jwt
from fastapi.testclient import TestClient

import ui.dashboard as dash
from api.config import get_settings
from api.v1 import backtest_derivations, backtest_service
from ui.providers import MockDashboardProvider

SECRET = "backend-sprint-4-secret-key-0123456789"
RATE = 4.0


def _bearer(**claims: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {jwt.encode(claims, SECRET, algorithm='HS256')}"}


def _result() -> dict:
    return {
        "market": {"symbol": "BTC", "price": 103.0},
        "trades": [
            {"id": "bt-1", "time": "t", "strategy": "A", "action": "BUY", "symbol": "BTC", "price": 100.0, "amount": 1.0},
            {"id": "bt-2", "time": "t", "strategy": "A", "action": "SELL", "symbol": "BTC", "price": 103.0, "amount": 1.0},
        ],
        "equity_curve": [
            {"time": "t0", "value": 10000.0},
            {"time": "t1", "value": 10200.0},  # peak
            {"time": "t2", "value": 10100.0},  # drawdown from 10200
            {"time": "t3", "value": 10300.0},  # final (new high)
        ],
    }


class BacktestDerivationTests(unittest.TestCase):
    def test_total_return(self) -> None:
        metrics = backtest_derivations.performance_metrics(_result(), RATE)
        self.assertEqual(metrics["total_return"]["myr"], 300.0)
        self.assertEqual(metrics["total_return"]["percent"], 3.0)

    def test_max_drawdown(self) -> None:
        metrics = backtest_derivations.performance_metrics(_result(), RATE)
        # 10100 vs peak 10200 -> -0.9804%
        self.assertAlmostEqual(metrics["max_drawdown"]["percent"], -0.9804, places=3)
        self.assertEqual(metrics["max_drawdown"]["value"]["myr"], -100.0)

    def test_untracked_metrics_are_null(self) -> None:
        metrics = backtest_derivations.performance_metrics(_result(), RATE)
        self.assertIsNone(metrics["cagr"])
        self.assertIsNone(metrics["sharpe_ratio"])
        self.assertIsNone(metrics["win_rate"])
        self.assertFalse(metrics["metrics_tracked"]["sharpe_ratio"])
        self.assertTrue(metrics["metrics_tracked"]["total_return"])
        self.assertEqual(metrics["total_trades"], 2)

    def test_drawdown_series_tracks_peak(self) -> None:
        data = backtest_derivations.drawdown_series(_result())
        self.assertEqual(data["count"], 4)
        self.assertEqual(data["points"][0]["drawdown_percent"], 0.0)
        self.assertLess(data["points"][2]["drawdown_percent"], 0.0)  # the dip

    def test_report_csv(self) -> None:
        csv_text = backtest_derivations.report_csv(_result())
        lines = csv_text.strip().splitlines()
        self.assertTrue(lines[0].startswith("id,time,strategy,action,symbol,price,amount,value"))
        self.assertEqual(len(lines), 3)  # header + 2 trades


class BacktestApiTests(unittest.TestCase):
    def setUp(self) -> None:
        backtest_service.reset()
        self._original = dash.provider
        dash.provider = MockDashboardProvider(seed=7, interval=3600)
        self._ctx = TestClient(dash.app)
        self.client = self._ctx.__enter__()

    def tearDown(self) -> None:
        self._ctx.__exit__(None, None, None)
        dash.provider.stop()
        dash.provider = self._original
        backtest_service.reset()
        os.environ.pop("NEXO_JWT_SECRET", None)
        get_settings.cache_clear()

    def _enable_auth(self) -> None:
        os.environ["NEXO_JWT_SECRET"] = SECRET
        get_settings.cache_clear()

    def test_status_idle_before_run(self) -> None:
        body = self.client.get("/api/v1/backtest/status").json()
        self.assertEqual(body["data"]["status"], "idle")

    def test_reads_404_before_run(self) -> None:
        self.assertEqual(self.client.get("/api/v1/backtest/metrics").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/backtest/equity-curve").status_code, 404)

    def test_run_requires_auth(self) -> None:
        response = self.client.post("/api/v1/backtest/run", json={"policy": "auto"})
        self.assertEqual(response.status_code, 401)

    def test_run_rejects_bad_policy(self) -> None:
        self._enable_auth()
        response = self.client.post(
            "/api/v1/backtest/run", json={"policy": "Z"}, headers=_bearer(sub="op", roles=["user"])
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "bad_request")

    def test_run_then_read_all(self) -> None:
        self._enable_auth()
        run = self.client.post(
            "/api/v1/backtest/run",
            json={"policy": "auto", "position_limit_enabled": True},
            headers=_bearer(sub="op", roles=["user"]),
        )
        self.assertEqual(run.status_code, 200)
        self.assertEqual(run.json()["data"]["status"], "completed")

        self.assertEqual(self.client.get("/api/v1/backtest/status").json()["data"]["status"], "completed")
        metrics = self.client.get("/api/v1/backtest/metrics").json()
        self.assertIn("total_return", metrics["data"])
        self.assertIsNone(metrics["data"]["cagr"])
        self.assertEqual(metrics["meta"]["currency"]["primary"], "MYR")
        self.assertGreater(self.client.get("/api/v1/backtest/equity-curve").json()["data"]["count"], 0)
        self.assertIn("points", self.client.get("/api/v1/backtest/drawdown").json()["data"])
        self.assertIn("trades", self.client.get("/api/v1/backtest/trades").json()["data"])

        report = self.client.get("/api/v1/backtest/report.csv")
        self.assertEqual(report.status_code, 200)
        self.assertIn("text/csv", report.headers["content-type"])

    def test_documented_in_openapi(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/backtest/run",
            "/api/v1/backtest/status",
            "/api/v1/backtest/equity-curve",
            "/api/v1/backtest/drawdown",
            "/api/v1/backtest/metrics",
            "/api/v1/backtest/trades",
            "/api/v1/backtest/report.csv",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
