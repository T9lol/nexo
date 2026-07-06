import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Button, Card, PageHeader } from '@/components/ui';
import { ConnectionStatus } from '@/features/dashboard/connection-status';
import {
  AllocationPieCard,
  AssetDetailPanel,
  AssetSummary,
  HoldingsCard,
  PortfolioValueCard,
  derivePortfolio,
} from '@/features/portfolio';
import { usePolling } from '@/hooks/use-polling';
import { getDashboardState, getUsdMyrRate } from '@/services';

export default function PortfolioPage() {
  const {
    data: state,
    status,
    error,
    lastUpdated,
    refetch,
  } = usePolling(getDashboardState, 5000);
  const { data: rate } = usePolling(getUsdMyrRate, 300000);

  const portfolio = useMemo(() => derivePortfolio(state), [state]);
  const holdings = useMemo(() => portfolio?.holdings ?? [], [portfolio]);

  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Keep a valid selection: default to the first holding, and recover if the
  // selected asset disappears.
  useEffect(() => {
    const first = holdings[0];
    if (!first) return;
    setSelectedId((current) =>
      current && holdings.some((holding) => holding.id === current)
        ? current
        : first.id,
    );
  }, [holdings]);

  const selected =
    holdings.find((holding) => holding.id === selectedId) ?? null;
  const loading = status === 'loading';
  const disconnected = status === 'error' && !state;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Portfolio"
        description="Holdings, allocation, and value over time."
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
              aria-label="Refresh portfolio"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Refresh
            </Button>
          </div>
        }
      />

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
                {error?.message ?? 'The portfolio could not load live data.'}
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={refetch}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Retry
          </Button>
        </Card>
      ) : null}

      <AssetSummary
        summary={portfolio?.summary}
        rate={rate}
        loading={loading}
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <HoldingsCard
            holdings={holdings}
            loading={loading}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>
        <div className="min-w-0 lg:col-span-1">
          <AllocationPieCard holdings={holdings} loading={loading} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <PortfolioValueCard data={state?.equity_curve} loading={loading} />
        </div>
        <div className="min-w-0 lg:col-span-1">
          <AssetDetailPanel
            holding={selected}
            trades={state?.trades}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
}
