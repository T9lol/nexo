"""Tests for centralized API configuration (:mod:`api.config`)."""

import os
import unittest

from api.config import get_settings


class ApiConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        # Isolate: snapshot and strip NEXO_* so defaults are deterministic.
        self._saved = {k: v for k, v in os.environ.items() if k.startswith("NEXO_")}
        for key in list(os.environ):
            if key.startswith("NEXO_"):
                del os.environ[key]
        get_settings.cache_clear()

    def tearDown(self) -> None:
        for key in list(os.environ):
            if key.startswith("NEXO_"):
                del os.environ[key]
        os.environ.update(self._saved)
        get_settings.cache_clear()

    def test_conservative_defaults(self) -> None:
        settings = get_settings()
        self.assertEqual(settings.api_v1_prefix, "/api/v1")
        self.assertEqual(settings.cors_origins, [])  # no cross-origin by default
        self.assertFalse(settings.cors_allow_credentials)
        self.assertFalse(settings.auth_configured)  # JWT ready but inert
        self.assertEqual(settings.log_level, "INFO")
        self.assertFalse(settings.log_requests)

    def test_environment_overrides(self) -> None:
        os.environ["NEXO_CORS_ORIGINS"] = "http://a.test, http://b.test"
        os.environ["NEXO_CORS_ALLOW_CREDENTIALS"] = "true"
        os.environ["NEXO_ENV"] = "staging"
        os.environ["NEXO_JWT_SECRET"] = "s3cret"
        os.environ["NEXO_LOG_REQUESTS"] = "on"
        get_settings.cache_clear()

        settings = get_settings()
        self.assertEqual(settings.cors_origins, ["http://a.test", "http://b.test"])
        self.assertTrue(settings.cors_allow_credentials)
        self.assertEqual(settings.environment, "staging")
        self.assertTrue(settings.auth_configured)
        self.assertTrue(settings.log_requests)

    def test_settings_are_cached(self) -> None:
        self.assertIs(get_settings(), get_settings())

    def test_never_wildcard_by_default(self) -> None:
        self.assertNotIn("*", get_settings().cors_origins)


if __name__ == "__main__":
    unittest.main()
