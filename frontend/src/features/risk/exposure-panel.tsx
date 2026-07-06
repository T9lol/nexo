import { ShieldAlert } from 'lucide-react';
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
import { exposureSlices, type RiskOverview } from './risk-model';

const COLORS = { exposure: '#10b981', cash: '#64748b' };

function ExposureTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0];
  if (!point) return null;
  const datum = point.payload as { label: string; value: number };
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-md">
      <div className="font-medium text-foreground">{datum.label}</div>
      <div className="tabular text-muted-foreground">
        {formatUSD(datum.value)}
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border py-2.5 text-sm last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="tabular font-medium">{value}</span>
    </div>
  );
}

export function ExposurePanel({
  overview,
  loading,
}: {
  overview?: RiskOverview | null;
  loading?: boolean;
}) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Current Exposure</CardTitle>
      </CardHeader>
      <CardContent>
        {loading || !overview ? (
          <Skeleton className="h-[220px] w-full" />
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            <div className="flex flex-col">
              <DetailRow
                label="Market exposure"
                value={formatUSD(overview.exposureValue)}
              />
              <DetailRow
                label="Exposure share"
                value={`${overview.exposurePct.toFixed(1)}%`}
              />
              <DetailRow
                label="Position"
                value={`${overview.positionUnits} / ${overview.maxPosition} BTC`}
              />
              <DetailRow label="Cash" value={formatUSD(overview.cash)} />
              <DetailRow
                label="Portfolio value"
                value={formatUSD(overview.equity)}
              />
            </div>
            <div className="flex flex-col items-center justify-center gap-3">
              {overview.equity <= 0 ? (
                <EmptyState
                  className="h-[180px] justify-center"
                  icon={ShieldAlert}
                  title="No exposure"
                  description="Portfolio exposure appears once the account holds value."
                />
              ) : (
                <ExposureDonut overview={overview} />
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ExposureDonut({ overview }: { overview: RiskOverview }) {
  const slices = exposureSlices(overview);
  return (
    <>
      <div className="h-[180px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={slices}
              dataKey="value"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius={48}
              outerRadius={74}
              paddingAngle={2}
              stroke="none"
              isAnimationActive={false}
            >
              {slices.map((slice) => (
                <Cell key={slice.kind} fill={COLORS[slice.kind]} />
              ))}
            </Pie>
            <Tooltip content={<ExposureTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="flex w-full flex-col gap-1.5">
        {slices.map((slice) => (
          <li
            key={slice.kind}
            className="flex items-center justify-between text-sm"
          >
            <span className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: COLORS[slice.kind] }}
                aria-hidden="true"
              />
              {slice.label}
            </span>
            <span className="tabular text-muted-foreground">
              {overview.equity > 0
                ? `${((slice.value / overview.equity) * 100).toFixed(1)}%`
                : '—'}
            </span>
          </li>
        ))}
      </ul>
    </>
  );
}
