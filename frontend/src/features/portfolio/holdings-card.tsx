import { Search } from 'lucide-react';
import { useMemo, useState, type KeyboardEvent } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui';
import { cn } from '@/lib/cn';
import { formatUSD } from '@/lib/currency';
import {
  filterHoldings,
  type Holding,
  type HoldingFilter,
} from './portfolio-model';

interface HoldingsCardProps {
  holdings: Holding[];
  loading?: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function AssetCell({ holding }: { holding: Holding }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-[10px] font-semibold text-muted-foreground">
        {holding.symbol.slice(0, 3)}
      </span>
      <div className="flex flex-col">
        <span className="font-medium text-foreground">{holding.symbol}</span>
        <span className="text-xs text-muted-foreground">{holding.name}</span>
      </div>
    </div>
  );
}

export function HoldingsCard({
  holdings,
  loading,
  selectedId,
  onSelect,
}: HoldingsCardProps) {
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState<HoldingFilter>('all');

  const filtered = useMemo(
    () => filterHoldings(holdings, query, kind),
    [holdings, query, kind],
  );

  const handleKey = (event: KeyboardEvent<HTMLTableRowElement>, id: string) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(id);
    }
  };

  return (
    <Card className="flex flex-col">
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle>Holdings</CardTitle>
          {!loading ? (
            <span className="tabular text-xs text-muted-foreground">
              {holdings.length}{' '}
              {holdings.length === 1 ? 'position' : 'positions'}
            </span>
          ) : null}
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by symbol or name"
              aria-label="Search holdings"
              className="pl-9"
            />
          </div>
          <Select
            value={kind}
            onValueChange={(value) => setKind(value as HoldingFilter)}
          >
            <SelectTrigger className="sm:w-[150px]" aria-label="Filter by type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All assets</SelectItem>
              <SelectItem value="crypto">Crypto</SelectItem>
              <SelectItem value="cash">Cash</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {loading ? (
          <div className="flex flex-col gap-2 px-6 pb-6">
            {Array.from({ length: 3 }).map((_, index) => (
              <Skeleton key={index} className="h-12 w-full" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            className="rounded-none border-0"
            icon={Search}
            title={holdings.length === 0 ? 'No holdings' : 'No matches'}
            description={
              holdings.length === 0
                ? 'Positions will appear here once the portfolio holds assets.'
                : 'No holdings match the current search or filter.'
            }
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Asset</TableHead>
                <TableHead className="text-right">Quantity</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead className="text-right">Allocation</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((holding) => {
                const selected = holding.id === selectedId;
                return (
                  <TableRow
                    key={holding.id}
                    onClick={() => onSelect(holding.id)}
                    onKeyDown={(event) => handleKey(event, holding.id)}
                    tabIndex={0}
                    aria-selected={selected}
                    data-state={selected ? 'selected' : undefined}
                    className={cn(
                      'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring',
                    )}
                  >
                    <TableCell>
                      <AssetCell holding={holding} />
                    </TableCell>
                    <TableCell className="text-right">
                      {holding.kind === 'cash'
                        ? formatUSD(holding.quantity)
                        : holding.quantity.toFixed(4)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatUSD(holding.price)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatUSD(holding.valueUsd)}
                    </TableCell>
                    <TableCell className="text-right">
                      {(holding.allocation * 100).toFixed(1)}%
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
