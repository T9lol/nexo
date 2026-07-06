import { useMemo, type ReactNode } from 'react';
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { formatUSD } from '@/lib/currency';
import { useTheme } from '@/theme/theme-context';
import type { DrawdownPoint } from './backtest-model';
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

function formatPct(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

interface ChartCardProps {
  title: string;
  children: ReactNode;
}

function ChartCard({ title, children }: ChartCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[240px] w-full">{children}</div>
      </CardContent>
    </Card>
  );
}

function EquityTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0];
  if (!point) return null;
  const datum = point.payload as { label: string };
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-md">
      <div className="text-muted-foreground">{datum.label}</div>
      <div className="tabular font-semibold">
        {formatUSD(typeof point.value === 'number' ? point.value : 0)}
      </div>
    </div>
  );
}

function DrawdownTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0];
  if (!point) return null;
  const datum = point.payload as { label: string };
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-md">
      <div className="text-muted-foreground">{datum.label}</div>
      <div className="tabular font-semibold text-negative">
        {formatPct(typeof point.value === 'number' ? point.value : 0)}
      </div>
    </div>
  );
}

export function BacktestEquityChart({ data }: { data: EquityPoint[] }) {
  const { resolvedTheme } = useTheme();
  const color = cssToken('--positive', '#10b981');
  const grid = cssToken('--border', '#e5e7eb');
  const axis = cssToken('--muted-foreground', '#6b7280');

  const chartData = useMemo(
    () =>
      data.map((point) => ({
        value: point.value,
        label: formatTime(point.time),
      })),
    [data],
  );

  return (
    <ChartCard title="Equity Curve">
      <div className="h-full w-full" key={resolvedTheme}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 8, right: 8, bottom: 0, left: 8 }}
          >
            <defs>
              <linearGradient id="btEquityFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.24} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={grid}
              vertical={false}
            />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: axis }}
              tickLine={false}
              axisLine={false}
              minTickGap={40}
            />
            <YAxis
              width={72}
              tick={{ fontSize: 11, fill: axis }}
              tickLine={false}
              axisLine={false}
              domain={['auto', 'auto']}
              tickFormatter={(value: number) => formatUSD(value)}
            />
            <Tooltip content={<EquityTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              fill="url(#btEquityFill)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}

export function BacktestDrawdownChart({ data }: { data: DrawdownPoint[] }) {
  const { resolvedTheme } = useTheme();
  const color = cssToken('--negative', '#dc2626');
  const grid = cssToken('--border', '#e5e7eb');
  const axis = cssToken('--muted-foreground', '#6b7280');

  const chartData = useMemo(
    () =>
      data.map((point) => ({
        value: point.value,
        label: formatTime(point.time),
      })),
    [data],
  );

  return (
    <ChartCard title="Drawdown">
      <div className="h-full w-full" key={resolvedTheme}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 8, right: 8, bottom: 0, left: 8 }}
          >
            <defs>
              <linearGradient id="btDrawdownFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0} />
                <stop offset="100%" stopColor={color} stopOpacity={0.24} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={grid}
              vertical={false}
            />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: axis }}
              tickLine={false}
              axisLine={false}
              minTickGap={40}
            />
            <YAxis
              width={56}
              tick={{ fontSize: 11, fill: axis }}
              tickLine={false}
              axisLine={false}
              domain={['auto', 0]}
              tickFormatter={(value: number) => formatPct(value)}
            />
            <Tooltip content={<DrawdownTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              fill="url(#btDrawdownFill)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
