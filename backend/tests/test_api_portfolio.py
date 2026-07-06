"""HTTP integration tests for the Portfolio module API."""

import unittest

from fastapi.testclient import TestClient

import ui.dashboard as dash
from ui.providers import MockDashboardProvider


class PortfolioApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original = dash.provider
        dash.provider = MockDashboardProvider(seed=7, interval=3600)
        self._ctx = TestClient(dash.app)
        self.client = self._ctx.__enter__()

    def tearDown(self) -> None:
        self._ctx.__exit__(None, None, None)
        dash.provider.stop()
        dash.provider = self._original

    def test_summary(self) -> None:
        body = self.client.get("/api/v1/portfolio/summary").json()
        self.assertTrue(body["success"])
        for key in ("total_value", "cash", "invested", "inception_pnl", "holdings_count"):
            self.assertIn(key, body["data"])
        self.assertEqual(body["meta"]["currency"]["primary"], "MYR")

    def test_holdings_list(self) -> None:
        body = self.client.get("/api/v1/portfolio/holdings").json()
        self.assertTrue(body["success"])
        self.assertIsInstance(body["data"]["holdings"], list)

    def test_allocation_percentages_sum_to_100(self) -> None:
        body = self.client.get("/api/v1/portfolio/allocation").json()
        self.assertTrue(body["success"])
        percents = [s["percent"] for s in body["data"]["allocation"]]
        self.assertEqual(round(sum(percents), 2), 100.0)

    def test_value_history(self) -> None:
        body = self.client.get("/api/v1/portfolio/value-history?limit=5").json()
        self.assertTrue(body["success"])
        self.assertIn("points", body["data"])
        self.assertLessEqual(body["data"]["count"], 5)

    def test_asset_details_known_symbol_case_insensitive(self) -> None:
        response = self.client.get("/api/v1/portfolio/assets/btc")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["symbol"], "BTC")

    def test_asset_details_unknown_symbol_is_404(self) -> None:
        response = self.client.get("/api/v1/portfolio/assets/DOGE")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")

    def test_documented_in_openapi(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/portfolio/summary",
            "/api/v1/portfolio/holdings",
            "/api/v1/portfolio/allocation",
            "/api/v1/portfolio/value-history",
            "/api/v1/portfolio/assets/{symbol}",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
