/**
 * Analytics service — PLACEHOLDER for time-bucketed PnL.
 *
 * The backend exposes all-time PnL via `/api/state` but not per-period
 * (today / this month) figures. Rather than fabricate values, these report
 * `available: false` so the UI can render an honest "not yet available" state.
 * Replace with a real endpoint call when the backend provides one.
 */

export interface PnlPeriod {
  available: boolean;
  /** PnL in USD when available; null otherwise. */
  value: number | null;
}

export interface PnlBreakdown {
  today: PnlPeriod;
  month: PnlPeriod;
}

const UNAVAILABLE: PnlPeriod = { available: false, value: null };

export function getPnlBreakdown(_signal?: AbortSignal): Promise<PnlBreakdown> {
  return Promise.resolve({ today: UNAVAILABLE, month: UNAVAILABLE });
}
