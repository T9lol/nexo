"""HTTP round-trip tests for the UI-4 control endpoints.

These use Starlette's real TestClient (backed by httpx, installed via the
``test`` extra) so requests traverse routing, Pydantic validation, the
provider, and JSON serialization exactly as in production. A deterministic mock
provider is injected so assertions are stable, and the mock's tick interval is
set arbitrarily large so no background ticking mutates state mid-assertion.
"""

import unittest

from fastapi.testclient import TestClient

import ui.dashboard as dash
from ui.providers import MockDashboardProvider


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


class ControlApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original = dash.provider
        # interval=3600 -> the mock never ticks during a test run.
        dash.provider = MockDashboardProvider(seed=7, interval=3600)
        self._ctx = TestClient(dash.app)
        self.client = self._ctx.__enter__()  # runs lifespan start()

    def tearDown(self) -> None:
        self._ctx.__exit__(None, None, None)  # runs lifespan stop()
        dash.provider.stop()
        dash.provider = self._original

    # -- reads --------------------------------------------------------------

    def test_get_control_is_canonical(self) -> None:
        response = self.client.get("/api/control")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body), CONTROL_KEYS)
        self.assertEqual(body["allowed"]["strategy_policy"], ["auto", "A", "B"])
        self.assertEqual(body["allowed"]["mode"], ["live", "backtest"])
        self.assertEqual(body["environment"], "local-simulation")

    def test_state_reflects_control(self) -> None:
        state = self.client.get("/api/state").json()
        self.assertIn("control", state)
        self.assertEqual(set(state["control"]), CONTROL_KEYS)

    def test_backward_compatible_endpoints(self) -> None:
        self.assertEqual(self.client.get("/api/health").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/api/trades").status_code, 200)

    # -- trading ------------------------------------------------------------

    def test_trading_valid_idempotent_and_reflected(self) -> None:
        first = self.client.post("/api/control/trading", json={"enabled": False})
        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.json()["trading_enabled"])

        # Idempotent: same command, same canonical result.
        second = self.client.post("/api/control/trading", json={"enabled": False})
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json(), first.json())

        # Reflected in /api/state.
        state = self.client.get("/api/state").json()
        self.assertFalse(state["control"]["trading_enabled"])

        resumed = self.client.post("/api/control/trading", json={"enabled": True})
        self.assertTrue(resumed.json()["trading_enabled"])

    def test_trading_invalid_payloads(self) -> None:
        self.assertEqual(
            self.client.post("/api/control/trading", json={}).status_code, 422
        )
        self.assertEqual(
            self.client.post(
                "/api/control/trading", json={"enabled": "banana"}
            ).status_code,
            422,
        )

    # -- strategy -----------------------------------------------------------

    def test_strategy_valid_all_policies_and_idempotent(self) -> None:
        for policy in ("auto", "A", "B"):
            response = self.client.post(
                "/api/control/strategy", json={"policy": policy}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["strategy_policy"], policy)
            self.assertEqual(response.json()["manual_override"], policy in ("A", "B"))
            # Idempotent repeat.
            again = self.client.post(
                "/api/control/strategy", json={"policy": policy}
            )
            self.assertEqual(again.json(), response.json())

        state = self.client.get("/api/state").json()
        self.assertEqual(state["control"]["strategy_policy"], "B")

    def test_strategy_invalid_value_is_400(self) -> None:
        response = self.client.post("/api/control/strategy", json={"policy": "C"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("policy", response.json()["detail"].lower())

    def test_strategy_missing_field_is_422(self) -> None:
        self.assertEqual(
            self.client.post("/api/control/strategy", json={}).status_code, 422
        )

    # -- risk ---------------------------------------------------------------

    def test_risk_valid_idempotent_and_reflected(self) -> None:
        first = self.client.post(
            "/api/control/risk", json={"position_limit_enabled": False}
        )
        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.json()["position_limit_enabled"])

        second = self.client.post(
            "/api/control/risk", json={"position_limit_enabled": False}
        )
        self.assertEqual(second.json(), first.json())

        state = self.client.get("/api/state").json()
        self.assertFalse(state["control"]["position_limit_enabled"])

    def test_risk_invalid_payload_is_422(self) -> None:
        self.assertEqual(
            self.client.post("/api/control/risk", json={}).status_code, 422
        )

    # -- mode ---------------------------------------------------------------

    def test_mode_roundtrip_idempotent_and_reflected(self) -> None:
        backtest = self.client.post("/api/control/mode", json={"mode": "backtest"})
        self.assertEqual(backtest.status_code, 200)
        self.assertEqual(backtest.json()["mode"], "backtest")

        # Idempotent repeat returns the same control state.
        again = self.client.post("/api/control/mode", json={"mode": "backtest"})
        self.assertEqual(again.json(), backtest.json())

        # /api/state now serves the isolated backtest snapshot.
        state = self.client.get("/api/state").json()
        self.assertEqual(state["mode"], "backtest review")
        self.assertEqual(state["control"]["mode"], "backtest")

        live = self.client.post("/api/control/mode", json={"mode": "live"})
        self.assertEqual(live.json()["mode"], "live")
        self.assertEqual(
            self.client.get("/api/state").json()["control"]["mode"], "live"
        )

    def test_mode_invalid_value_is_400(self) -> None:
        response = self.client.post("/api/control/mode", json={"mode": "paper"})
        self.assertEqual(response.status_code, 400)

    def test_mode_missing_field_is_422(self) -> None:
        self.assertEqual(
            self.client.post("/api/control/mode", json={}).status_code, 422
        )


if __name__ == "__main__":
    unittest.main()
