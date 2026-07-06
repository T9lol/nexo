"""Phase 4 tests: bot catalog and subscription lifecycle (capital reservation)."""

import unittest

from tests.support import ApiTestBase


class BotCatalogTests(ApiTestBase):
    def test_bots_require_auth(self) -> None:
        self.assertEqual(self.client.get("/api/v2/bots").status_code, 401)

    def test_seeded_bots_listed(self) -> None:
        access = self.token()
        data = self.client.get("/api/v2/bots", headers=self.auth(access)).json()["data"]
        keys = {b["key"] for b in data["bots"]}
        self.assertEqual(keys, {"auto", "A", "B"})

    def test_bot_detail_404(self) -> None:
        access = self.token()
        self.assertEqual(
            self.client.get("/api/v2/bots/9999", headers=self.auth(access)).status_code, 404
        )


class SubscriptionTests(ApiTestBase):
    def _fund(self, access, amount=1000) -> None:
        self.client.post("/api/v2/wallet/deposit", json={"amount": amount}, headers=self.auth(access))

    def _first_bot_id(self, access) -> int:
        bots = self.client.get("/api/v2/bots", headers=self.auth(access)).json()["data"]["bots"]
        return bots[0]["id"]

    def test_subscribe_reserves_capital(self) -> None:
        access = self.token()
        self._fund(access, 1000)
        bot_id = self._first_bot_id(access)
        r = self.client.post(
            "/api/v2/subscriptions", json={"bot_id": bot_id, "capital": 400}, headers=self.auth(access)
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["data"]["status"], "active")
        self.assertEqual(r.json()["data"]["capital"], 400)
        # Capital is frozen in the wallet.
        wallet = self.client.get("/api/v2/wallet", headers=self.auth(access)).json()["data"]
        self.assertEqual(wallet["frozen_balance"], 400)
        self.assertEqual(wallet["available"], 600)

    def test_subscribe_insufficient_funds(self) -> None:
        access = self.token()
        self._fund(access, 100)
        bot_id = self._first_bot_id(access)
        r = self.client.post(
            "/api/v2/subscriptions", json={"bot_id": bot_id, "capital": 500}, headers=self.auth(access)
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "insufficient_funds")

    def test_subscribe_unknown_bot_404(self) -> None:
        access = self.token()
        self._fund(access, 1000)
        r = self.client.post(
            "/api/v2/subscriptions", json={"bot_id": 9999, "capital": 100}, headers=self.auth(access)
        )
        self.assertEqual(r.status_code, 404)

    def test_pause_resume_cycle(self) -> None:
        access = self.token()
        self._fund(access)
        bot_id = self._first_bot_id(access)
        sub_id = self.client.post(
            "/api/v2/subscriptions", json={"bot_id": bot_id, "capital": 200}, headers=self.auth(access)
        ).json()["data"]["id"]

        self.assertEqual(
            self.client.post(f"/api/v2/subscriptions/{sub_id}/pause", headers=self.auth(access)).json()["data"]["status"],
            "paused",
        )
        # Cannot pause again.
        self.assertEqual(
            self.client.post(f"/api/v2/subscriptions/{sub_id}/pause", headers=self.auth(access)).status_code, 409
        )
        self.assertEqual(
            self.client.post(f"/api/v2/subscriptions/{sub_id}/resume", headers=self.auth(access)).json()["data"]["status"],
            "active",
        )

    def test_cancel_releases_capital(self) -> None:
        access = self.token()
        self._fund(access, 1000)
        bot_id = self._first_bot_id(access)
        sub_id = self.client.post(
            "/api/v2/subscriptions", json={"bot_id": bot_id, "capital": 400}, headers=self.auth(access)
        ).json()["data"]["id"]

        r = self.client.post(f"/api/v2/subscriptions/{sub_id}/cancel", headers=self.auth(access))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["status"], "cancelled")
        # Capital released back to available.
        wallet = self.client.get("/api/v2/wallet", headers=self.auth(access)).json()["data"]
        self.assertEqual(wallet["frozen_balance"], 0)
        self.assertEqual(wallet["available"], 1000)
        # Cancelling again is a conflict.
        self.assertEqual(
            self.client.post(f"/api/v2/subscriptions/{sub_id}/cancel", headers=self.auth(access)).status_code, 409
        )

    def test_subscriptions_are_user_scoped(self) -> None:
        owner = self.token("owner@test.co")
        self._fund(owner)
        bot_id = self._first_bot_id(owner)
        sub_id = self.client.post(
            "/api/v2/subscriptions", json={"bot_id": bot_id, "capital": 100}, headers=self.auth(owner)
        ).json()["data"]["id"]

        other = self.token("other@test.co")
        # Another user cannot see or act on it.
        self.assertEqual(
            self.client.get(f"/api/v2/subscriptions/{sub_id}", headers=self.auth(other)).status_code, 404
        )
        self.assertEqual(
            self.client.post(f"/api/v2/subscriptions/{sub_id}/cancel", headers=self.auth(other)).status_code, 404
        )


if __name__ == "__main__":
    unittest.main()
