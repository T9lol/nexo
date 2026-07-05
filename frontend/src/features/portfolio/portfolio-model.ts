import type { DashboardState, Trade } from '@/services';

/**
 * Portfolio holdings derived from the real `/api/state` snapshot. The engine
 * holds two real positions — the traded asset (e.g. BTC) and USD cash — so
 * these are computed, never fabricated. When there is no state, callers render
 * an empty/unavailable UI instead.
 */

export type HoldingKind = 'crypto' | 'cash';

export interface Holding {
  id: string;
  symbol: string;
  name: string;
  kind: HoldingKind;
  /** Units held (asset amount, or USD amount for cash). */
  quantity: number;
  /** USD price per unit (1 for cash). */
  price: number;
  /** USD value of the position. */
  valueUsd: number;
  /** Share of the total portfolio, 0..1. */
  allocation: number;
}

export interface PortfolioSummary {
  totalUsd: number;
  investedUsd: number;
  cashUsd: number;
  pnlUsd: number;
  holdingsCount: number;
}

export interface DerivedPortfolio {
  holdings: Holding[];
  summary: PortfolioSummary;
  updatedAt: string;
}

export function derivePortfolio(
  state: DashboardState | null | undefined,
): DerivedPortfolio | null {
  if (!state) return null;

  const price = state.market.price;
  const assetQty = state.portfolio.asset;
  const investedUsd = assetQty * price;
  const cashUsd = state.portfolio.cash;
  const totalUsd = state.portfolio.equity;
  const share = (value: number) => (totalUsd > 0 ? value / totalUsd : 0);

  const holdings: Holding[] = [];

  // Only include the traded asset when a position is actually held.
  if (assetQty > 0) {
    holdings.push({
      id: state.market.symbol,
      symbol: state.market.symbol,
      name: assetName(state.market.symbol),
      kind: 'crypto',
      quantity: assetQty,
      price,
      valueUsd: investedUsd,
      allocation: share(investedUsd),
    });
  }

  // Cash is always a real position in this simulator.
  holdings.push({
    id: 'USD-CASH',
    symbol: 'USD',
    name: 'Cash',
    kind: 'cash',
    quantity: cashUsd,
    price: 1,
    valueUsd: cashUsd,
    allocation: share(cashUsd),
  });

  return {
    holdings,
    summary: {
      totalUsd,
      investedUsd,
      cashUsd,
      pnlUsd: state.portfolio.pnl,
      holdingsCount: holdings.length,
    },
    updatedAt: state.updated_at,
  };
}

export type HoldingFilter = 'all' | HoldingKind;

/** Filter holdings by a free-text query (symbol/name) and a kind. */
export function filterHoldings(
  holdings: Holding[],
  query: string,
  kind: HoldingFilter,
): Holding[] {
  const q = query.trim().toLowerCase();
  return holdings.filter((holding) => {
    const matchesKind = kind === 'all' || holding.kind === kind;
    const matchesQuery =
      q === '' ||
      holding.symbol.toLowerCase().includes(q) ||
      holding.name.toLowerCase().includes(q);
    return matchesKind && matchesQuery;
  });
}

/** Recent trades for a given holding symbol (cash has none). */
export function tradesForSymbol(
  trades: Trade[] | undefined,
  symbol: string,
): Trade[] {
  if (!trades) return [];
  return trades.filter((trade) => trade.symbol === symbol);
}

const ASSET_NAMES: Record<string, string> = {
  BTC: 'Bitcoin',
  ETH: 'Ethereum',
};

function assetName(symbol: string): string {
  return ASSET_NAMES[symbol] ?? symbol;
}
