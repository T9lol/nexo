import { LineChart as LineChartIcon } from 'lucide-react';
import { useMemo } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
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
import { useTheme } from '@/theme/theme-context';
import type { EquityPoint } from '@/services';

function cssToken(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return raw ? `hsl(${raw})` : fallback;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function ValueTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0];
  if (!point) return null;
  const label = (point.payload as { label?: string }).label ?? '';
  const value = typeof point.value === 'number' ? point.value : 0;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-md">
      <div className="text-muted-foreground">{label}</div>
      <div className="tabular font-semibold">{formatUSD(value)}</div>
    </div>
  );
}

interface PortfolioValueCardProps {
  data?: EquityPoint[] | null;
  loading?: boolean;
}

/** Portfolio value over time, from the backend equity history. */
export function PortfolioValueCard({ data, loading }: PortfolioValueCardProps) {
  const { resolvedTheme } = useTheme();

  const colors = {
    line: cssToken('--primary', '#10b981'),
    grid: cssToken('--border', '#e5e7eb'),
    axis: cssToken('--muted-foreground', '#6b7280'),
  };

  const chartData = useMemo(
    () =>
      (data ?? []).map((point) => ({
        value: point.value,
        label: formatTime(point.time),
      })),
    [data],
  );

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Portfolio Value</CardTitle>
        {data ? (
          <span className="tabular text-xs text-muted-foreground">
            {data.length} points
          </span>
        ) : null}
      </CardHeader>
      <CardContent>
        {loading && !data ? (
          <Skeleton className="h-[260px] w-full" />
        ) : chartData.length < 2 ? (
          <EmptyState
            className="h-[260px] justify-center"
            icon={LineChartIcon}
            title="Not enough history yet"
            description="Portfolio value over time appears once a few points are recorded."
          />
        ) : (
          <div className="h-[260px] w-full" key={resolvedTheme}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={chartData}
                margin={{ top: 8, right: 8, bottom: 0, left: 8 }}
              >
                <defs>
                  <linearGradient
                    id="portfolioFill"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stopColor={colors.line}
                      stopOpacity={0.24}
                    />
                    <stop
                      offset="100%"
                      stopColor={colors.line}
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={colors.grid}
                  vertical={false}
                />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: colors.axis }}
                  tickLine={false}
                  axisLine={false}
                  minTickGap={48}
                />
                <YAxis
                  width={72}
                  tick={{ fontSize: 11, fill: colors.axis }}
                  tickLine={false}
                  axisLine={false}
                  domain={['auto', 'auto']}
                  tickFormatter={(value: number) => formatUSD(value)}
                />
                <Tooltip content={<ValueTooltip />} />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={colors.line}
                  strokeWidth={2}
                  fill="url(#portfolioFill)"
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
