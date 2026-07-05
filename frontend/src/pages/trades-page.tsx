import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  PageHeader,
} from '@/components/ui';
import { ConnectionStatus } from '@/features/dashboard/connection-status';
import {
  EMPTY_FILTERS,
  TradeFiltersBar,
  TradeHistoryTable,
  TradePagination,
  downloadCsv,
  filterTrades,
  paginate,
  tradesToCsv,
  uniqueAssets,
  type TradeFilters,
} from '@/features/trades';
import { usePolling } from '@/hooks/use-polling';
import {
  getTrades,
  TRADE_CSV_EXPORT_AVAILABLE,
  TRADE_SERVER_PAGINATION_AVAILABLE,
} from '@/services';

const EXPORT_HINT = TRADE_CSV_EXPORT_AVAILABLE
  ? undefined
  : 'Server export is not available — exports the filtered rows as CSV (client-side).';

export default function TradesPage() {
  const {
    data: trades,
    status,
    error,
    lastUpdated,
    refetch,
  } = usePolling(getTrades, 5000);

  const allTrades = useMemo(() => trades ?? [], [trades]);

  const [filters, setFilters] = useState<TradeFilters>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const assets = useMemo(() => uniqueAssets(allTrades), [allTrades]);
  const filtered = useMemo(
    () => filterTrades(allTrades, filters),
    [allTrades, filters],
  );
  const pageData = useMemo(
    () => paginate(filtered, page, pageSize),
    [filtered, page, pageSize],
  );

  // Keep the current page in range when the result set shrinks.
  useEffect(() => {
    if (page > pageData.totalPages) setPage(pageData.totalPages);
  }, [page, pageData.totalPages]);

  const updateFilters = (patch: Partial<TradeFilters>) => {
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1);
  };
  const resetFilters = () => {
    setFilters(EMPTY_FILTERS);
    setPage(1);
  };

  const handleExport = () => {
    const stamp = new Date()
      .toISOString()
      .slice(0, 19)
      .replace(/[:T]/g, '-');
    downloadCsv(`nexo-trades-${stamp}.csv`, tradesToCsv(filtered));
  };

  const loading = status === 'loading';
  const disconnected = status === 'error' && !trades;
  const hasAny = allTrades.length > 0;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Trade History"
        description="Executed fills with search, filters, and CSV export."
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
              aria-label="Refresh trades"
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
                {error?.message ?? 'The trade history could not load data.'}
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={refetch}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Retry
          </Button>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <TradeFiltersBar
            filters={filters}
            onChange={updateFilters}
            onReset={resetFilters}
            assets={assets}
            onExport={handleExport}
            exportHint={EXPORT_HINT}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle>Trades</CardTitle>
          {!loading ? (
            <span className="tabular text-xs text-muted-foreground">
              {filtered.length} of {allTrades.length}
            </span>
          ) : null}
        </CardHeader>
        <CardContent className="p-0">
          <TradeHistoryTable
            rows={pageData.items}
            loading={loading}
            emptyTitle={hasAny ? 'No matching trades' : 'No trades yet'}
            emptyDescription={
              hasAny
                ? 'No trades match the current search or filters.'
                : 'Executed fills will appear here once trading data is available.'
            }
          />
          {!loading && filtered.length > 0 ? (
            <TradePagination
              page={pageData.page}
              pageSize={pageData.pageSize}
              totalItems={pageData.totalItems}
              totalPages={pageData.totalPages}
              onPageChange={setPage}
              onPageSizeChange={(size) => {
                setPageSize(size);
                setPage(1);
              }}
            />
          ) : null}
        </CardContent>
      </Card>

      {!TRADE_SERVER_PAGINATION_AVAILABLE ? (
        <p className="text-xs text-muted-foreground">
          Showing the most recent executed fills from the backend. Server-side
          pagination and CSV export endpoints are not available in this build;
          pagination and export run client-side over the loaded rows.
        </p>
      ) : null}
    </div>
  );
}
