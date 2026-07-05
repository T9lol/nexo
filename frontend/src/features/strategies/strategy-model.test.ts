import { describe, expect, it } from 'vitest';
import type { DashboardState } from '@/services';
import { deriveStrategies } from './strategy-model';

function makeState(overrides?: Partial<DashboardState>): DashboardState {
  return {
    status: 'live',
    mode: 'UI-4 runtime',
    updated_at: '2026-07-06T00:00:00Z',
    market: { symbol: 'BTC', price: 100 },
    portfolio: { cash: 9500, asset: 5, equity: 10000, pnl: 25 },
    selected_strategy: 'A',
    strategies: {
      A: { score: 30, weight: 1.2, updates: 10, adaptive: 36 },
      B: { score: 20, weight: 1.0, updates: 5, adaptive: 20 },
    },
    trades: [
      { id: '1', time: 't', strategy: 'A', action: 'BUY', symbol: 'BTC', price: 1, amount: 1 },
      { id: '2', time: 't', strategy: 'A', action: 'SELL', symbol: 'BTC', price: 1, amount: 1 },
      { id: '3', time: 't', strategy: 'B', action: 'BUY', symbol: 'BTC', price: 1, amount: 1 },
    ],
    equity_curve: [],
    control: {
      trading_enabled: true,
      strategy_policy: 'auto',
      effective_strategy: 'A',
      manual_override: false,
      position_limit_enabled: true,
      mode: 'live',
      environment: 'local-simulation',
      allowed: { strategy_policy: ['auto', 'A', 'B'], mode: ['live', 'backtest'] },
    },
    ...overrides,
  };
}

describe('deriveStrategies', () => {
  it('returns null without state', () => {
    expect(deriveStrategies(null)).toBeNull();
  });

  it('derives metrics, active flag, and trade counts, ranked by performance', () => {
    const view = deriveStrategies(makeState())!;
    expect(view.strategies.map((s) => s.name)).toEqual(['A', 'B']); // adaptive desc

    const a = view.strategies.find((s) => s.name === 'A')!;
    expect(a.isActive).toBe(true);
    expect(a.adaptive).toBe(36);
    expect(a.trades).toBe(2);

    const b = view.strategies.find((s) => s.name === 'B')!;
    expect(b.isActive).toBe(false);
    expect(b.trades).toBe(1);

    expect(view.activeName).toBe('A');
    expect(view.manualOverride).toBe(false);
  });

  it('reflects a manual override policy', () => {
    const view = deriveStrategies(
      makeState({
        selected_strategy: 'B',
        control: {
          ...makeState().control,
          strategy_policy: 'B',
          manual_override: true,
          effective_strategy: 'B',
        },
      }),
    )!;
    expect(view.manualOverride).toBe(true);
    expect(view.strategies.find((s) => s.name === 'B')!.isActive).toBe(true);
  });
});
