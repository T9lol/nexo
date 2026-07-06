"""Unit + HTTP tests for the Risk Center API."""

import os
import unittest

import jwt
from fastapi.testclient import TestClient

import ui.dashboard as dash
from api.config import get_settings
from api.v1 import risk_derivations
from ui.providers import MockDashboardProvider

SECRET = "backend-sprint-4-secret-key-0123456789"
RATE = 4.0
MAX_POSITION = 5.0


def _bearer(**claims: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {jwt.encode(claims, SECRET, algorithm='HS256')}"}


def _snapshot(*, asset=5.0, cash=9500.0, trading=True, limit=True) -> dict:
    price = 100.0
    return {
        "updated_at": "2026-07-06T09:00:00+00:00",
        "market": {"symbol": "BTC", "price": price},
        "portfolio": {"cash": cash, "asset": asset, "equity": cash + asset * price, "pnl": 0.0},
        "control": {
            "trading_enabled": trading,
            "position_limit_enabled": limit,
            "environment": "local-simulation",
        },
    }


class RiskDerivationTests(unittest.TestCase):
    def test_overview_at_limit(self) -> None:
        data = risk_derivations.risk_overview(_snapshot(), MAX_POSITION, RATE)
        self.assertEqual(data["current_position"], 5.0)
        self.assertEqual(data["position_utilization_percent"], 100.0)
        self.assertEqual(data["exposure"]["percent"], 5.0)  # 500 / 10000
        self.assertTrue(data["limit_breached"])

    def test_portfolio_exposure_sums_100(self) -> None:
        data = risk_derivations.portfolio_exposure(_snapshot(), RATE)
        percents = [e["percent"] for e in data["exposures"]]
        self.assertEqual(round(sum(percents), 2), 100.0)

    def test_config_reports_supported_and_unsupported(self) -> None:
        data = risk_derivations.risk_configuration(_snapshot(), MAX_POSITION)
        self.assertEqual(data["max_position"], 5.0)
        self.assertEqual(data["editable"], ["position_limit_enabled"])
        self.assertIn("stop_loss", data["unsupported"])
        self.assertIn("daily_loss_limit", data["unsupported"])

    def test_alerts_derived_from_state(self) -> None:
        breach = risk_derivations.risk_alerts(_snapshot(asset=5.0), MAX_POSITION)
        codes = {a["code"] for a in breach["alerts"]}
        self.assertIn("position_limit_reached", codes)
        self.assertFalse(breach["history_available"])

        paused = risk_derivations.risk_alerts(_snapshot(asset=0.0, trading=False), MAX_POSITION)
        self.assertIn("trading_paused", {a["code"] for a in paused["alerts"]})

        clean = risk_derivations.risk_alerts(_snapshot(asset=0.0), MAX_POSITION)
        self.assertEqual(clean["alerts"], [])


class RiskApiTests(unittest.TestCase):
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

    def test_public_reads(self) -> None:
        for path in ("overview", "exposure", "portfolio-exposure", "config", "alerts"):
            response = self.client.get(f"/api/v1/risk/{path}")
            self.assertEqual(response.status_code, 200, path)
            self.assertTrue(response.json()["success"])

    def test_overview_has_engine_limit(self) -> None:
        data = self.client.get("/api/v1/risk/overview").json()["data"]
        self.assertEqual(data["max_position"], 5.0)
        self.assertIn("exposure", data)

    def test_emergency_stop_requires_auth(self) -> None:
        self.assertEqual(self.client.post("/api/v1/risk/emergency-stop").status_code, 401)

    def test_emergency_stop_halts_trading(self) -> None:
        self._enable_auth()
        response = self.client.post(
            "/api/v1/risk/emergency-stop", headers=_bearer(sub="op", roles=["user"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["data"]["trading_enabled"])
        # Reflected in the live control state.
        self.assertFalse(self.client.get("/api/control").json()["trading_enabled"])

    def test_save_settings_requires_auth_and_applies(self) -> None:
        self.assertEqual(
            self.client.put("/api/v1/risk/config", json={"position_limit_enabled": False}).status_code,
            401,
        )
        self._enable_auth()
        response = self.client.put(
            "/api/v1/risk/config",
            json={"position_limit_enabled": False},
            headers=_bearer(sub="op", roles=["user"]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["data"]["position_limit_enabled"])
        self.assertFalse(self.client.get("/api/control").json()["position_limit_enabled"])

    def test_save_settings_validates_body(self) -> None:
        self._enable_auth()
        response = self.client.put(
            "/api/v1/risk/config", json={}, headers=_bearer(sub="op", roles=["user"])
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_documented_in_openapi(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/risk/overview",
            "/api/v1/risk/exposure",
            "/api/v1/risk/portfolio-exposure",
            "/api/v1/risk/config",
            "/api/v1/risk/alerts",
            "/api/v1/risk/emergency-stop",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
