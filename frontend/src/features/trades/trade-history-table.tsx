import { Inbox } from 'lucide-react';
import {
  Badge,
  EmptyState,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui';
import { formatUSD } from '@/lib/currency';
import type { Trade } from '@/services';

interface TradeHistoryTableProps {
  rows: Trade[];
  loading?: boolean;
  emptyTitle: string;
  emptyDescription: string;
}

function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return `${date.toLocaleDateString([], { month: 'short', day: '2-digit' })} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
}

/** Muted placeholder for a metric the backend does not provide. */
function Unavailable() {
  return (
    <span className="text-muted-foreground" title="Not available">
      &mdash;
    </span>
  );
}

export function TradeHistoryTable({
  rows,
  loading,
  emptyTitle,
  emptyDescription,
}: TradeHistoryTableProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2 px-6 pb-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <EmptyState
        className="rounded-none border-0"
        icon={Inbox}
        title={emptyTitle}
        description={emptyDescription}
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Side</TableHead>
          <TableHead>Asset</TableHead>
          <TableHead className="text-right">Quantity</TableHead>
          <TableHead className="text-right">Price</TableHead>
          <TableHead className="text-right">Fee</TableHead>
          <TableHead className="text-right">Realized PnL</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Date / Time</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((trade) => (
          <TableRow key={trade.id}>
            <TableCell>
              <Badge variant={trade.action === 'BUY' ? 'positive' : 'negative'}>
                {trade.action}
              </Badge>
            </TableCell>
            <TableCell className="font-medium">{trade.symbol}</TableCell>
            <TableCell className="text-right">
              {trade.amount.toFixed(4)}
            </TableCell>
            <TableCell className="text-right">
              {formatUSD(trade.price)}
            </TableCell>
            <TableCell className="text-right">
              <Unavailable />
            </TableCell>
            <TableCell className="text-right">
              <Unavailable />
            </TableCell>
            <TableCell>
              <Badge variant="outline">Filled</Badge>
            </TableCell>
            <TableCell className="whitespace-nowrap text-right text-muted-foreground">
              {formatDateTime(trade.time)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
