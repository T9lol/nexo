"""Railway deployment contract tests."""

from __future__ import annotations

import os
import threading
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import ui.dashboard as dash


class RailwayDeploymentTests(unittest.TestCase):
    def test_ping_is_minimal_and_public(self) -> None:
        response = TestClient(dash.app).get("/ping")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_database_initialization_does_not_delay_liveness(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def slow_init() -> None:
            started.set()
            release.wait(timeout=2)

        try:
            with patch("db.init_db", side_effect=slow_init):
                before = time.monotonic()
                with TestClient(dash.app) as client:
                    startup_seconds = time.monotonic() - before
                    self.assertTrue(started.wait(timeout=1))
                    self.assertLess(startup_seconds, 1)
                    self.assertEqual(client.get("/ping").json(), {"status": "ok"})
        finally:
            release.set()

    def test_python_entrypoint_uses_railway_port(self) -> None:
        with patch.dict(os.environ, {"PORT": "9123"}), patch(
            "uvicorn.run"
        ) as uvicorn_run:
            dash.run()

        uvicorn_run.assert_called_once_with(
            dash.app,
            host="0.0.0.0",
            port=9123,
            reload=False,
        )


if __name__ == "__main__":
    unittest.main()
