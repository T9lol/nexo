import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Skeleton,
} from '@/components/ui';
import { APP_NAME, APP_VERSION } from '@/lib/app-info';
import type { SystemHealth } from '@/services';
import { InfoTile } from './settings-fields';

interface SystemInfoCardProps {
  health?: SystemHealth | null;
  loading?: boolean;
  error?: boolean;
}

export function SystemInfoCard({ health, loading, error }: SystemInfoCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>System Information</CardTitle>
      </CardHeader>
      <CardContent>
        {loading && !health ? (
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-16 w-full" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            <InfoTile label="Application" value={APP_NAME} />
            <InfoTile label="Frontend version" value={APP_VERSION} />
            <InfoTile
              label="Environment"
              value={health?.environment ?? '—'}
            />
            <InfoTile label="Runtime mode" value={health?.mode ?? '—'} />
            <InfoTile
              label="Backend"
              value={
                error || !health ? (
                  <Badge variant="negative">Unreachable</Badge>
                ) : (
                  <Badge variant={health.healthy ? 'positive' : 'warning'}>
                    {health.healthy ? 'Healthy' : health.status}
                  </Badge>
                )
              }
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
