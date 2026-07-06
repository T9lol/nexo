"""Unit + HTTP tests for the Trade History API."""

import unittest

from fastapi.testclient import TestClient

import ui.dashboard as dash
from api.v1 import trade_derivations
from ui.providers import MockDashboardProvider


def _trades() -> list[dict]:
    return [
        {"id": "t3", "time": "2026-07-06T09:00:00+00:00", "strategy": "A",
         "action": "SELL", "symbol": "BTC", "price": 101.0, "amount": 1.0},
        {"id": "t2", "time": "2026-07-06T08:30:00+00:00", "strategy": "B",
         "action": "BUY", "symbol": "ETH", "price": 5.0, "amount": 4.0},
        {"id": "t1", "time": "2026-07-06T08:00:00+00:00", "strategy": "A",
         "action": "BUY", "symbol": "BTC", "price": 99.0, "amount": 2.0},
    ]


def _snapshot() -> dict:
    return {"updated_at": "2026-07-06T09:00:00+00:00", "trades": _trades()}


class TradeDerivationTests(unittest.TestCase):
    def test_enrich_adds_value(self) -> None:
        data = trade_derivations.trade_history(_snapshot(), page=1, page_size=10)
        first = data["trades"][0]
        self.assertEqual(first["value"], 101.0)  # 101 * 1

    def test_filter_by_symbol_side_strategy(self) -> None:
        snap = _snapshot()
        self.assertEqual(
            len(trade_derivations.trade_history(snap, symbol="BTC")["trades"]), 2
        )
        self.assertEqual(
            len(trade_derivations.trade_history(snap, side="buy")["trades"]), 2
        )
        self.assertEqual(
            len(trade_derivations.trade_history(snap, strategy="b")["trades"]), 1
        )

    def test_pagination(self) -> None:
        data = trade_derivations.trade_history(_snapshot(), page=2, page_size=2)
        self.assertEqual(data["pagination"], {"page": 2, "page_size": 2, "total": 3, "total_pages": 2})
        self.assertEqual(len(data["trades"]), 1)  # 3 total, last page has 1

    def test_details_and_missing(self) -> None:
        self.assertEqual(trade_derivations.trade_details(_snapshot(), "t2")["symbol"], "ETH")
        self.assertIsNone(trade_derivations.trade_details(_snapshot(), "nope"))

    def test_csv_has_header_and_rows(self) -> None:
        csv_text = trade_derivations.trades_csv(_snapshot(), symbol="BTC")
        lines = csv_text.strip().splitlines()
        self.assertEqual(lines[0], "id,time,strategy,action,symbol,price,amount,value")
        self.assertEqual(len(lines), 3)  # header + 2 BTC rows


class TradeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original = dash.provider
        provider = MockDashboardProvider(seed=7, interval=3600)
        provider.store.trades = _trades()
        dash.provider = provider
        self._ctx = TestClient(dash.app)
        self.client = self._ctx.__enter__()

    def tearDown(self) -> None:
        self._ctx.__exit__(None, None, None)
        dash.provider.stop()
        dash.provider = self._original

    def test_history_pagination_and_currency_meta(self) -> None:
        body = self.client.get("/api/v1/trade-history?page=1&page_size=2").json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["pagination"]["total"], 3)
        self.assertEqual(len(body["data"]["trades"]), 2)
        self.assertEqual(body["meta"]["currency"]["primary"], "MYR")

    def test_filter_side_valid_and_invalid(self) -> None:
        ok = self.client.get("/api/v1/trade-history?side=buy")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(len(ok.json()["data"]["trades"]), 2)
        bad = self.client.get("/api/v1/trade-history?side=hodl")
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()["error"]["code"], "validation_error")

    def test_page_validation(self) -> None:
        self.assertEqual(self.client.get("/api/v1/trade-history?page=0").status_code, 422)
        self.assertEqual(
            self.client.get("/api/v1/trade-history?page_size=999").status_code, 422
        )

    def test_trade_details_and_404(self) -> None:
        ok = self.client.get("/api/v1/trade-history/t1")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["data"]["value"], 198.0)  # 99 * 2
        self.assertEqual(self.client.get("/api/v1/trade-history/missing").status_code, 404)

    def test_csv_export(self) -> None:
        response = self.client.get("/api/v1/trade-history/export.csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["content-type"])
        self.assertIn("attachment", response.headers.get("content-disposition", ""))
        self.assertTrue(response.text.startswith("id,time,strategy,action,symbol,price,amount,value"))

    def test_documented_in_openapi(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/trade-history",
            "/api/v1/trade-history/export.csv",
            "/api/v1/trade-history/{trade_id}",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
