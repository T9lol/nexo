"""Trading signal generators."""

from .base import BaseStrategy
from .strategy_a import StrategyA
from .strategy_b import StrategyB

__all__ = ["BaseStrategy", "StrategyA", "StrategyB"]
