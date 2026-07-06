"""Tests for JWT-ready auth/authorization abstractions (:mod:`api.security`).

Tokens are minted *inside the tests* purely to exercise the decode/verify path.
The application itself never issues tokens.
"""

import os
import unittest

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.config import get_settings
from api.errors import UnauthorizedError, install_exception_handlers
from api.security import (
    Principal,
    Role,
    decode_access_token,
    require_admin,
    require_user,
)

SECRET = "unit-test-secret"


def _token(*, secret: str = SECRET, **claims: object) -> str:
    return jwt.encode(claims, secret, algorithm="HS256")


def _bearer(**claims: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(**claims)}"}


def _make_app() -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)

    @app.get("/user")
    def user_route(principal: Principal = Depends(require_user)) -> dict[str, object]:
        return {"subject": principal.subject, "roles": [r.value for r in principal.roles]}

    @app.get("/admin")
    def admin_route(principal: Principal = Depends(require_admin)) -> dict[str, str]:
        return {"subject": principal.subject}

    return app


class DecodeAccessTokenTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["NEXO_JWT_SECRET"] = SECRET
        get_settings.cache_clear()
        self.settings = get_settings()

    def tearDown(self) -> None:
        os.environ.pop("NEXO_JWT_SECRET", None)
        get_settings.cache_clear()

    def test_valid_token_yields_principal_with_roles(self) -> None:
        principal = decode_access_token(
            _token(sub="u1", roles=["user", "admin"]), self.settings
        )
        self.assertEqual(principal.subject, "u1")
        self.assertIn(Role.ADMIN, principal.roles)
        self.assertTrue(principal.has_role(Role.USER))

    def test_unknown_roles_are_ignored(self) -> None:
        principal = decode_access_token(
            _token(sub="u1", roles=["user", "superhero"]), self.settings
        )
        self.assertEqual(principal.roles, [Role.USER])

    def test_missing_subject_is_rejected(self) -> None:
        with self.assertRaises(UnauthorizedError):
            decode_access_token(_token(roles=["user"]), self.settings)

    def test_bad_signature_is_rejected(self) -> None:
        with self.assertRaises(UnauthorizedError):
            decode_access_token(_token(secret="wrong", sub="u1"), self.settings)

    def test_unconfigured_auth_is_rejected(self) -> None:
        os.environ.pop("NEXO_JWT_SECRET", None)
        get_settings.cache_clear()
        with self.assertRaises(UnauthorizedError):
            decode_access_token(_token(sub="u1"), get_settings())


class AuthorizationGateTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["NEXO_JWT_SECRET"] = SECRET
        get_settings.cache_clear()
        self.client = TestClient(_make_app())

    def tearDown(self) -> None:
        os.environ.pop("NEXO_JWT_SECRET", None)
        get_settings.cache_clear()

    def test_require_user_rejects_anonymous(self) -> None:
        response = self.client.get("/user")
        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "unauthorized")
        self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_require_user_accepts_valid_token(self) -> None:
        response = self.client.get("/user", headers=_bearer(sub="u1", roles=["user"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["subject"], "u1")

    def test_invalid_token_is_401(self) -> None:
        response = self.client.get(
            "/user", headers={"Authorization": "Bearer not-a-jwt"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "invalid_token")

    def test_require_admin_forbids_non_admin(self) -> None:
        response = self.client.get("/admin", headers=_bearer(sub="u1", roles=["user"]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "forbidden")

    def test_require_admin_allows_admin(self) -> None:
        response = self.client.get(
            "/admin", headers=_bearer(sub="admin1", roles=["admin"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["subject"], "admin1")


if __name__ == "__main__":
    unittest.main()
