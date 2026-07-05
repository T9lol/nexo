import { Inbox } from 'lucide-react';
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
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

interface RecentTradesCardProps {
  trades?: Trade[] | null;
  loading?: boolean;
  limit?: number;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function RecentTradesCard({
  trades,
  loading,
  limit = 8,
}: RecentTradesCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Recent Trades</CardTitle>
        {trades ? (
          <span className="tabular text-xs text-muted-foreground">
            {trades.length} {trades.length === 1 ? 'fill' : 'fills'}
          </span>
        ) : null}
      </CardHeader>
      <CardContent className="p-0">
        {loading && !trades ? (
          <div className="flex flex-col gap-2 px-6 pb-6">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-9 w-full" />
            ))}
          </div>
        ) : !trades || trades.length === 0 ? (
          <EmptyState
            className="rounded-none border-0"
            icon={Inbox}
            title="No trades yet"
            description="Executed fills will appear here."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Side</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead className="text-right">Size</TableHead>
                <TableHead className="text-right">Price</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trades.slice(0, limit).map((trade) => (
                <TableRow key={trade.id}>
                  <TableCell className="text-muted-foreground">
                    {formatTime(trade.time)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={trade.action === 'BUY' ? 'positive' : 'negative'}
                    >
                      {trade.action}
                    </Badge>
                  </TableCell>
                  <TableCell>Strategy {trade.strategy}</TableCell>
                  <TableCell className="text-right">
                    {trade.amount.toFixed(2)} {trade.symbol}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatUSD(trade.price)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
