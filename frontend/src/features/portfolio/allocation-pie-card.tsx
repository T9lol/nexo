import { PieChartIcon } from 'lucide-react';
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  type TooltipProps,
} from 'recharts';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  Skeleton,
} from '@/components/ui';
import { formatUSD } from '@/lib/currency';
import type { Holding } from './portfolio-model';

// Categorical palette that reads well in both light and dark themes.
const PALETTE = ['#10b981', '#64748b', '#f59e0b', '#3b82f6', '#a855f7'];

function colorFor(index: number): string {
  return PALETTE[index % PALETTE.length] ?? '#10b981';
}

interface AllocationSlice {
  symbol: string;
  value: number;
  allocation: number;
}

function AllocationTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0];
  if (!point) return null;
  const slice = point.payload as AllocationSlice;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-md">
      <div className="font-medium text-foreground">{slice.symbol}</div>
      <div className="tabular text-muted-foreground">
        {formatUSD(slice.value)} &middot; {(slice.allocation * 100).toFixed(1)}%
      </div>
    </div>
  );
}

interface AllocationPieCardProps {
  holdings: Holding[];
  loading?: boolean;
}

export function AllocationPieCard({ holdings, loading }: AllocationPieCardProps) {
  const slices: AllocationSlice[] = holdings
    .filter((holding) => holding.valueUsd > 0)
    .map((holding) => ({
      symbol: holding.symbol,
      value: holding.valueUsd,
      allocation: holding.allocation,
    }));

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Allocation</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-[220px] w-full" />
        ) : slices.length === 0 ? (
          <EmptyState
            className="h-[220px] justify-center"
            icon={PieChartIcon}
            title="No allocation to show"
            description="Allocation appears once the portfolio holds value."
          />
        ) : (
          <div className="flex flex-col gap-4">
            <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={slices}
                    dataKey="value"
                    nameKey="symbol"
                    cx="50%"
                    cy="50%"
                    innerRadius={52}
                    outerRadius={82}
                    paddingAngle={2}
                    stroke="none"
                    isAnimationActive={false}
                  >
                    {slices.map((slice, index) => (
                      <Cell key={slice.symbol} fill={colorFor(index)} />
                    ))}
                  </Pie>
                  <Tooltip content={<AllocationTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="flex flex-col gap-2">
              {slices.map((slice, index) => (
                <li
                  key={slice.symbol}
                  className="flex items-center justify-between gap-3 text-sm"
                >
                  <span className="flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: colorFor(index) }}
                      aria-hidden="true"
                    />
                    <span className="font-medium">{slice.symbol}</span>
                  </span>
                  <span className="tabular text-muted-foreground">
                    {(slice.allocation * 100).toFixed(1)}%
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
