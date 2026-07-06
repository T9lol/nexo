"""Shared test base for v2 API tests: isolated in-memory DB + auth helpers.

Not collected by ``unittest discover`` (filename does not match ``test*``).
"""

from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import ui.dashboard as dash
from api.config import get_settings
from api.v2 import auth_service
from api.v2.bots_service import seed_bots
from db.base import Base
from db.models import User, UserRole
from db.session import get_db

SECRET = "v2-tests-secret-key-0123456789abcdef01"


class ApiTestBase(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["NEXO_JWT_SECRET"] = SECRET
        get_settings.cache_clear()
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        # Seed the bot catalog into the isolated test DB.
        with self.Session() as seed_session:
            seed_bots(seed_session)
            seed_session.commit()

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

    # -- auth helpers ---------------------------------------------------------

    def register(self, email: str = "u@test.co", password: str = "password123"):
        return self.client.post(
            "/api/v2/auth/register", json={"email": email, "password": password}
        )

    def login(self, email: str = "u@test.co", password: str = "password123"):
        return self.client.post(
            "/api/v2/auth/login", json={"email": email, "password": password}
        )

    def token(self, email: str = "u@test.co", password: str = "password123") -> str:
        self.register(email, password)
        return self.login(email, password).json()["data"]["access_token"]

    def make_admin_token(
        self, email: str = "admin@test.co", password: str = "adminpass123"
    ) -> str:
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
        return self.login(email, password).json()["data"]["access_token"]

    @staticmethod
    def auth(access: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access}"}
