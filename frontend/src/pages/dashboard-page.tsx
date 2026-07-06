import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button, Card, PageHeader } from '@/components/ui';
import {
  ActiveStrategyCard,
  ConnectionStatus,
  EquityCurveCard,
  PnlCard,
  RecentTradesCard,
  SystemStatusCard,
  TotalAssetsCard,
} from '@/features/dashboard';
import { usePolling } from '@/hooks/use-polling';
import { getDashboardState, getPnlBreakdown, getUsdMyrRate } from '@/services';

export default function DashboardPage() {
  const {
    data: state,
    status,
    error,
    lastUpdated,
    refetch,
  } = usePolling(getDashboardState, 5000);
  const { data: rate } = usePolling(getUsdMyrRate, 300000);
  const { data: pnl } = usePolling(getPnlBreakdown, 300000);

  const loading = status === 'loading';
  const disconnected = status === 'error' && !state;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Dashboard"
        description="Live overview of assets, performance, and engine status."
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
              aria-label="Refresh dashboard"
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
                {error?.message ?? 'The dashboard could not load live data.'}
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={refetch}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Retry
          </Button>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <TotalAssetsCard
          equityUsd={state?.portfolio.equity}
          rate={rate}
          loading={loading}
        />
        <PnlCard
          label="Today's PnL"
          period={pnl?.today}
          loading={loading || !pnl}
        />
        <PnlCard
          label="Monthly PnL"
          period={pnl?.month}
          loading={loading || !pnl}
        />
        <ActiveStrategyCard state={state} loading={loading} />
        <SystemStatusCard state={state} loading={loading} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <EquityCurveCard data={state?.equity_curve} loading={loading} />
        </div>
        <div className="lg:col-span-1">
          <RecentTradesCard trades={state?.trades} loading={loading} />
        </div>
      </div>
    </div>
  );
}
