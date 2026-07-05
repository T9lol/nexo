import { Download, Search, X } from 'lucide-react';
import {
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import { EMPTY_FILTERS, type TradeFilters } from './trade-model';

interface TradeFiltersBarProps {
  filters: TradeFilters;
  onChange: (patch: Partial<TradeFilters>) => void;
  onReset: () => void;
  assets: string[];
  onExport: () => void;
  exportHint?: string;
}

function isActive(filters: TradeFilters): boolean {
  return (
    filters.query !== EMPTY_FILTERS.query ||
    filters.asset !== EMPTY_FILTERS.asset ||
    filters.side !== EMPTY_FILTERS.side ||
    filters.status !== EMPTY_FILTERS.status ||
    filters.from !== EMPTY_FILTERS.from ||
    filters.to !== EMPTY_FILTERS.to
  );
}

export function TradeFiltersBar({
  filters,
  onChange,
  onReset,
  assets,
  onExport,
  exportHint,
}: TradeFiltersBarProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            value={filters.query}
            onChange={(event) => onChange({ query: event.target.value })}
            placeholder="Search by asset, strategy, side, or id"
            aria-label="Search trades"
            className="pl-9"
          />
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onExport}
          title={exportHint}
          aria-label="Export CSV"
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          Export CSV
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        <Select
          value={filters.asset}
          onValueChange={(value) => onChange({ asset: value })}
        >
          <SelectTrigger aria-label="Filter by asset">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All assets</SelectItem>
            {assets.map((asset) => (
              <SelectItem key={asset} value={asset}>
                {asset}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.side}
          onValueChange={(value) => onChange({ side: value })}
        >
          <SelectTrigger aria-label="Filter by side">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All sides</SelectItem>
            <SelectItem value="BUY">Buy</SelectItem>
            <SelectItem value="SELL">Sell</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={filters.status}
          onValueChange={(value) => onChange({ status: value })}
        >
          <SelectTrigger aria-label="Filter by status">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="filled">Filled</SelectItem>
          </SelectContent>
        </Select>

        <Input
          type="date"
          value={filters.from}
          onChange={(event) => onChange({ from: event.target.value })}
          aria-label="From date"
        />
        <Input
          type="date"
          value={filters.to}
          onChange={(event) => onChange({ to: event.target.value })}
          aria-label="To date"
        />
      </div>

      {isActive(filters) ? (
        <div>
          <Button variant="ghost" size="sm" onClick={onReset}>
            <X className="h-4 w-4" aria-hidden="true" />
            Clear filters
          </Button>
        </div>
      ) : null}
    </div>
  );
}
