import type { KeyboardEvent } from 'react';
import {
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
import { cn } from '@/lib/cn';
import { BrainCircuit } from 'lucide-react';
import type { StrategyMetrics } from './strategy-model';
import { StrategyStatusBadge } from './strategy-status-badge';

interface StrategyListProps {
  strategies: StrategyMetrics[];
  loading?: boolean;
  selectedName: string | null;
  onSelect: (name: string) => void;
}

function signed(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
}

export function StrategyList({
  strategies,
  loading,
  selectedName,
  onSelect,
}: StrategyListProps) {
  const handleKey = (
    event: KeyboardEvent<HTMLTableRowElement>,
    name: string,
  ) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(name);
    }
  };

  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Strategies</CardTitle>
        {!loading ? (
          <span className="tabular text-xs text-muted-foreground">
            {strategies.length}{' '}
            {strategies.length === 1 ? 'strategy' : 'strategies'}
          </span>
        ) : null}
      </CardHeader>
      <CardContent className="p-0">
        {loading ? (
          <div className="flex flex-col gap-2 px-6 pb-6">
            {Array.from({ length: 2 }).map((_, index) => (
              <Skeleton key={index} className="h-12 w-full" />
            ))}
          </div>
        ) : strategies.length === 0 ? (
          <EmptyState
            className="rounded-none border-0"
            icon={BrainCircuit}
            title="No strategies"
            description="Strategies will appear here once the engine reports them."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Strategy</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Performance</TableHead>
                <TableHead className="text-right">Reward</TableHead>
                <TableHead className="text-right">Weight</TableHead>
                <TableHead className="text-right">Trades</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {strategies.map((strategy) => {
                const selected = strategy.name === selectedName;
                return (
                  <TableRow
                    key={strategy.name}
                    onClick={() => onSelect(strategy.name)}
                    onKeyDown={(event) => handleKey(event, strategy.name)}
                    tabIndex={0}
                    aria-selected={selected}
                    data-state={selected ? 'selected' : undefined}
                    className="cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                  >
                    <TableCell>
                      <div className="flex items-center gap-2.5">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-xs font-semibold text-muted-foreground">
                          {strategy.name}
                        </span>
                        <span className="font-medium text-foreground">
                          Strategy {strategy.name}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <StrategyStatusBadge active={strategy.isActive} />
                    </TableCell>
                    <TableCell
                      className={cn(
                        'text-right font-medium',
                        strategy.adaptive >= 0
                          ? 'text-positive'
                          : 'text-negative',
                      )}
                    >
                      {signed(strategy.adaptive)}
                    </TableCell>
                    <TableCell className="text-right">
                      {signed(strategy.score)}
                    </TableCell>
                    <TableCell className="text-right">
                      {strategy.weight.toFixed(4)}
                    </TableCell>
                    <TableCell className="text-right">
                      {strategy.trades}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
