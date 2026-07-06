"""Reward-weighted adaptive strategy evaluator."""


class StrategyEvaluator:
    def __init__(self) -> None:
        self.scores: dict[str, float] = {}
        self.weights: dict[str, float] = {}
        self.updates: dict[str, int] = {}

    def update(self, name: str, reward: float) -> None:
        reward = float(reward)
        self.scores[name] = self.scores.get(name, 0.0) + reward
        self.weights.setdefault(name, 1.0)
        self.updates[name] = self.updates.get(name, 0) + 1

        if reward > 0:
            self.weights[name] *= 1.05
        elif reward < 0:
            self.weights[name] *= 0.95
        self.weights[name] = min(10.0, max(0.1, self.weights[name]))

    def weighted_score(self, name: str) -> float:
        score = self.scores[name]
        weight = self.weights.get(name, 1.0)
        return score * weight if score >= 0 else score / weight

    def ranking(self) -> list[tuple[str, float]]:
        return sorted(
            ((name, self.weighted_score(name)) for name in self.scores),
            key=lambda item: item[1],
            reverse=True,
        )

    def weighted_best(self) -> str | None:
        ranking = self.ranking()
        return ranking[0][0] if ranking else None

    def report(self) -> None:
        print("\n===== ADAPTIVE STRATEGY STATE =====", flush=True)
        for name, adaptive_score in self.ranking():
            print(
                f"{name} | reward={self.scores[name]:+.2f} | "
                f"weight={self.weights[name]:.4f} | "
                f"adaptive_score={adaptive_score:+.2f} | "
                f"updates={self.updates[name]}",
                flush=True,
            )
        print(f"Selected Strategy: {self.weighted_best() or 'N/A'}", flush=True)
        print("===================================\n", flush=True)
