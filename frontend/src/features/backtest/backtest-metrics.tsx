import { type ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { cn } from '@/lib/cn';
import type { BacktestMetrics } from './backtest-model';

function pct(fraction: number): string {
  return `${fraction >= 0 ? '+' : ''}${(fraction * 100).toFixed(2)}%`;
}

function MetricTile({
  label,
  value,
  hint,
  unavailable,
  tone,
}: {
  label: string;
  value?: ReactNode;
  hint?: string;
  unavailable?: boolean;
  tone?: 'positive' | 'negative';
}) {
  return (
    <div className="flex flex-col rounded-lg border border-border p-3">
      <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      {unavailable ? (
        <>
          <span className="mt-1 text-xl font-semibold text-muted-foreground">
            &mdash;
          </span>
          <span className="text-[11px] text-muted-foreground">
            {hint ?? 'Not available'}
          </span>
        </>
      ) : (
        <>
          <span
            className={cn(
              'tabular mt-1 text-xl font-semibold',
              tone === 'positive' && 'text-positive',
              tone === 'negative' && 'text-negative',
            )}
          >
            {value}
          </span>
          {hint ? (
            <span className="text-[11px] text-muted-foreground">{hint}</span>
          ) : null}
        </>
      )}
    </div>
  );
}

/** Performance metrics. Total Return and Max Drawdown are derived from the real
 * equity curve; CAGR, Sharpe, and Win Rate need inputs the backtest does not
 * provide and are honestly reported as unavailable. */
export function BacktestMetricsPanel({
  metrics,
}: {
  metrics: BacktestMetrics;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
          <MetricTile
            label="Total Return"
            value={pct(metrics.totalReturn)}
            tone={metrics.totalReturn >= 0 ? 'positive' : 'negative'}
          />
          <MetricTile
            label="Max Drawdown"
            value={pct(metrics.maxDrawdown)}
            tone="negative"
            hint="from equity curve"
          />
          <MetricTile
            label="CAGR"
            unavailable
            hint="No calendar time basis"
          />
          <MetricTile
            label="Sharpe Ratio"
            unavailable
            hint="No time / risk-free basis"
          />
          <MetricTile label="Win Rate" unavailable hint="No per-trade PnL" />
        </div>
      </CardContent>
    </Card>
  );
}
