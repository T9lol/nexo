"""Integration tests for the versioned API, legacy compatibility, and OpenAPI.

Covers standardized envelopes, JWT-ready authorization on control mutations,
that legacy routes are byte-for-byte preserved (shapes, status codes, public
access), deprecation headers, and OpenAPI documentation of both surfaces.
"""

import os
import unittest

import jwt
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

import ui.dashboard as dash
from api.config import get_settings
from ui.providers import MockDashboardProvider

SECRET = "v1-integration-secret"


def _bearer(**claims: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {jwt.encode(claims, SECRET, algorithm='HS256')}"}


class ApiV1IntegrationTests(unittest.TestCase):
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

    # -- standardized success envelopes ------------------------------------

    def test_health_envelope(self) -> None:
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"success": True, "data": {"status": "ok"}, "meta": {"api_version": "v1"}},
        )

    def test_state_envelope(self) -> None:
        body = self.client.get("/api/v1/state").json()
        self.assertTrue(body["success"])
        self.assertEqual(body["meta"]["api_version"], "v1")
        self.assertIn("control", body["data"])
        self.assertIn("market", body["data"])

    def test_trades_envelope(self) -> None:
        body = self.client.get("/api/v1/trades").json()
        self.assertTrue(body["success"])
        self.assertIsInstance(body["data"], list)

    def test_control_get_envelope(self) -> None:
        body = self.client.get("/api/v1/control").json()
        self.assertTrue(body["success"])
        self.assertIn("trading_enabled", body["data"])

    # -- authorization gates -----------------------------------------------

    def test_control_mutation_requires_auth(self) -> None:
        response = self.client.post("/api/v1/control/trading", json={"enabled": True})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "unauthorized")
        self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_auth_me_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)

    def test_control_mutation_authorized(self) -> None:
        self._enable_auth()
        response = self.client.post(
            "/api/v1/control/trading",
            json={"enabled": False},
            headers=_bearer(sub="op1", roles=["user"]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertFalse(response.json()["data"]["trading_enabled"])
        # Mutation is applied to the shared provider (no new business logic).
        reflected = self.client.get("/api/v1/state").json()
        self.assertFalse(reflected["data"]["control"]["trading_enabled"])

    def test_auth_me_authorized(self) -> None:
        self._enable_auth()
        response = self.client.get(
            "/api/v1/auth/me", headers=_bearer(sub="op1", roles=["user"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"], {"subject": "op1", "roles": ["user"]}
        )

    # -- standardized error envelopes --------------------------------------

    def test_validation_error_envelope(self) -> None:
        self._enable_auth()
        response = self.client.post(
            "/api/v1/control/trading", json={}, headers=_bearer(sub="op1", roles=["user"])
        )
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "validation_error")
        self.assertIsInstance(body["error"]["details"], list)

    def test_domain_error_envelope(self) -> None:
        self._enable_auth()
        response = self.client.post(
            "/api/v1/control/strategy",
            json={"policy": "C"},
            headers=_bearer(sub="op1", roles=["user"]),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "bad_request")

    # -- legacy compatibility (must be byte-for-byte preserved) ------------

    def test_legacy_read_shapes_unchanged(self) -> None:
        self.assertEqual(self.client.get("/api/health").json(), {"status": "ok"})
        self.assertIn("portfolio", self.client.get("/api/state").json())
        self.assertIsInstance(self.client.get("/api/trades").json(), list)

    def test_legacy_error_shapes_unchanged(self) -> None:
        strategy = self.client.post("/api/control/strategy", json={"policy": "C"})
        self.assertEqual(strategy.status_code, 400)
        self.assertIn("policy", strategy.json()["detail"].lower())  # raw {"detail"}
        self.assertEqual(
            self.client.post("/api/control/trading", json={}).status_code, 422
        )

    def test_legacy_mutations_remain_public(self) -> None:
        # No auth applied to legacy routes -> frontend/proxy keep working.
        response = self.client.post("/api/control/trading", json={"enabled": True})
        self.assertEqual(response.status_code, 200)
        self.assertIn("trading_enabled", response.json())

    # -- deprecation / migration structure ---------------------------------

    def test_legacy_carries_deprecation_headers(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.headers.get("deprecation"), "true")
        self.assertEqual(
            response.headers.get("link"),
            '</api/v1/health>; rel="successor-version"',
        )

    def test_versioned_routes_not_deprecated(self) -> None:
        self.assertIsNone(
            self.client.get("/api/v1/health").headers.get("deprecation")
        )

    # -- OpenAPI documentation ---------------------------------------------

    def test_openapi_documents_both_surfaces(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        self.assertIn("/api/v1/state", paths)
        self.assertIn("/api/v1/control/trading", paths)
        self.assertIn("/api/v1/auth/me", paths)
        self.assertIn("/api/state", paths)
        # Legacy is advertised as deprecated; versioned is not.
        self.assertTrue(paths["/api/state"]["get"]["deprecated"])
        self.assertNotIn("deprecated", paths["/api/v1/state"]["get"])

    def test_docs_endpoint_served(self) -> None:
        self.assertEqual(self.client.get("/docs").status_code, 200)

    # -- CORS configuration -------------------------------------------------

    def test_cors_middleware_installed(self) -> None:
        self.assertTrue(
            any(mw.cls is CORSMiddleware for mw in dash.app.user_middleware)
        )


if __name__ == "__main__":
    unittest.main()
