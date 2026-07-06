"""Unit + HTTP tests for the Settings API."""

import os
import unittest

import jwt
from fastapi.testclient import TestClient

import ui.dashboard as dash
from api.config import get_settings
from api.v1 import settings_service
from ui.providers import MockDashboardProvider

SECRET = "backend-sprint-5-secret-key-0123456789ab"


def _bearer(roles: list[str]) -> dict[str, str]:
    token = jwt.encode({"sub": "op", "roles": roles}, SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


class FxServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        settings_service.reset()

    def tearDown(self) -> None:
        settings_service.reset()

    def test_automatic_falls_back_to_placeholder(self) -> None:
        resolved = settings_service.resolve_rate(4.7)
        self.assertEqual(resolved["rate"], 4.7)
        self.assertEqual(resolved["source"], "fallback")
        self.assertEqual(resolved["mode"], "automatic")

    def test_manual_override(self) -> None:
        settings_service.set_fx("manual", 4.55)
        resolved = settings_service.resolve_rate(4.7)
        self.assertEqual(resolved["rate"], 4.55)
        self.assertEqual(resolved["source"], "manual")

    def test_invalid_manual_normalizes_to_none(self) -> None:
        settings_service.set_fx("manual", 0)
        self.assertIsNone(settings_service.get_fx()["manual_rate"])
        # Falls back because there is no valid manual rate.
        self.assertEqual(settings_service.resolve_rate(4.7)["source"], "fallback")


class SettingsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        settings_service.reset()
        self._original = dash.provider
        dash.provider = MockDashboardProvider(seed=7, interval=3600)
        self._ctx = TestClient(dash.app)
        self.client = self._ctx.__enter__()

    def tearDown(self) -> None:
        self._ctx.__exit__(None, None, None)
        dash.provider.stop()
        dash.provider = self._original
        settings_service.reset()
        os.environ.pop("NEXO_JWT_SECRET", None)
        get_settings.cache_clear()

    def _enable_auth(self) -> None:
        os.environ["NEXO_JWT_SECRET"] = SECRET
        get_settings.cache_clear()

    def test_public_reads(self) -> None:
        for path in ("theme", "language", "currency", "exchange-rate", "system-info", "profile"):
            self.assertEqual(self.client.get(f"/api/v1/settings/{path}").status_code, 200, path)

    def test_currency_is_myr_primary(self) -> None:
        data = self.client.get("/api/v1/settings/currency").json()["data"]
        self.assertEqual(data["primary"], "MYR")
        self.assertTrue(data["usd_is_approximate"])

    def test_system_info_is_real(self) -> None:
        data = self.client.get("/api/v1/settings/system-info").json()["data"]
        self.assertIn("app_version", data)
        self.assertEqual(data["environment"], "local-simulation")

    def test_notifications_and_keys_require_user(self) -> None:
        self.assertEqual(self.client.get("/api/v1/settings/notifications").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/settings/api-keys").status_code, 401)
        self._enable_auth()
        notif = self.client.get("/api/v1/settings/notifications", headers=_bearer(["user"]))
        self.assertEqual(notif.status_code, 200)
        self.assertFalse(notif.json()["data"]["delivery_available"])
        keys = self.client.get("/api/v1/settings/api-keys", headers=_bearer(["user"]))
        self.assertEqual(keys.json()["data"]["keys"], [])

    def test_create_api_key_is_unavailable(self) -> None:
        self._enable_auth()
        response = self.client.post("/api/v1/settings/api-keys", headers=_bearer(["user"]))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "not_available")

    def test_exchange_rate_update_requires_admin(self) -> None:
        self._enable_auth()
        body = {"mode": "manual", "manual_rate": 4.55}
        self.assertEqual(
            self.client.put("/api/v1/settings/exchange-rate", json=body).status_code, 401
        )
        self.assertEqual(
            self.client.put("/api/v1/settings/exchange-rate", json=body, headers=_bearer(["user"])).status_code,
            403,
        )
        ok = self.client.put("/api/v1/settings/exchange-rate", json=body, headers=_bearer(["admin"]))
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["data"]["effective_rate"], 4.55)
        self.assertEqual(ok.json()["data"]["effective_source"], "manual")
        # Reflected in the currency view.
        self.assertEqual(
            self.client.get("/api/v1/settings/currency").json()["data"]["usd_myr_rate"], 4.55
        )

    def test_exchange_rate_validation(self) -> None:
        self._enable_auth()
        bad = self.client.put(
            "/api/v1/settings/exchange-rate", json={"mode": "manual"}, headers=_bearer(["admin"])
        )
        self.assertEqual(bad.status_code, 400)
        unknown = self.client.put(
            "/api/v1/settings/exchange-rate", json={"mode": "zzz"}, headers=_bearer(["admin"])
        )
        self.assertEqual(unknown.status_code, 400)

    def test_profile_anonymous_vs_authenticated(self) -> None:
        anon = self.client.get("/api/v1/settings/profile").json()["data"]
        self.assertFalse(anon["authenticated"])
        self._enable_auth()
        auth = self.client.get("/api/v1/settings/profile", headers=_bearer(["user"])).json()["data"]
        self.assertTrue(auth["authenticated"])
        self.assertEqual(auth["subject"], "op")

    def test_documented_in_openapi(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/settings/profile",
            "/api/v1/settings/currency",
            "/api/v1/settings/exchange-rate",
            "/api/v1/settings/notifications",
            "/api/v1/settings/api-keys",
            "/api/v1/settings/system-info",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
