/**
 * Risk service contracts.
 *
 * The backend exposes two real risk controls (trading pause and the
 * position-limit policy toggle, wired via control-service). It does NOT expose
 * a configurable max-position value, daily-loss / drawdown limits, stop-loss /
 * take-profit settings, a "save risk config" endpoint, or a risk-alerts feed.
 * These typed flags/contracts let the UI keep those inputs honestly disabled
 * and derive alerts client-side, without inventing values or changing the
 * backend risk engine.
 */

/** Max position (BTC) enforced by the backend RiskEngine. Fixed, not settable. */
export const BACKEND_MAX_POSITION = 5;

export const RISK_CONFIG_SAVE_AVAILABLE = false;
export const RISK_ALERTS_FEED_AVAILABLE = false;

export interface RiskConfiguration {
  maxPositionSize: number;
  dailyLossLimit: number | null;
  maxDrawdownLimit: number | null;
  stopLoss: number | null;
  takeProfit: number | null;
}

/**
 * Placeholder for a future risk-configuration endpoint. Not available yet —
 * rejecting rather than pretending to persist limits the backend cannot honour.
 */
export function saveRiskConfiguration(
  _config: RiskConfiguration,
): Promise<RiskConfiguration> {
  return Promise.reject(
    new Error(
      'Saving risk limits (max position, daily loss, drawdown, stop-loss, take-profit) is not supported by the backend.',
    ),
  );
}
