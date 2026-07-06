"""Phase 3 tests: wallet ledger, deposit/withdraw flow, admin approval, RBAC."""

import unittest

from tests.support import ApiTestBase


class WalletTests(ApiTestBase):
    def test_wallet_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/api/v2/wallet").status_code, 401)

    def test_new_wallet_is_zero(self) -> None:
        access = self.token()
        data = self.client.get("/api/v2/wallet", headers=self.auth(access)).json()["data"]
        self.assertEqual(data["balance"], 0)
        self.assertEqual(data["frozen_balance"], 0)
        self.assertEqual(data["available"], 0)
        self.assertEqual(data["currency"], "MYR")

    def test_deposit_increases_balance_and_logs_transaction(self) -> None:
        access = self.token()
        r = self.client.post("/api/v2/wallet/deposit", json={"amount": 500}, headers=self.auth(access))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["wallet"]["balance"], 500)
        self.assertEqual(r.json()["data"]["transaction"]["type"], "deposit")
        self.assertEqual(r.json()["data"]["transaction"]["status"], "completed")

        ledger = self.client.get("/api/v2/wallet/transactions", headers=self.auth(access)).json()["data"]
        self.assertEqual(ledger["pagination"]["total"], 1)
        self.assertEqual(ledger["transactions"][0]["amount"], 500)

    def test_deposit_must_be_positive(self) -> None:
        access = self.token()
        r = self.client.post("/api/v2/wallet/deposit", json={"amount": 0}, headers=self.auth(access))
        self.assertEqual(r.status_code, 422)  # pydantic gt=0

    def test_withdraw_freezes_funds(self) -> None:
        access = self.token()
        self.client.post("/api/v2/wallet/deposit", json={"amount": 1000}, headers=self.auth(access))
        r = self.client.post("/api/v2/wallet/withdraw", json={"amount": 300}, headers=self.auth(access))
        self.assertEqual(r.status_code, 200)
        wallet = r.json()["data"]["wallet"]
        self.assertEqual(wallet["balance"], 1000)  # not yet debited
        self.assertEqual(wallet["frozen_balance"], 300)
        self.assertEqual(wallet["available"], 700)
        self.assertEqual(r.json()["data"]["transaction"]["status"], "pending")

    def test_withdraw_insufficient_available(self) -> None:
        access = self.token()
        self.client.post("/api/v2/wallet/deposit", json={"amount": 100}, headers=self.auth(access))
        r = self.client.post("/api/v2/wallet/withdraw", json={"amount": 500}, headers=self.auth(access))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "insufficient_funds")


class WithdrawalApprovalTests(ApiTestBase):
    def _setup_withdrawal(self):
        access = self.token()
        self.client.post("/api/v2/wallet/deposit", json={"amount": 1000}, headers=self.auth(access))
        tx = self.client.post(
            "/api/v2/wallet/withdraw", json={"amount": 400}, headers=self.auth(access)
        ).json()["data"]["transaction"]
        admin = self.make_admin_token()
        return access, admin, tx["id"]

    def test_admin_lists_pending(self) -> None:
        _access, admin, tx_id = self._setup_withdrawal()
        r = self.client.get("/api/v2/wallet/withdrawals/pending", headers=self.auth(admin))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["count"], 1)
        self.assertEqual(r.json()["data"]["withdrawals"][0]["id"], tx_id)

    def test_pending_requires_admin(self) -> None:
        access, _admin, _tx = self._setup_withdrawal()
        self.assertEqual(self.client.get("/api/v2/wallet/withdrawals/pending").status_code, 401)
        self.assertEqual(
            self.client.get("/api/v2/wallet/withdrawals/pending", headers=self.auth(access)).status_code, 403
        )

    def test_approve_settles_funds(self) -> None:
        access, admin, tx_id = self._setup_withdrawal()
        r = self.client.post(f"/api/v2/wallet/withdrawals/{tx_id}/approve", headers=self.auth(admin))
        self.assertEqual(r.status_code, 200)
        wallet = r.json()["data"]["wallet"]
        self.assertEqual(wallet["balance"], 600)  # 1000 - 400
        self.assertEqual(wallet["frozen_balance"], 0)
        self.assertEqual(r.json()["data"]["transaction"]["status"], "approved")

    def test_reject_releases_funds(self) -> None:
        access, admin, tx_id = self._setup_withdrawal()
        r = self.client.post(f"/api/v2/wallet/withdrawals/{tx_id}/reject", headers=self.auth(admin))
        self.assertEqual(r.status_code, 200)
        wallet = r.json()["data"]["wallet"]
        self.assertEqual(wallet["balance"], 1000)  # unchanged
        self.assertEqual(wallet["frozen_balance"], 0)  # released
        self.assertEqual(r.json()["data"]["transaction"]["status"], "rejected")
        # Funds are available again.
        avail = self.client.get("/api/v2/wallet", headers=self.auth(access)).json()["data"]["available"]
        self.assertEqual(avail, 1000)

    def test_double_approve_is_conflict(self) -> None:
        _access, admin, tx_id = self._setup_withdrawal()
        self.client.post(f"/api/v2/wallet/withdrawals/{tx_id}/approve", headers=self.auth(admin))
        again = self.client.post(f"/api/v2/wallet/withdrawals/{tx_id}/approve", headers=self.auth(admin))
        self.assertEqual(again.status_code, 409)
        self.assertEqual(again.json()["error"]["code"], "conflict")


if __name__ == "__main__":
    unittest.main()
