import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Button, Card, PageHeader } from '@/components/ui';
import { ConnectionStatus } from '@/features/dashboard/connection-status';
import {
  EmergencyStopCard,
  ExposurePanel,
  RiskAlertsPanel,
  RiskConfigCard,
  RiskOverviewCards,
  deriveRiskAlerts,
  deriveRiskOverview,
} from '@/features/risk';
import { usePolling } from '@/hooks/use-polling';
import {
  BACKEND_MAX_POSITION,
  getDashboardState,
  setPositionLimit,
  setTrading,
} from '@/services';

export default function RiskPage() {
  const {
    data: state,
    status,
    error,
    lastUpdated,
    refetch,
  } = usePolling(getDashboardState, 5000);

  const overview = useMemo(
    () => deriveRiskOverview(state, BACKEND_MAX_POSITION),
    [state],
  );
  const alerts = useMemo(
    () => (overview ? deriveRiskAlerts(overview) : []),
    [overview],
  );

  const [pending, setPending] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const runControl = async (action: () => Promise<unknown>) => {
    if (pending) return;
    setPending(true);
    setActionError(null);
    try {
      await action();
      refetch();
    } catch (caught) {
      setActionError((caught as Error).message);
    } finally {
      setPending(false);
    }
  };

  const loading = status === 'loading';
  const disconnected = status === 'error' && !state;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Risk Center"
        description="Exposure, live risk controls, and alerts."
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
              aria-label="Refresh risk data"
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
                {error?.message ?? 'The risk center could not load data.'}
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={refetch}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Retry
          </Button>
        </Card>
      ) : null}

      {actionError ? (
        <Card className="flex items-start gap-3 border-negative/40 bg-negative/5 p-4">
          <AlertTriangle
            className="mt-0.5 h-5 w-5 shrink-0 text-negative"
            aria-hidden="true"
          />
          <p className="text-sm text-muted-foreground">
            Control command failed: {actionError}
          </p>
        </Card>
      ) : null}

      <RiskOverviewCards overview={overview} loading={loading} />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <ExposurePanel overview={overview} loading={loading} />
        </div>
        <div className="min-w-0 lg:col-span-1">
          <RiskAlertsPanel alerts={alerts} loading={loading} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-1">
          <EmergencyStopCard
            tradingEnabled={overview?.tradingEnabled ?? true}
            pending={pending}
            onSetTrading={(enabled) =>
              void runControl(() => setTrading(enabled))
            }
          />
        </div>
        <div className="min-w-0 lg:col-span-2">
          <RiskConfigCard
            positionLimitEnabled={overview?.positionLimitEnabled ?? true}
            maxPosition={BACKEND_MAX_POSITION}
            pending={pending}
            onSetPositionLimit={(enabled) =>
              void runControl(() => setPositionLimit(enabled))
            }
          />
        </div>
      </div>
    </div>
  );
}
