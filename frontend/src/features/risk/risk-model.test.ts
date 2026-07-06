import { describe, expect, it } from 'vitest';
import type { DashboardState } from '@/services';
import {
  deriveRiskAlerts,
  deriveRiskOverview,
  exposureSlices,
} from './risk-model';

function makeState(overrides?: Partial<DashboardState>): DashboardState {
  return {
    status: 'live',
    mode: 'UI-4 runtime',
    updated_at: '2026-07-06T00:00:00Z',
    market: { symbol: 'BTC', price: 100 },
    portfolio: { cash: 9800, asset: 2, equity: 10000, pnl: 0 },
    selected_strategy: 'A',
    strategies: { A: { score: 1, weight: 1, updates: 1, adaptive: 1 } },
    trades: [],
    equity_curve: [],
    control: {
      trading_enabled: true,
      strategy_policy: 'auto',
      effective_strategy: 'A',
      manual_override: false,
      position_limit_enabled: true,
      mode: 'live',
      environment: 'local-simulation',
      allowed: { strategy_policy: ['auto'], mode: ['live'] },
    },
    ...overrides,
  };
}

describe('deriveRiskOverview', () => {
  it('returns null without state', () => {
    expect(deriveRiskOverview(null, 5)).toBeNull();
  });

  it('derives exposure and status from real state', () => {
    const overview = deriveRiskOverview(makeState(), 5)!;
    expect(overview.exposureValue).toBe(200); // 2 * 100
    expect(overview.exposurePct).toBeCloseTo(2);
    expect(overview.positionUnits).toBe(2);
    expect(overview.maxPosition).toBe(5);
    expect(overview.tradingEnabled).toBe(true);
    expect(overview.positionLimitEnabled).toBe(true);
  });
});

describe('exposureSlices', () => {
  it('includes market exposure and cash', () => {
    const slices = exposureSlices(deriveRiskOverview(makeState(), 5)!);
    expect(slices.map((s) => s.kind)).toEqual(['exposure', 'cash']);
  });
});

describe('deriveRiskAlerts', () => {
  const overview = (o?: Partial<DashboardState>) =>
    deriveRiskOverview(makeState(o), 5)!;

  it('has no alerts in a healthy state', () => {
    expect(deriveRiskAlerts(overview())).toEqual([]);
  });

  it('flags a trading pause as critical', () => {
    const alerts = deriveRiskAlerts(
      overview({
        control: { ...makeState().control, trading_enabled: false },
      }),
    );
    expect(alerts.find((a) => a.id === 'trading-paused')?.level).toBe(
      'critical',
    );
  });

  it('flags a disabled position-limit policy', () => {
    const alerts = deriveRiskAlerts(
      overview({
        control: { ...makeState().control, position_limit_enabled: false },
      }),
    );
    expect(alerts.some((a) => a.id === 'position-limit-off')).toBe(true);
  });

  it('flags a position at the limit', () => {
    const alerts = deriveRiskAlerts(
      overview({ portfolio: { cash: 9500, asset: 5, equity: 10000, pnl: 0 } }),
    );
    expect(alerts.some((a) => a.id === 'position-at-limit')).toBe(true);
  });
});
