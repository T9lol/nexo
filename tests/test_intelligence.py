import unittest

from intelligence import StrategyEvaluator, StrategyManager


class ProbeStrategy:
    def __init__(self) -> None:
        self.calls = 0

    def on_price(self, event: dict[str, object]) -> None:
        self.calls += 1


class IntelligenceTests(unittest.TestCase):
    def test_reward_updates_weight_and_selection(self) -> None:
        evaluator = StrategyEvaluator()
        evaluator.update("A", 30)
        evaluator.update("B", 24)

        self.assertGreater(evaluator.weights["A"], 1)
        self.assertEqual(evaluator.weighted_best(), "A")

    def test_manager_routes_only_to_selected_strategy(self) -> None:
        strategy_a = ProbeStrategy()
        strategy_b = ProbeStrategy()
        evaluator = StrategyEvaluator()
        evaluator.update("A", 30)
        evaluator.update("B", 24)
        manager = StrategyManager(
            {"A": strategy_a, "B": strategy_b}, evaluator
        )

        manager.on_price({"symbol": "BTC", "price": 100})

        self.assertEqual(strategy_a.calls, 1)
        self.assertEqual(strategy_b.calls, 0)


if __name__ == "__main__":
    unittest.main()
