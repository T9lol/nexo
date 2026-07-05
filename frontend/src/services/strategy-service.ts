/**
 * Strategy service contracts.
 *
 * The backend exposes per-strategy score / weight / updates / adaptive metrics
 * through `/api/state`, but it does NOT expose per-strategy PnL, win rate, or
 * drawdown, and there is NO per-strategy enable/disable endpoint. These typed
 * contracts model those capabilities so the UI can render honest
 * "unavailable" / "disabled" states today and swap in real calls when the
 * backend provides them — without fabricating values or changing backend
 * trading logic.
 */

export interface MetricValue {
  available: boolean;
  /** Present only when `available` is true. */
  value: number | null;
}

const UNAVAILABLE: MetricValue = { available: false, value: null };

export interface StrategyExtendedMetrics {
  pnl: MetricValue;
  winRate: MetricValue;
  drawdown: MetricValue;
}

/**
 * Extended per-strategy metrics. No backend endpoint exists yet, so this always
 * reports unavailable rather than inventing values.
 */
export function getStrategyExtendedMetrics(
  _name: string,
): Promise<StrategyExtendedMetrics> {
  return Promise.resolve({
    pnl: UNAVAILABLE,
    winRate: UNAVAILABLE,
    drawdown: UNAVAILABLE,
  });
}

/** Whether per-strategy enable/disable is supported by the backend. */
export const STRATEGY_TOGGLE_AVAILABLE = false;

export interface StrategyToggleResult {
  name: string;
  enabled: boolean;
}

/**
 * Placeholder contract for a future enable/disable endpoint. Until one exists
 * the UI must keep the control disabled; calling this rejects rather than
 * pretending to mutate state.
 */
export function setStrategyEnabled(
  name: string,
  _enabled: boolean,
): Promise<StrategyToggleResult> {
  return Promise.reject(
    new Error(
      `Enable/disable for strategy "${name}" is not available in this build.`,
    ),
  );
}
