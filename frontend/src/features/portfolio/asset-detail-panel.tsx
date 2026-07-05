import { MousePointerClick } from 'lucide-react';
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  Skeleton,
} from '@/components/ui';
import { formatUSD } from '@/lib/currency';
import type { Trade } from '@/services';
import { tradesForSymbol, type Holding } from './portfolio-model';

interface AssetDetailPanelProps {
  holding?: Holding | null;
  trades?: Trade[];
  loading?: boolean;
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border py-2.5 text-sm last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="tabular font-medium">{value}</span>
    </div>
  );
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function AssetDetailPanel({
  holding,
  trades,
  loading,
}: AssetDetailPanelProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Asset Detail</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-10 w-40" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : !holding ? (
          <EmptyState
            icon={MousePointerClick}
            title="No asset selected"
            description="Select a holding to see its details and recent activity."
          />
        ) : (
          <div className="flex flex-col gap-5">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-xs font-semibold text-muted-foreground">
                {holding.symbol.slice(0, 3)}
              </span>
              <div className="flex flex-col">
                <span className="font-semibold text-foreground">
                  {holding.symbol}
                </span>
                <span className="text-xs text-muted-foreground">
                  {holding.name}
                </span>
              </div>
              <Badge
                variant={holding.kind === 'cash' ? 'default' : 'primary'}
                className="ml-auto capitalize"
              >
                {holding.kind}
              </Badge>
            </div>

            <div className="flex flex-col">
              <DetailRow
                label="Quantity"
                value={
                  holding.kind === 'cash'
                    ? formatUSD(holding.quantity)
                    : `${holding.quantity.toFixed(4)} ${holding.symbol}`
                }
              />
              <DetailRow label="Price" value={formatUSD(holding.price)} />
              <DetailRow label="Value" value={formatUSD(holding.valueUsd)} />
              <DetailRow
                label="Allocation"
                value={`${(holding.allocation * 100).toFixed(1)}%`}
              />
            </div>

            <div className="flex flex-col gap-2">
              <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Recent activity
              </h4>
              {holding.kind === 'cash' ? (
                <p className="text-sm text-muted-foreground">
                  Cash positions have no trade history.
                </p>
              ) : (
                <AssetTrades trades={tradesForSymbol(trades, holding.symbol)} />
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function AssetTrades({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No recent trades for this asset.
      </p>
    );
  }
  return (
    <ul className="flex flex-col gap-1.5">
      {trades.slice(0, 5).map((trade) => (
        <li
          key={trade.id}
          className="flex items-center justify-between gap-2 text-sm"
        >
          <span className="flex items-center gap-2">
            <Badge variant={trade.action === 'BUY' ? 'positive' : 'negative'}>
              {trade.action}
            </Badge>
            <span className="text-muted-foreground">
              {formatTime(trade.time)}
            </span>
          </span>
          <span className="tabular">
            {trade.amount.toFixed(2)} @ {formatUSD(trade.price)}
          </span>
        </li>
      ))}
    </ul>
  );
}
