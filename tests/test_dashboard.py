import unittest

from ui.dashboard import DashboardStore


class DashboardStoreTests(unittest.TestCase):
    def test_snapshot_contains_product_panels(self) -> None:
        state = DashboardStore(seed=42).snapshot()

        self.assertEqual(state["status"], "live")
        self.assertIn("portfolio", state)
        self.assertIn("strategies", state)
        self.assertIn("trades", state)
        self.assertIn("equity_curve", state)

    def test_seeded_ticks_are_reproducible(self) -> None:
        first = DashboardStore(seed=7)
        second = DashboardStore(seed=7)

        for _ in range(10):
            first.tick()
            second.tick()

        self.assertEqual(first.snapshot()["market"], second.snapshot()["market"])
        self.assertEqual(first.snapshot()["portfolio"], second.snapshot()["portfolio"])
        self.assertEqual(len(first.snapshot()["equity_curve"]), 11)


if __name__ == "__main__":
    unittest.main()
