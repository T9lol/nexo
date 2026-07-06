"""Unit tests for the pure Dashboard/Portfolio derivations.

Synthetic snapshots let us assert exact values (currency conversion, allocation
percentages, windowed PnL) independent of the live engine.
"""

import unittest
from datetime import datetime, timezone

from api.v1 import derivations

RATE = 4.0  # easy math: usd = myr / 4


def _snapshot_with_position() -> dict:
    return {
        "status": "live",
        "mode": "UI-4 runtime",
        "updated_at": "2026-07-06T09:00:00+00:00",
        "market": {"symbol": "BTC", "price": 100.0},
        "portfolio": {"cash": 5000.0, "asset": 50.0, "equity": 10000.0, "pnl": 250.0},
        "selected_strategy": "A",
        "strategies": {},
        "trades": [
            {"id": "t1", "symbol": "BTC", "action": "BUY", "price": 100.0,
             "amount": 1.0, "strategy": "A", "time": "2026-07-06T08:00:00+00:00"},
            {"id": "t2", "symbol": "ETH", "action": "SELL", "price": 5.0,
             "amount": 2.0, "strategy": "B", "time": "2026-07-06T07:00:00+00:00"},
        ],
        "equity_curve": [
            {"time": "2026-06-30T23:00:00+00:00", "value": 9000.0},
            {"time": "2026-07-05T23:00:00+00:00", "value": 10000.0},
            {"time": "2026-07-06T00:30:00+00:00", "value": 10100.0},
            {"time": "2026-07-06T09:00:00+00:00", "value": 10250.0},
        ],
    }


def _flat_snapshot() -> dict:
    return {
        "status": "live",
        "mode": "UI-4 runtime",
        "updated_at": "2026-07-06T09:00:00+00:00",
        "market": {"symbol": "BTC", "price": 100.0},
        "portfolio": {"cash": 10000.0, "asset": 0.0, "equity": 10000.0, "pnl": 0.0},
        "selected_strategy": "A",
        "trades": [],
        "equity_curve": [],
    }


NOW = datetime(2026, 7, 6, 9, 0, 0, tzinfo=timezone.utc)


class WindowedPnlTests(unittest.TestCase):
    def test_today_uses_prior_close_baseline(self) -> None:
        curve = _snapshot_with_position()["equity_curve"]
        result = derivations.windowed_pnl(curve, "day", now=NOW)
        self.assertEqual(result["baseline"], 10000.0)  # 2026-07-05 23:00 close
        self.assertEqual(result["amount"], 250.0)
        self.assertEqual(result["percent"], 2.5)

    def test_month_uses_prior_month_close(self) -> None:
        curve = _snapshot_with_position()["equity_curve"]
        result = derivations.windowed_pnl(curve, "month", now=NOW)
        self.assertEqual(result["baseline"], 9000.0)  # 2026-06-30 23:00 close
        self.assertEqual(result["amount"], 1250.0)
        self.assertEqual(result["percent"], 13.89)

    def test_empty_curve_is_zero(self) -> None:
        result = derivations.windowed_pnl([], "day", now=NOW)
        self.assertEqual(result["amount"], 0.0)
        self.assertEqual(result["percent"], 0.0)
        self.assertIsNone(result["baseline_at"])

    def test_all_history_inside_window_uses_earliest(self) -> None:
        curve = [
            {"time": "2026-07-06T01:00:00+00:00", "value": 10000.0},
            {"time": "2026-07-06T09:00:00+00:00", "value": 10300.0},
        ]
        result = derivations.windowed_pnl(curve, "day", now=NOW)
        self.assertEqual(result["baseline"], 10000.0)
        self.assertEqual(result["amount"], 300.0)


