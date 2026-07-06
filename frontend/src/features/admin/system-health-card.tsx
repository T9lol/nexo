import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Skeleton,
} from '@/components/ui';
import type { SystemHealth } from '@/services';

interface SystemHealthCardProps {
  health?: SystemHealth | null;
  loading?: boolean;
  error?: boolean;
}

function HealthTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col rounded-lg border border-border p-3">
      <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="mt-1 text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

/** Real system health from /api/health + /api/state. */
export function SystemHealthCard({
  health,
  loading,
  error,
}: SystemHealthCardProps) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>System Health</CardTitle>
        {!loading ? (
          error || !health ? (
            <Badge variant="negative">Unreachable</Badge>
          ) : (
            <Badge variant={health.healthy ? 'positive' : 'warning'}>
              {health.healthy ? 'Healthy' : health.status}
            </Badge>
          )
        ) : null}
      </CardHeader>
      <CardContent>
        {loading && !health ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <Skeleton key={index} className="h-16 w-full" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <HealthTile label="Status" value={health?.status ?? '—'} />
            <HealthTile label="Runtime mode" value={health?.mode ?? '—'} />
            <HealthTile
              label="Environment"
              value={health?.environment ?? '—'}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
