import type { Trade } from './types';

/**
 * Trade service contracts.
 *
 * The backend exposes executed fills via `/api/trades` (id, time, strategy,
 * action, symbol, price, amount). It does NOT expose per-trade fee or realized
 * PnL, a richer status lifecycle, server-side pagination, or a CSV export
 * endpoint. These typed flags/contracts let the UI render honest
 * "unavailable" / "disabled" states and fall back to client-side behaviour
 * (pagination, CSV of already-loaded rows) without fabricating values or
 * changing backend business logic.
 */

export const TRADE_FEE_AVAILABLE = false;
export const TRADE_REALIZED_PNL_AVAILABLE = false;
export const TRADE_SERVER_PAGINATION_AVAILABLE = false;
export const TRADE_CSV_EXPORT_AVAILABLE = false;

/**
 * Every record from `/api/trades` is an executed fill, so the only status the
 * backend represents is "filled". A richer lifecycle (pending/cancelled/
 * rejected) is not available.
 */
export type TradeStatus = 'filled';

export function tradeStatus(_trade: Trade): TradeStatus {
  return 'filled';
}

export interface TradePageRequest {
  page: number;
  pageSize: number;
}

/**
 * Placeholder for a future server-side paginated trades endpoint. Not available
 * yet — the UI paginates the loaded rows client-side instead.
 */
export function getTradesPage(_request: TradePageRequest): Promise<Trade[]> {
  return Promise.reject(
    new Error('Server-side trade pagination is not available in this build.'),
  );
}

/**
 * Placeholder for a future backend CSV export endpoint. Not available yet — the
 * UI exports the currently loaded/filtered rows client-side instead.
 */
export function exportTradesCsvViaBackend(): Promise<Blob> {
  return Promise.reject(
    new Error('Server-side CSV export is not available in this build.'),
  );
}
