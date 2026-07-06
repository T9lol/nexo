"""Phase 2 tests: auth (register/login/refresh/logout), RBAC, password hashing."""

import os
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import ui.dashboard as dash
from api.config import get_settings
from api.v2 import auth_service
from db.base import Base
from db.models import User, UserRole
from db.session import get_db

SECRET = "phase2-auth-secret-key-0123456789abcdef"


class AuthTestBase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["NEXO_JWT_SECRET"] = SECRET
        get_settings.cache_clear()
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        def _override_get_db():
            session = self.Session()
            try:
                yield session
            finally:
                session.close()

        dash.app.dependency_overrides[get_db] = _override_get_db
        self.client = TestClient(dash.app)

    def tearDown(self) -> None:
        dash.app.dependency_overrides.clear()
        os.environ.pop("NEXO_JWT_SECRET", None)
        get_settings.cache_clear()

    # helpers -----------------------------------------------------------------

    def _register(self, email="a@test.co", password="password123"):
        return self.client.post("/api/v2/auth/register", json={"email": email, "password": password})

    def _login(self, email="a@test.co", password="password123"):
        return self.client.post("/api/v2/auth/login", json={"email": email, "password": password})

    def _auth_header(self, access: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access}"}

    def _make_admin(self, email="admin@test.co", password="adminpass123") -> None:
        session = self.Session()
        session.add(
            User(
                email=email,
                hashed_password=auth_service.hash_password(password),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
        )
        session.commit()
        session.close()


class PasswordHashingTests(unittest.TestCase):
    def test_hash_and_verify(self) -> None:
        h = auth_service.hash_password("s3cret-pass")
        self.assertNotEqual(h, "s3cret-pass")
        self.assertTrue(auth_service.verify_password("s3cret-pass", h))
        self.assertFalse(auth_service.verify_password("wrong", h))


class RegisterLoginTests(AuthTestBase):
    def test_register_creates_user(self) -> None:
        r = self._register()
        self.assertEqual(r.status_code, 201)
        data = r.json()["data"]
        self.assertEqual(data["email"], "a@test.co")
        self.assertEqual(data["role"], "user")
        self.assertTrue(data["is_active"])

    def test_register_duplicate_is_409(self) -> None:
        self._register()
        r = self._register()
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "conflict")

    def test_register_weak_password_is_422(self) -> None:
        r = self.client.post("/api/v2/auth/register", json={"email": "b@test.co", "password": "short"})
        self.assertEqual(r.status_code, 422)

    def test_register_bad_email_is_422(self) -> None:
        r = self.client.post("/api/v2/auth/register", json={"email": "notanemail", "password": "password123"})
        self.assertEqual(r.status_code, 422)

    def test_login_returns_token_pair(self) -> None:
        self._register()
        r = self._login()
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertGreater(data["expires_in"], 0)

    def test_login_wrong_password_is_401(self) -> None:
        self._register()
        r = self._login(password="wrongpass1")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"]["code"], "invalid_credentials")


class SessionTests(AuthTestBase):
    def test_me_requires_and_accepts_token(self) -> None:
        self.assertEqual(self.client.get("/api/v2/auth/me").status_code, 401)
        self._register()
        access = self._login().json()["data"]["access_token"]
        r = self.client.get("/api/v2/auth/me", headers=self._auth_header(access))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["email"], "a@test.co")

    def test_refresh_rotates_and_invalidates_old(self) -> None:
        self._register()
        first = self._login().json()["data"]["refresh_token"]
        rotated = self.client.post("/api/v2/auth/refresh", json={"refresh_token": first})
        self.assertEqual(rotated.status_code, 200)
        new_refresh = rotated.json()["data"]["refresh_token"]
        self.assertNotEqual(new_refresh, first)
        # Old refresh token is now revoked.
        self.assertEqual(
            self.client.post("/api/v2/auth/refresh", json={"refresh_token": first}).status_code, 401
        )
        # New one still works.
        self.assertEqual(
            self.client.post("/api/v2/auth/refresh", json={"refresh_token": new_refresh}).status_code, 200
        )

    def test_logout_revokes_refresh(self) -> None:
        self._register()
        refresh = self._login().json()["data"]["refresh_token"]
        self.assertEqual(self.client.post("/api/v2/auth/logout", json={"refresh_token": refresh}).status_code, 200)
        self.assertEqual(
            self.client.post("/api/v2/auth/refresh", json={"refresh_token": refresh}).status_code, 401
        )

    def test_invalid_refresh_is_401(self) -> None:
        self.assertEqual(
            self.client.post("/api/v2/auth/refresh", json={"refresh_token": "nope"}).status_code, 401
        )


class RbacTests(AuthTestBase):
    def test_users_list_requires_admin(self) -> None:
        self._register()
        user_access = self._login().json()["data"]["access_token"]
        # No token -> 401
        self.assertEqual(self.client.get("/api/v2/users").status_code, 401)
        # User role -> 403
        self.assertEqual(
            self.client.get("/api/v2/users", headers=self._auth_header(user_access)).status_code, 403
        )
        # Admin -> 200
        self._make_admin()
        admin_access = self._login(email="admin@test.co", password="adminpass123").json()["data"]["access_token"]
        r = self.client.get("/api/v2/users", headers=self._auth_header(admin_access))
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.json()["data"]["pagination"]["total"], 2)

    def test_users_me(self) -> None:
        self._register()
        access = self._login().json()["data"]["access_token"]
        r = self.client.get("/api/v2/users/me", headers=self._auth_header(access))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["email"], "a@test.co")


if __name__ == "__main__":
    unittest.main()
