import type { DashboardState } from '@/services';

/**
 * Strategy metrics derived from the real `/api/state` snapshot. All fields here
 * come straight from the backend evaluator or the trade feed — none are
 * fabricated. Metrics the backend does not expose (PnL, win rate, drawdown) are
 * modelled by the strategy service as explicitly unavailable.
 */

export interface StrategyMetrics {
  name: string;
  /** Cumulative reward from the evaluator. */
  score: number;
  /** Adaptive weight. */
  weight: number;
  /** Number of evaluator updates. */
  updates: number;
  /** Performance score = the evaluator's selection metric (reward × weight). */
  adaptive: number;
  /** Trades attributed to this strategy in the recent trade feed. */
  trades: number;
  /** True when this is the currently selected/effective strategy. */
  isActive: boolean;
}

export interface StrategyView {
  strategies: StrategyMetrics[];
  activeName: string | null;
  /** Routing policy: 'auto' | strategy name. */
  policy: string;
  manualOverride: boolean;
}

export function deriveStrategies(
  state: DashboardState | null | undefined,
): StrategyView | null {
  if (!state) return null;

  const active = state.selected_strategy;

  const tradeCounts: Record<string, number> = {};
  for (const trade of state.trades) {
    tradeCounts[trade.strategy] = (tradeCounts[trade.strategy] ?? 0) + 1;
  }

  const strategies: StrategyMetrics[] = Object.entries(state.strategies).map(
    ([name, stat]) => ({
      name,
      score: stat.score,
      weight: stat.weight,
      updates: stat.updates,
      adaptive: stat.adaptive,
      trades: tradeCounts[name] ?? 0,
      isActive: name === active,
    }),
  );

  // Rank by performance score (the selection metric), highest first.
  strategies.sort((a, b) => b.adaptive - a.adaptive);

  return {
    strategies,
    activeName: active,
    policy: state.control?.strategy_policy ?? 'auto',
    manualOverride: state.control?.manual_override ?? false,
  };
}
