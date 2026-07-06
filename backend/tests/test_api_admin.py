"""HTTP tests for the Admin Console API (RBAC, real vs unavailable, maintenance)."""

import os
import unittest

import jwt
from fastapi.testclient import TestClient

import ui.dashboard as dash
from api.config import get_settings
from api.logging import clear_audit_records
from api.v1 import admin_service
from ui.providers import MockDashboardProvider

SECRET = "backend-sprint-5-secret-key-0123456789ab"


def _bearer(roles: list[str]) -> dict[str, str]:
    token = jwt.encode({"sub": "admin1", "roles": roles}, SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


class AdminApiTests(unittest.TestCase):
    def setUp(self) -> None:
        admin_service.reset_maintenance()
        self._original = dash.provider
        dash.provider = MockDashboardProvider(seed=7, interval=3600)
        self._ctx = TestClient(dash.app)
        self.client = self._ctx.__enter__()
        os.environ["NEXO_JWT_SECRET"] = SECRET  # admin routes need RBAC
        get_settings.cache_clear()

    def tearDown(self) -> None:
        admin_service.reset_maintenance()  # never leave maintenance on
        self._ctx.__exit__(None, None, None)
        dash.provider.stop()
        dash.provider = self._original
        os.environ.pop("NEXO_JWT_SECRET", None)
        get_settings.cache_clear()

    # -- RBAC ---------------------------------------------------------------

    def test_admin_routes_enforce_rbac(self) -> None:
        self.assertEqual(self.client.get("/api/v1/admin/users").status_code, 401)
        self.assertEqual(
            self.client.get("/api/v1/admin/users", headers=_bearer(["user"])).status_code, 403
        )
        ok = self.client.get("/api/v1/admin/users", headers=_bearer(["admin"]))
        self.assertEqual(ok.status_code, 200)

    def test_unavailable_subsystems_return_empty(self) -> None:
        for path in ("users", "kyc", "deposits", "withdrawals"):
            data = self.client.get(f"/api/v1/admin/{path}", headers=_bearer(["admin"])).json()["data"]
            self.assertEqual(data["items"], [])
            self.assertFalse(data["available"])

    def test_kyc_status_filter_validated(self) -> None:
        ok = self.client.get("/api/v1/admin/kyc?status=approved", headers=_bearer(["admin"]))
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["data"]["status"], "approved")
        bad = self.client.get("/api/v1/admin/kyc?status=weird", headers=_bearer(["admin"]))
        self.assertEqual(bad.status_code, 422)

    def test_decision_actions_are_unavailable(self) -> None:
        for path in ("kyc/k1", "deposits/d1", "withdrawals/w1"):
            response = self.client.post(
                f"/api/v1/admin/{path}/decision",
                json={"decision": "approved"},
                headers=_bearer(["admin"]),
            )
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["error"]["code"], "not_available")

    # -- Real capabilities --------------------------------------------------

    def test_feature_flags_are_real(self) -> None:
        flags = self.client.get("/api/v1/admin/feature-flags", headers=_bearer(["admin"])).json()["data"]
        keys = {f["key"] for f in flags["flags"]}
        self.assertIn("authentication_configured", keys)
        self.assertIn("user_management", keys)

    def test_system_health_is_real(self) -> None:
        data = self.client.get("/api/v1/admin/system-health", headers=_bearer(["admin"])).json()["data"]
        self.assertTrue(data["healthy"])
        self.assertEqual(data["environment"], "local-simulation")

    def test_audit_log_captures_events(self) -> None:
        clear_audit_records()
        # A logged admin action.
        self.client.put(
            "/api/v1/admin/maintenance",
            json={"enabled": False, "message": "noop"},
            headers=_bearer(["admin"]),
        )
        logs = self.client.get(
            "/api/v1/admin/audit-logs?event=admin_maintenance", headers=_bearer(["admin"])
        ).json()["data"]
        self.assertGreaterEqual(logs["count"], 1)
        self.assertFalse(logs["durable"])

    # -- Maintenance mode ---------------------------------------------------

    def test_maintenance_mode_gates_traffic(self) -> None:
        self.assertFalse(
            self.client.get("/api/v1/admin/maintenance", headers=_bearer(["admin"])).json()["data"]["enabled"]
        )
        enabled = self.client.put(
            "/api/v1/admin/maintenance",
            json={"enabled": True, "message": "Upgrading"},
            headers=_bearer(["admin"]),
        )
        self.assertTrue(enabled.json()["data"]["enabled"])

        # Non-exempt endpoint is blocked; admin + health stay reachable.
        blocked = self.client.get("/api/v1/dashboard/summary")
        self.assertEqual(blocked.status_code, 503)
        self.assertEqual(blocked.json()["error"]["code"], "maintenance")
        self.assertEqual(self.client.get("/api/v1/health").status_code, 200)
        self.assertEqual(
            self.client.get("/api/v1/admin/maintenance", headers=_bearer(["admin"])).status_code, 200
        )

        # Disable restores normal traffic.
        self.client.put(
            "/api/v1/admin/maintenance", json={"enabled": False}, headers=_bearer(["admin"])
        )
        self.assertEqual(self.client.get("/api/v1/dashboard/summary").status_code, 200)

    def test_documented_in_openapi(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/admin/users",
            "/api/v1/admin/kyc",
            "/api/v1/admin/deposits",
            "/api/v1/admin/withdrawals",
            "/api/v1/admin/audit-logs",
            "/api/v1/admin/system-health",
            "/api/v1/admin/feature-flags",
            "/api/v1/admin/maintenance",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
