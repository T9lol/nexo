import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Badge, Button, Card, PageHeader } from '@/components/ui';
import { ConnectionStatus } from '@/features/dashboard/connection-status';
import {
  StrategyComparisonChart,
  StrategyDetail,
  StrategyList,
  deriveStrategies,
} from '@/features/strategies';
import { usePolling } from '@/hooks/use-polling';
import { getDashboardState } from '@/services';

export default function StrategiesPage() {
  const {
    data: state,
    status,
    error,
    lastUpdated,
    refetch,
  } = usePolling(getDashboardState, 5000);

  const view = useMemo(() => deriveStrategies(state), [state]);
  const strategies = useMemo(() => view?.strategies ?? [], [view]);

  const [selectedName, setSelectedName] = useState<string | null>(null);

  // Default to the active strategy; recover if the selection disappears.
  useEffect(() => {
    if (strategies.length === 0) return;
    const active = strategies.find((strategy) => strategy.isActive);
    const fallback = active ?? strategies[0];
    if (!fallback) return;
    setSelectedName((current) =>
      current && strategies.some((strategy) => strategy.name === current)
        ? current
        : fallback.name,
    );
  }, [strategies]);

  const selected =
    strategies.find((strategy) => strategy.name === selectedName) ?? null;
  const loading = status === 'loading';
  const disconnected = status === 'error' && !state;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Strategy Center"
        description="Compare strategies, review scores, and inspect status."
        actions={
          <div className="flex items-center gap-3">
            <ConnectionStatus
              status={status}
              error={error}
              lastUpdated={lastUpdated}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={refetch}
              aria-label="Refresh strategies"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Refresh
            </Button>
          </div>
        }
      />

      {view ? (
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <span>Routing policy:</span>
          <Badge variant={view.manualOverride ? 'warning' : 'primary'}>
            {view.manualOverride
              ? `Manual override (${view.policy})`
              : 'Auto · adaptive'}
          </Badge>
        </div>
      ) : null}

      {disconnected ? (
        <Card className="flex flex-col gap-3 border-negative/40 bg-negative/5 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <AlertTriangle
              className="mt-0.5 h-5 w-5 shrink-0 text-negative"
              aria-hidden="true"
            />
            <div className="flex flex-col gap-0.5">
              <p className="text-sm font-medium text-foreground">
                Unable to reach the NeXo backend
              </p>
              <p className="text-sm text-muted-foreground">
                {error?.message ?? 'The strategy center could not load data.'}
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={refetch}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Retry
          </Button>
        </Card>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <StrategyList
            strategies={strategies}
            loading={loading}
            selectedName={selectedName}
            onSelect={setSelectedName}
          />
        </div>
        <div className="min-w-0 lg:col-span-1">
          <StrategyDetail
            strategy={selected}
            manualOverride={view?.manualOverride}
            loading={loading}
          />
        </div>
      </div>

      <StrategyComparisonChart
        strategies={strategies}
        activeName={view?.activeName ?? null}
        loading={loading}
      />
    </div>
  );
}
