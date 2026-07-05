import { describe, expect, it } from 'vitest';
import type { DashboardState, Trade } from '@/services';
import {
  derivePortfolio,
  filterHoldings,
  tradesForSymbol,
} from './portfolio-model';

function makeState(overrides?: Partial<DashboardState>): DashboardState {
  return {
    status: 'live',
    mode: 'UI-4 runtime',
    updated_at: '2026-07-06T00:00:00Z',
    market: { symbol: 'BTC', price: 100 },
    portfolio: { cash: 9500, asset: 5, equity: 10000, pnl: 25 },
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

describe('derivePortfolio', () => {
  it('returns null without state', () => {
    expect(derivePortfolio(null)).toBeNull();
  });

  it('derives crypto and cash holdings with allocations', () => {
    const result = derivePortfolio(makeState());
    expect(result).not.toBeNull();
    const holdings = result!.holdings;
    expect(holdings).toHaveLength(2);

    const btc = holdings.find((h) => h.symbol === 'BTC')!;
    expect(btc.quantity).toBe(5);
    expect(btc.valueUsd).toBe(500);
    expect(btc.allocation).toBeCloseTo(0.05);

    const cash = holdings.find((h) => h.symbol === 'USD')!;
    expect(cash.kind).toBe('cash');
    expect(cash.valueUsd).toBe(9500);
    expect(cash.allocation).toBeCloseTo(0.95);

    expect(result!.summary.totalUsd).toBe(10000);
    expect(result!.summary.holdingsCount).toBe(2);
  });

  it('omits the asset holding when nothing is held', () => {
    const result = derivePortfolio(
      makeState({ portfolio: { cash: 10000, asset: 0, equity: 10000, pnl: 0 } }),
    );
    expect(result!.holdings).toHaveLength(1);
    expect(result!.holdings[0]!.kind).toBe('cash');
  });
});

describe('filterHoldings', () => {
  const holdings = derivePortfolio(makeState())!.holdings;

  it('filters by free-text query', () => {
    expect(filterHoldings(holdings, 'bit', 'all').map((h) => h.symbol)).toEqual([
      'BTC',
    ]);
    expect(filterHoldings(holdings, 'usd', 'all').map((h) => h.symbol)).toEqual([
      'USD',
    ]);
  });

  it('filters by kind', () => {
    expect(filterHoldings(holdings, '', 'cash').map((h) => h.symbol)).toEqual([
      'USD',
    ]);
    expect(filterHoldings(holdings, '', 'crypto').map((h) => h.symbol)).toEqual([
      'BTC',
    ]);
  });
});

describe('tradesForSymbol', () => {
  const trades: Trade[] = [
    { id: '1', time: 't', strategy: 'A', action: 'BUY', symbol: 'BTC', price: 1, amount: 1 },
    { id: '2', time: 't', strategy: 'A', action: 'SELL', symbol: 'ETH', price: 1, amount: 1 },
  ];

  it('returns only matching-symbol trades', () => {
    expect(tradesForSymbol(trades, 'BTC').map((t) => t.id)).toEqual(['1']);
    expect(tradesForSymbol(undefined, 'BTC')).toEqual([]);
  });
});
