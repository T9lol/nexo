import type { DashboardState, EquityPoint, Trade } from '@/services';

/**
 * Backtest result derived from the real reference-backtest snapshot. Equity and
 * trades come straight from the backend; drawdown, total return, and max
 * drawdown are exact functions of the real equity curve (no assumptions). CAGR,
 * Sharpe, and win rate are NOT derived here because they need inputs the
 * backtest does not provide (calendar time, risk-free rate, per-trade PnL).
 */

export interface DrawdownPoint {
  time: string;
  /** Drawdown as a fraction (<= 0). */
  value: number;
}

export interface BacktestMetrics {
  /** Total return as a fraction (final / initial - 1). */
  totalReturn: number;
  /** Worst peak-to-trough as a fraction (<= 0). */
  maxDrawdown: number;
}

export interface BacktestResult {
  equityCurve: EquityPoint[];
  drawdown: DrawdownPoint[];
  trades: Trade[];
  initialCapital: number;
  finalValue: number;
  metrics: BacktestMetrics;
  strategy: string;
  ranAt: string;
}

export function computeDrawdown(equity: EquityPoint[]): DrawdownPoint[] {
  let peak = -Infinity;
  return equity.map((point) => {
    peak = Math.max(peak, point.value);
    const value = peak > 0 ? point.value / peak - 1 : 0;
    return { time: point.time, value };
  });
}

export function maxDrawdown(equity: EquityPoint[]): number {
  return computeDrawdown(equity).reduce(
    (min, point) => Math.min(min, point.value),
    0,
  );
}

export function totalReturn(equity: EquityPoint[]): number {
  const first = equity[0]?.value;
  const last = equity[equity.length - 1]?.value;
  if (first === undefined || last === undefined || first === 0) return 0;
  return last / first - 1;
}

export function deriveBacktestResult(
  state: DashboardState,
  strategy: string,
): BacktestResult {
  const equityCurve = state.equity_curve;
  const initialCapital = equityCurve[0]?.value ?? 0;
  const finalValue =
    equityCurve[equityCurve.length - 1]?.value ?? initialCapital;
  return {
    equityCurve,
    drawdown: computeDrawdown(equityCurve),
    trades: state.trades,
    initialCapital,
    finalValue,
    metrics: {
      totalReturn: totalReturn(equityCurve),
      maxDrawdown: maxDrawdown(equityCurve),
    },
    strategy,
    ranAt: new Date().toISOString(),
  };
}

function csvCell(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

/** Client-side report: real params/metrics/trades; unavailable metrics as N/A. */
export function backtestReportToCsv(result: BacktestResult): string {
  const pct = (fraction: number) => `${(fraction * 100).toFixed(4)}%`;
  const lines = [
    'NeXo Backtest Report',
    `Generated,${new Date(result.ranAt).toISOString()}`,
    `Strategy,${result.strategy}`,
    `Asset,BTC`,
    `Initial Capital,${result.initialCapital}`,
    `Final Value,${result.finalValue}`,
    `Total Return,${pct(result.metrics.totalReturn)}`,
    `Max Drawdown,${pct(result.metrics.maxDrawdown)}`,
    'CAGR,N/A',
    'Sharpe Ratio,N/A',
    'Win Rate,N/A',
    '',
    'Time,Side,Asset,Quantity,Price',
  ];
  for (const trade of result.trades) {
    lines.push(
      [
        new Date(trade.time).toISOString(),
        trade.action,
        trade.symbol,
        String(trade.amount),
        String(trade.price),
      ]
        .map(csvCell)
        .join(','),
    );
  }
  return lines.join('\n');
}
