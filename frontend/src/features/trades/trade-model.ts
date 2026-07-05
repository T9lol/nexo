import type { Trade } from '@/services';

export interface TradeFilters {
  query: string;
  asset: string; // 'all' | symbol
  side: string; // 'all' | 'BUY' | 'SELL'
  status: string; // 'all' | 'filled'
  from: string; // yyyy-mm-dd or ''
  to: string; // yyyy-mm-dd or ''
}

export const EMPTY_FILTERS: TradeFilters = {
  query: '',
  asset: 'all',
  side: 'all',
  status: 'all',
  from: '',
  to: '',
};

/** Unique asset symbols present in the data, sorted. */
export function uniqueAssets(trades: Trade[]): string[] {
  return [...new Set(trades.map((trade) => trade.symbol))].sort();
}

/** Apply search + asset/side/status/date-range filters (all client-side). */
export function filterTrades(trades: Trade[], filters: TradeFilters): Trade[] {
  const query = filters.query.trim().toLowerCase();
  const fromMs = filters.from
    ? new Date(`${filters.from}T00:00:00`).getTime()
    : null;
  const toMs = filters.to
    ? new Date(`${filters.to}T23:59:59.999`).getTime()
    : null;

  return trades.filter((trade) => {
    if (filters.asset !== 'all' && trade.symbol !== filters.asset) return false;
    if (filters.side !== 'all' && trade.action !== filters.side) return false;
    // The only real status is "filled"; the filter never fabricates others.
    if (filters.status !== 'all' && filters.status !== 'filled') return false;

    const time = new Date(trade.time).getTime();
    if (fromMs !== null && time < fromMs) return false;
    if (toMs !== null && time > toMs) return false;

    if (query) {
      const haystack =
        `${trade.symbol} ${trade.strategy} ${trade.action} ${trade.id}`.toLowerCase();
      if (!haystack.includes(query)) return false;
    }
    return true;
  });
}

export interface Page<T> {
  items: T[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

/** Client-side pagination (server-side pagination is not available). */
export function paginate<T>(
  items: T[],
  page: number,
  pageSize: number,
): Page<T> {
  const totalItems = items.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    page: safePage,
    pageSize,
    totalItems,
    totalPages,
  };
}

const CSV_HEADERS = [
  'Date/Time',
  'Side',
  'Asset',
  'Quantity',
  'Price',
  'Fee',
  'Realized PnL',
  'Status',
  'Strategy',
];

function csvCell(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

/**
 * Build a CSV from real trade fields. Fee and Realized PnL are written as "N/A"
 * because the backend does not provide them — never fabricated.
 */
export function tradesToCsv(trades: Trade[]): string {
  const lines = [CSV_HEADERS.join(',')];
  for (const trade of trades) {
    lines.push(
      [
        new Date(trade.time).toISOString(),
        trade.action,
        trade.symbol,
        String(trade.amount),
        String(trade.price),
        'N/A',
        'N/A',
        'Filled',
        trade.strategy,
      ]
        .map(csvCell)
        .join(','),
    );
  }
  return lines.join('\n');
}

/** Trigger a client-side CSV download (browser only). */
export function downloadCsv(filename: string, content: string): void {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
