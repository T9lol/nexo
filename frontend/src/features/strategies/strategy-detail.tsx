import { MousePointerClick } from 'lucide-react';
import { type ReactNode } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  Skeleton,
  Switch,
} from '@/components/ui';
import { cn } from '@/lib/cn';
import { STRATEGY_TOGGLE_AVAILABLE } from '@/services';
import type { StrategyMetrics } from './strategy-model';
import { StrategyStatusBadge } from './strategy-status-badge';

interface StrategyDetailProps {
  strategy?: StrategyMetrics | null;
  manualOverride?: boolean;
  loading?: boolean;
}

function MetricTile({
  label,
  value,
  hint,
  unavailable,
}: {
  label: string;
  value?: ReactNode;
  hint?: string;
  unavailable?: boolean;
}) {
  return (
    <div className="flex flex-col rounded-lg border border-border p-3">
      <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      {unavailable ? (
        <>
          <span className="mt-1 text-lg font-semibold text-muted-foreground">
            &mdash;
          </span>
          <span className="text-[11px] text-muted-foreground">
            {hint ?? 'Not available'}
          </span>
        </>
      ) : (
        <>
          <span className="tabular mt-1 text-lg font-semibold">{value}</span>
          {hint ? (
            <span className="text-[11px] text-muted-foreground">{hint}</span>
          ) : null}
        </>
      )}
    </div>
  );
}

function signed(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
}

export function StrategyDetail({
  strategy,
  manualOverride = false,
  loading,
}: StrategyDetailProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Strategy Detail</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-10 w-40" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-28 w-full" />
          </div>
        ) : !strategy ? (
          <EmptyState
            icon={MousePointerClick}
            title="No strategy selected"
            description="Select a strategy to see its metrics and status."
          />
        ) : (
          <div className="flex flex-col gap-5">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-sm font-semibold text-muted-foreground">
                {strategy.name}
              </span>
              <div className="flex flex-col">
                <span className="font-semibold text-foreground">
                  Strategy {strategy.name}
                </span>
                <span className="text-xs text-muted-foreground">
                  {strategy.isActive
                    ? manualOverride
                      ? 'Active · manual override'
                      : 'Active · auto-selected'
                    : 'Standby · candidate'}
                </span>
              </div>
              <div className="ml-auto">
                <StrategyStatusBadge active={strategy.isActive} />
              </div>
            </div>

            <div className="rounded-lg border border-border bg-muted/30 p-4">
              <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                Performance Score
              </div>
              <div
                className={cn(
                  'tabular mt-1 text-3xl font-semibold tracking-tight',
                  strategy.adaptive >= 0 ? 'text-positive' : 'text-negative',
                )}
              >
                {signed(strategy.adaptive)}
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                Heuristic selection metric (reward × adaptive weight) — not
                trained ML/RL.
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <MetricTile
                label="Cumulative Reward"
                value={signed(strategy.score)}
              />
              <MetricTile
                label="Adaptive Weight"
                value={strategy.weight.toFixed(4)}
              />
              <MetricTile label="Updates" value={strategy.updates} />
              <MetricTile
                label="Total Trades"
                value={strategy.trades}
                hint="from recent trade feed"
              />
              <MetricTile
                label="PnL"
                unavailable
                hint="No per-strategy endpoint"
              />
              <MetricTile
                label="Win Rate"
                unavailable
                hint="No per-strategy endpoint"
              />
              <MetricTile
                label="Max Drawdown"
                unavailable
                hint="No per-strategy endpoint"
              />
            </div>

            <div className="flex items-center justify-between gap-3 rounded-lg border border-border p-3">
              <div className="flex flex-col">
                <span className="text-sm font-medium text-foreground">
                  Enabled
                </span>
                <span className="text-xs text-muted-foreground">
                  {STRATEGY_TOGGLE_AVAILABLE
                    ? 'Toggle this strategy on or off.'
                    : 'Per-strategy enable/disable is not available yet.'}
                </span>
              </div>
              <Switch
                disabled={!STRATEGY_TOGGLE_AVAILABLE}
                aria-label={`Enable strategy ${strategy.name}`}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