class DashboardSummaryTests(unittest.TestCase):
    def test_summary_fields_and_currency(self) -> None:
        data = derivations.dashboard_summary(_snapshot_with_position(), RATE, now=NOW)
        self.assertEqual(data["total_assets"], {"myr": 10000.0, "usd": 2500.0, "usd_is_approximate": True})
        self.assertEqual(data["today_pnl"]["myr"], 250.0)
        self.assertEqual(data["today_pnl"]["percent"], 2.5)
        self.assertEqual(data["monthly_pnl"]["myr"], 1250.0)
        self.assertEqual(data["active_strategy"], "A")
        self.assertEqual(data["system_status"]["status"], "live")
        self.assertEqual(data["system_status"]["environment"], None)  # no control block

    def test_system_status_reads_control(self) -> None:
        snap = _flat_snapshot()
        snap["control"] = {"mode": "backtest", "trading_enabled": False, "environment": "local-simulation"}
        data = derivations.dashboard_summary(snap, RATE, now=NOW)
        self.assertEqual(data["system_status"]["mode"], "backtest")
        self.assertFalse(data["system_status"]["trading_enabled"])
        self.assertEqual(data["system_status"]["environment"], "local-simulation")


class TradesAndCurveTests(unittest.TestCase):
    def test_equity_curve_limit_and_rounding(self) -> None:
        snap = _snapshot_with_position()
        data = derivations.equity_curve(snap, limit=2)
        self.assertEqual(data["count"], 2)
        self.assertEqual([p["value"] for p in data["points"]], [10100.0, 10250.0])

    def test_recent_trades_limit(self) -> None:
        data = derivations.recent_trades(_snapshot_with_position(), limit=1)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["trades"][0]["id"], "t1")


class PortfolioTests(unittest.TestCase):
    def test_summary(self) -> None:
        data = derivations.portfolio_summary(_snapshot_with_position(), RATE)
        self.assertEqual(data["total_value"]["myr"], 10000.0)
        self.assertEqual(data["cash"]["myr"], 5000.0)
        self.assertEqual(data["invested"]["myr"], 5000.0)  # 50 * 100
        self.assertEqual(data["holdings_count"], 1)

    def test_holdings_position(self) -> None:
        data = derivations.holdings(_snapshot_with_position(), RATE)
        self.assertEqual(data["count"], 1)
        holding = data["holdings"][0]
        self.assertEqual(holding["symbol"], "BTC")
        self.assertEqual(holding["quantity"], 50.0)
        self.assertEqual(holding["market_value"]["myr"], 5000.0)
        self.assertEqual(holding["allocation_percent"], 50.0)
        # Cost basis is not tracked by the engine -> honest null.
        self.assertIsNone(holding["average_cost"])
        self.assertIsNone(holding["unrealized_pnl"])

    def test_holdings_empty_when_flat(self) -> None:
        data = derivations.holdings(_flat_snapshot(), RATE)
        self.assertEqual(data["holdings"], [])
        self.assertEqual(data["count"], 0)

    def test_allocation_sums_to_100(self) -> None:
        data = derivations.allocation(_snapshot_with_position(), RATE)
        percents = {s["symbol"]: s["percent"] for s in data["allocation"]}
        self.assertEqual(percents["CASH"], 50.0)
        self.assertEqual(percents["BTC"], 50.0)
        self.assertEqual(round(sum(percents.values()), 2), 100.0)

    def test_asset_details_known_symbol_filters_trades(self) -> None:
        data = derivations.asset_details(_snapshot_with_position(), "btc", RATE)
        self.assertIsNotNone(data)
        self.assertEqual(data["symbol"], "BTC")
        self.assertEqual(data["quantity"], 50.0)
        self.assertEqual(data["market_value"]["myr"], 5000.0)
        # Only BTC trades, ETH filtered out.
        self.assertEqual([t["id"] for t in data["recent_trades"]], ["t1"])

    def test_asset_details_unknown_symbol_is_none(self) -> None:
        self.assertIsNone(
            derivations.asset_details(_snapshot_with_position(), "DOGE", RATE)
        )


if __name__ == "__main__":
    unittest.main()
