import { BarChart3 } from 'lucide-react';
import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
} from '@/components/ui';
import { useTheme } from '@/theme/theme-context';
import type { StrategyMetrics } from './strategy-model';

type Metric = 'adaptive' | 'score' | 'weight' | 'trades';

const METRIC_LABELS: Record<Metric, string> = {
  adaptive: 'Performance Score',
  score: 'Cumulative Reward',
  weight: 'Adaptive Weight',
  trades: 'Total Trades',
};

const ACTIVE_COLOR = '#10b981';
const OTHER_COLOR = '#64748b';

function cssToken(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return raw ? `hsl(${raw})` : fallback;
}

function formatValue(metric: Metric, value: number): string {
  if (metric === 'weight') return value.toFixed(4);
  if (metric === 'trades') return String(value);
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
}

interface ComparisonDatum {
  name: string;
  value: number;
  active: boolean;
}

function makeTooltip(metric: Metric) {
  return function ComparisonTooltip({
    active,
    payload,
  }: TooltipProps<number, string>) {
    if (!active || !payload || payload.length === 0) return null;
    const point = payload[0];
    if (!point) return null;
    const datum = point.payload as ComparisonDatum;
    return (
      <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-md">
        <div className="font-medium text-foreground">{datum.name}</div>
        <div className="tabular text-muted-foreground">
          {METRIC_LABELS[metric]}: {formatValue(metric, datum.value)}
        </div>
      </div>
    );
  };
}

interface StrategyComparisonChartProps {
  strategies: StrategyMetrics[];
  activeName: string | null;
  loading?: boolean;
}

export function StrategyComparisonChart({
  strategies,
  activeName,
  loading,
}: StrategyComparisonChartProps) {
  const { resolvedTheme } = useTheme();
  const [metric, setMetric] = useState<Metric>('adaptive');

  const gridColor = cssToken('--border', '#e5e7eb');
  const axisColor = cssToken('--muted-foreground', '#6b7280');

  const data: ComparisonDatum[] = strategies.map((strategy) => ({
    name: `Strategy ${strategy.name}`,
    value: strategy[metric],
    active: strategy.name === activeName,
  }));

  const Tip = makeTooltip(metric);

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3 space-y-0">
        <CardTitle>Performance Comparison</CardTitle>
        <Select
          value={metric}
          onValueChange={(value) => setMetric(value as Metric)}
        >
          <SelectTrigger className="w-[190px]" aria-label="Comparison metric">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(METRIC_LABELS) as Metric[]).map((key) => (
              <SelectItem key={key} value={key}>
                {METRIC_LABELS[key]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-[280px] w-full" />
        ) : data.length === 0 ? (
          <EmptyState
            className="h-[280px] justify-center"
            icon={BarChart3}
            title="No strategies to compare"
            description="Comparison appears once the engine reports strategies."
          />
        ) : (
          <div className="h-[280px] w-full" key={resolvedTheme}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data}
                margin={{ top: 8, right: 8, bottom: 0, left: 8 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={gridColor}
                  vertical={false}
                />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12, fill: axisColor }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  width={64}
                  tick={{ fontSize: 11, fill: axisColor }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  cursor={{ fill: 'hsl(var(--muted) / 0.4)' }}
                  content={<Tip />}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                  {data.map((datum) => (
                    <Cell
                      key={datum.name}
                      fill={datum.active ? ACTIVE_COLOR : OTHER_COLOR}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
