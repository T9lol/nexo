import { setRuntimeMode, setStrategyPolicy } from './control-service';
import { getDashboardState } from './dashboard-service';
import type { DashboardState } from './types';

/**
 * Backtest service.
 *
 * The backend provides ONE backtest mechanism: a deterministic reference replay
 * of a fixed price history, triggered via the runtime-mode endpoint. It is
 * driven only by the selected strategy policy — it does NOT accept a
 * configurable asset, date range, or initial capital. The flags/contracts below
 * let the UI keep those inputs honestly disabled and offer a client-side report
 * export, without sending ignored inputs to the backend or changing backend
 * algorithms.
 */

export const CONFIGURABLE_BACKTEST_AVAILABLE = false;
export const BACKTEST_REPORT_EXPORT_AVAILABLE = false;

export interface ConfigurableBacktestParams {
  strategy: string;
  asset: string;
  from: string;
  to: string;
  initialCapital: number;
}

/**
 * Placeholder for a future configurable backtest endpoint. Not available yet —
 * rejecting rather than silently ignoring asset/date/capital inputs.
 */
export function runConfigurableBacktest(
  _params: ConfigurableBacktestParams,
): Promise<DashboardState> {
  return Promise.reject(
    new Error(
      'Configurable backtest parameters (asset, date range, capital) are not supported by the backend.',
    ),
  );
}

/** Placeholder for a future server-side report export endpoint. */
export function exportBacktestReportViaBackend(): Promise<Blob> {
  return Promise.reject(
    new Error(
      'Server-side backtest report export is not available in this build.',
    ),
  );
}

/**
 * Run the backend reference backtest. Applies the strategy policy (which the
 * backend backtest respects), triggers the deterministic replay via the mode
 * endpoint, captures the resulting snapshot, then restores live mode.
 *
 * Asset / date range / initial capital are intentionally NOT sent — the backend
 * ignores them, so mapping them here would be dishonest.
 */
export async function runReferenceBacktest(
  policy: string,
  signal?: AbortSignal,
): Promise<DashboardState> {
  await setStrategyPolicy(policy, signal);
  await setRuntimeMode('backtest', signal);
  try {
    return await getDashboardState(signal);
  } finally {
    try {
      await setRuntimeMode('live');
    } catch {
      /* best-effort restore of live mode */
    }
  }
}
