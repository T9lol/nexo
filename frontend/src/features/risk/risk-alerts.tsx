import {
  AlertTriangle,
  Info,
  OctagonAlert,
  ShieldCheck,
  type LucideIcon,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Skeleton,
} from '@/components/ui';
import { cn } from '@/lib/cn';
import type { AlertLevel, RiskAlert } from './risk-model';

const LEVEL: Record<
  AlertLevel,
  { icon: LucideIcon; tone: string; container: string }
> = {
  critical: {
    icon: OctagonAlert,
    tone: 'text-negative',
    container: 'border-negative/40 bg-negative/5',
  },
  warning: {
    icon: AlertTriangle,
    tone: 'text-warning',
    container: 'border-warning/40 bg-warning/5',
  },
  info: {
    icon: Info,
    tone: 'text-muted-foreground',
    container: 'border-border bg-muted/30',
  },
};

export function RiskAlertsPanel({
  alerts,
  loading,
}: {
  alerts: RiskAlert[];
  loading?: boolean;
}) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Risk Alerts</CardTitle>
        {!loading ? (
          <span className="tabular text-xs text-muted-foreground">
            {alerts.length}
          </span>
        ) : null}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 2 }).map((_, index) => (
              <Skeleton key={index} className="h-14 w-full" />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-6 text-center">
            <ShieldCheck className="h-8 w-8 text-positive" aria-hidden="true" />
            <p className="text-sm font-medium text-foreground">
              No active risk alerts
            </p>
            <p className="max-w-xs text-xs text-muted-foreground">
              Runtime conditions are within expected ranges.
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-2">
            {alerts.map((alert) => {
              const { icon: Icon, tone, container } = LEVEL[alert.level];
              return (
                <li
                  key={alert.id}
                  className={cn(
                    'flex items-start gap-3 rounded-lg border p-3',
                    container,
                  )}
                >
                  <Icon
                    className={cn('mt-0.5 h-4 w-4 shrink-0', tone)}
                    aria-hidden="true"
                  />
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm font-medium text-foreground">
                      {alert.title}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {alert.description}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
