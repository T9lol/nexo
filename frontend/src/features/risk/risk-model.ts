import type { DashboardState } from '@/services';

/**
 * Risk state derived from the real `/api/state` snapshot. Exposure figures come
 * straight from the portfolio and market price; alerts are computed from real
 * runtime conditions (trading paused, policy disabled, position at limit,
 * backtest mode). Nothing here is fabricated.
 */

export interface RiskOverview {
  equity: number;
  exposureValue: number;
  exposurePct: number;
  cash: number;
  cashPct: number;
  positionUnits: number;
  price: number;
  maxPosition: number;
  tradingEnabled: boolean;
  positionLimitEnabled: boolean;
  mode: string;
}

export function deriveRiskOverview(
  state: DashboardState | null | undefined,
  maxPosition: number,
): RiskOverview | null {
  if (!state) return null;

  const price = state.market.price;
  const positionUnits = state.portfolio.asset;
  const exposureValue = positionUnits * price;
  const cash = state.portfolio.cash;
  const equity = state.portfolio.equity;
  const share = (value: number) => (equity > 0 ? (value / equity) * 100 : 0);

  return {
    equity,
    exposureValue,
    exposurePct: share(exposureValue),
    cash,
    cashPct: share(cash),
    positionUnits,
    price,
    maxPosition,
    tradingEnabled: state.control?.trading_enabled ?? true,
    positionLimitEnabled: state.control?.position_limit_enabled ?? true,
    mode: state.control?.mode ?? state.mode,
  };
}

export interface ExposureSlice {
  label: string;
  value: number;
  kind: 'exposure' | 'cash';
}

export function exposureSlices(overview: RiskOverview): ExposureSlice[] {
  const slices: ExposureSlice[] = [];
  if (overview.exposureValue > 0) {
    slices.push({
      label: 'Market exposure',
      value: overview.exposureValue,
      kind: 'exposure',
    });
  }
  slices.push({ label: 'Cash', value: overview.cash, kind: 'cash' });
  return slices;
}

export type AlertLevel = 'critical' | 'warning' | 'info';

export interface RiskAlert {
  id: string;
  level: AlertLevel;
  title: string;
  description: string;
}

/** Alerts derived from real runtime conditions (no dedicated backend feed). */
export function deriveRiskAlerts(overview: RiskOverview): RiskAlert[] {
  const alerts: RiskAlert[] = [];

  if (!overview.tradingEnabled) {
    alerts.push({
      id: 'trading-paused',
      level: 'critical',
      title: 'Trading paused',
      description:
        'Emergency stop is active — new strategy signals cannot produce fills.',
    });
  }

  if (!overview.positionLimitEnabled) {
    alerts.push({
      id: 'position-limit-off',
      level: 'warning',
      title: 'Position-limit policy disabled',
      description:
        'Positions may exceed the configured cap. Hard execution invariants still apply.',
    });
  }

  if (
    overview.positionLimitEnabled &&
    overview.positionUnits >= overview.maxPosition
  ) {
    alerts.push({
      id: 'position-at-limit',
      level: 'warning',
      title: 'Position at limit',
      description: `Holding ${overview.positionUnits} of ${overview.maxPosition} BTC.`,
    });
  }

  if (overview.mode === 'backtest') {
    alerts.push({
      id: 'backtest-mode',
      level: 'info',
      title: 'Backtest mode active',
      description: 'The engine is running a backtest review, not live trading.',
    });
  }

  return alerts;
}
