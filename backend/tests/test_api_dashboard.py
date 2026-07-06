"""HTTP integration tests for the Dashboard module API."""

import unittest

from fastapi.testclient import TestClient

import ui.dashboard as dash
from ui.providers import MockDashboardProvider


class DashboardApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original = dash.provider
        dash.provider = MockDashboardProvider(seed=7, interval=3600)
        self._ctx = TestClient(dash.app)
        self.client = self._ctx.__enter__()

    def tearDown(self) -> None:
        self._ctx.__exit__(None, None, None)
        dash.provider.stop()
        dash.provider = self._original

    def test_summary_shape_and_currency_meta(self) -> None:
        response = self.client.get("/api/v1/dashboard/summary")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["meta"]["currency"]["primary"], "MYR")
        self.assertTrue(body["meta"]["currency"]["usd_is_approximate"])
        data = body["data"]
        for key in ("total_assets", "today_pnl", "monthly_pnl", "active_strategy", "system_status"):
            self.assertIn(key, data)
        self.assertIn("myr", data["total_assets"])
        self.assertIn("usd", data["total_assets"])
        self.assertEqual(data["system_status"]["environment"], "local-simulation")

    def test_equity_curve_public_and_limit(self) -> None:
        body = self.client.get("/api/v1/dashboard/equity-curve?limit=1").json()
        self.assertTrue(body["success"])
        self.assertLessEqual(body["data"]["count"], 1)
        self.assertIn("points", body["data"])

    def test_recent_trades(self) -> None:
        body = self.client.get("/api/v1/dashboard/trades").json()
        self.assertTrue(body["success"])
        self.assertIsInstance(body["data"]["trades"], list)

    def test_limit_validation_is_standardized_422(self) -> None:
        response = self.client.get("/api/v1/dashboard/equity-curve?limit=0")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "validation_error")
        self.assertEqual(
            self.client.get("/api/v1/dashboard/trades?limit=9999").status_code, 422
        )

    def test_documented_in_openapi(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        self.assertIn("/api/v1/dashboard/summary", paths)
        self.assertIn("/api/v1/dashboard/equity-curve", paths)
        self.assertIn("/api/v1/dashboard/trades", paths)


if __name__ == "__main__":
    unittest.main()
