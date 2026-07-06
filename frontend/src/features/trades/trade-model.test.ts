import { describe, expect, it } from 'vitest';
import type { Trade } from '@/services';
import {
  EMPTY_FILTERS,
  filterTrades,
  paginate,
  tradesToCsv,
  uniqueAssets,
} from './trade-model';

const TRADES: Trade[] = [
  {
    id: '1',
    time: '2026-07-01T12:00:00Z',
    strategy: 'A',
    action: 'BUY',
    symbol: 'BTC',
    price: 100,
    amount: 1,
  },
  {
    id: '2',
    time: '2026-07-10T12:00:00Z',
    strategy: 'B',
    action: 'SELL',
    symbol: 'ETH',
    price: 50,
    amount: 2,
  },
  {
    id: '3',
    time: '2026-07-20T12:00:00Z',
    strategy: 'A',
    action: 'BUY',
    symbol: 'BTC',
    price: 110,
    amount: 1,
  },
];

describe('uniqueAssets', () => {
  it('returns sorted distinct symbols', () => {
    expect(uniqueAssets(TRADES)).toEqual(['BTC', 'ETH']);
  });
});

describe('filterTrades', () => {
  it('returns all with empty filters', () => {
    expect(filterTrades(TRADES, EMPTY_FILTERS)).toHaveLength(3);
  });

  it('filters by side', () => {
    const buys = filterTrades(TRADES, { ...EMPTY_FILTERS, side: 'BUY' });
    expect(buys.map((t) => t.id)).toEqual(['1', '3']);
  });

  it('filters by asset', () => {
    const eth = filterTrades(TRADES, { ...EMPTY_FILTERS, asset: 'ETH' });
    expect(eth.map((t) => t.id)).toEqual(['2']);
  });

  it('filters by free-text query', () => {
    expect(
      filterTrades(TRADES, { ...EMPTY_FILTERS, query: 'eth' }).map((t) => t.id),
    ).toEqual(['2']);
  });

  it('filters by date range (wide margins for tz safety)', () => {
    const mid = filterTrades(TRADES, {
      ...EMPTY_FILTERS,
      from: '2026-07-05',
      to: '2026-07-15',
    });
    expect(mid.map((t) => t.id)).toEqual(['2']);
  });
});

describe('paginate', () => {
  it('slices items and reports totals', () => {
    const page1 = paginate(TRADES, 1, 2);
    expect(page1.items.map((t) => t.id)).toEqual(['1', '2']);
    expect(page1.totalPages).toBe(2);

    const page2 = paginate(TRADES, 2, 2);
    expect(page2.items.map((t) => t.id)).toEqual(['3']);

    // Out-of-range page is clamped.
    expect(paginate(TRADES, 99, 2).page).toBe(2);
  });
});

describe('tradesToCsv', () => {
  it('includes real fields and marks fee/PnL as N/A', () => {
    const csv = tradesToCsv(TRADES);
    const lines = csv.split('\n');
    expect(lines[0]).toContain(
      'Date/Time,Side,Asset,Quantity,Price,Fee,Realized PnL,Status',
    );
    expect(lines).toHaveLength(4);
    expect(lines[1]).toContain('BUY');
    expect(lines[1]).toContain('BTC');
    expect(lines[1]).toContain('N/A'); // fee + realized PnL
    expect(lines[1]).toContain('Filled');
  });
});
