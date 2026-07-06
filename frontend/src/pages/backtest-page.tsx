import { Download, FlaskConical } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  PageHeader,
} from '@/components/ui';
import {
  BacktestDrawdownChart,
  BacktestEquityChart,
  BacktestForm,
  BacktestMetricsPanel,
  BacktestStatusPanel,
  backtestReportToCsv,
  deriveBacktestResult,
  type BacktestResult,
  type BacktestRunStatus,
} from '@/features/backtest';
import { TradeHistoryTable, downloadCsv } from '@/features/trades';
import { usePolling } from '@/hooks/use-polling';
import {
  BACKTEST_REPORT_EXPORT_AVAILABLE,
  getControl,
  runReferenceBacktest,
} from '@/services';

const DEFAULT_STRATEGIES = ['auto', 'A', 'B'];

const EXPORT_HINT = BACKTEST_REPORT_EXPORT_AVAILABLE
  ? undefined
  : 'Server report export is not available — exports results as CSV (client-side).';

export default function BacktestPage() {
  // Fetch control once for the available strategy policies.
  const { data: control } = usePolling(getControl, 3_600_000);
  const strategies = control?.allowed?.strategy_policy ?? DEFAULT_STRATEGIES;

  const [strategy, setStrategy] = useState('auto');
  const [running, setRunning] = useState(false);
  const [runStatus, setRunStatus] = useState<BacktestRunStatus>('idle');
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const controllerRef = useRef<AbortController | null>(null);
  useEffect(() => () => controllerRef.current?.abort(), []);

  const handleRun = async () => {
    if (running) return;
    const controller = new AbortController();
    controllerRef.current = controller;
    setRunning(true);
    setRunStatus('running');
    setError(null);
    try {
      const state = await runReferenceBacktest(strategy, controller.signal);
      if (controller.signal.aborted) return;
      setResult(deriveBacktestResult(state, strategy));
      setRunStatus('complete');
    } catch (caught) {
      if (controller.signal.aborted) return;
      setError((caught as Error).message);
      setRunStatus('error');
    } finally {
      if (!controller.signal.aborted) setRunning(false);
    }
  };

  const handleExport = () => {
    if (!result) return;
    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
    downloadCsv(`nexo-backtest-${stamp}.csv`, backtestReportToCsv(result));
  };

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Backtest Center"
        description="Run the reference backtest and review its results."
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            disabled={!result}
            title={EXPORT_HINT}
            aria-label="Export report"
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            Export Report
          </Button>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="flex min-w-0 flex-col gap-4 lg:col-span-1">
          <BacktestForm
            strategy={strategy}
            strategies={strategies}
            onStrategyChange={setStrategy}
            onRun={handleRun}
            running={running}
          />
          <BacktestStatusPanel
            status={runStatus}
            error={error}
            ranAt={result?.ranAt}
            strategy={result?.strategy}
          />
        </div>

        <div className="flex min-w-0 flex-col gap-4 lg:col-span-2">
          {result ? (
            <>
              <BacktestMetricsPanel metrics={result.metrics} />
              <BacktestEquityChart data={result.equityCurve} />
              <BacktestDrawdownChart data={result.drawdown} />
              <Card>
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <CardTitle>Backtest Trades</CardTitle>
                  <span className="tabular text-xs text-muted-foreground">
                    {result.trades.length}{' '}
                    {result.trades.length === 1 ? 'trade' : 'trades'}
                  </span>
                </CardHeader>
                <CardContent className="p-0">
                  <TradeHistoryTable
                    rows={result.trades}
                    emptyTitle="No trades in this backtest"
                    emptyDescription="The selected strategy produced no fills over the reference history."
                  />
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="py-12">
                <EmptyState
                  className="border-0"
                  icon={FlaskConical}
                  title="No backtest run yet"
                  description="Configure the strategy and run a backtest to see the equity curve, drawdown, performance metrics, and trades."
                />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
