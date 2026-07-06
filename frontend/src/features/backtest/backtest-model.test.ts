import { describe, expect, it } from 'vitest';
import type { DashboardState } from '@/services';
import {
  backtestReportToCsv,
  computeDrawdown,
  deriveBacktestResult,
  maxDrawdown,
  totalReturn,
} from './backtest-model';

const EQUITY = [
  { time: '2026-07-06T00:00:00Z', value: 100 },
  { time: '2026-07-06T00:00:01Z', value: 110 },
  { time: '2026-07-06T00:00:02Z', value: 99 },
];

function makeState(): DashboardState {
  return {
    status: 'live',
    mode: 'backtest review',
    updated_at: '2026-07-06T00:00:02Z',
    market: { symbol: 'BTC', price: 99 },
    portfolio: { cash: 99, asset: 0, equity: 99, pnl: -1 },
    selected_strategy: 'A',
    strategies: { A: { score: 1, weight: 1, updates: 1, adaptive: 1 } },
    trades: [
      { id: 'bt-1', time: '2026-07-06T00:00:01Z', strategy: 'A', action: 'BUY', symbol: 'BTC', price: 98, amount: 1 },
    ],
    equity_curve: EQUITY,
    control: {
      trading_enabled: true,
      strategy_policy: 'auto',
      effective_strategy: 'A',
      manual_override: false,
      position_limit_enabled: true,
      mode: 'backtest',
      environment: 'local-simulation',
      allowed: { strategy_policy: ['auto', 'A', 'B'], mode: ['live', 'backtest'] },
    },
  };
}

describe('backtest metrics', () => {
  it('computes drawdown from the equity curve', () => {
    const dd = computeDrawdown(EQUITY).map((p) => p.value);
    expect(dd[0]).toBeCloseTo(0);
    expect(dd[1]).toBeCloseTo(0);
    expect(dd[2]).toBeCloseTo(-0.1); // 99 vs peak 110
  });

  it('computes max drawdown and total return', () => {
    expect(maxDrawdown(EQUITY)).toBeCloseTo(-0.1);
    expect(totalReturn(EQUITY)).toBeCloseTo(-0.01); // 99/100 - 1
  });

  it('derives a full result from the snapshot', () => {
    const result = deriveBacktestResult(makeState(), 'A');
    expect(result.initialCapital).toBe(100);
    expect(result.finalValue).toBe(99);
    expect(result.trades).toHaveLength(1);
    expect(result.strategy).toBe('A');
    expect(result.metrics.maxDrawdown).toBeCloseTo(-0.1);
  });
});

describe('backtestReportToCsv', () => {
  it('includes real metrics and marks unavailable ones as N/A', () => {
    const csv = backtestReportToCsv(deriveBacktestResult(makeState(), 'A'));
    expect(csv).toContain('NeXo Backtest Report');
    expect(csv).toContain('Total Return,');
    expect(csv).toContain('Max Drawdown,');
    expect(csv).toContain('CAGR,N/A');
    expect(csv).toContain('Sharpe Ratio,N/A');
    expect(csv).toContain('Win Rate,N/A');
    expect(csv).toContain('BUY,BTC');
  });
});
