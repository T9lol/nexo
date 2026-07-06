import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui';
import type { BadgeProps } from '@/components/ui';

export type BacktestRunStatus = 'idle' | 'running' | 'complete' | 'error';

interface BacktestStatusPanelProps {
  status: BacktestRunStatus;
  error?: string | null;
  ranAt?: string | null;
  strategy?: string | null;
}

const PRESENTATION: Record<
  BacktestRunStatus,
  { label: string; variant: BadgeProps['variant'] }
> = {
  idle: { label: 'Not run', variant: 'default' },
  running: { label: 'Running', variant: 'warning' },
  complete: { label: 'Completed', variant: 'positive' },
  error: { label: 'Failed', variant: 'negative' },
};

export function BacktestStatusPanel({
  status,
  error,
  ranAt,
  strategy,
}: BacktestStatusPanelProps) {
  const { label, variant } = PRESENTATION[status];

  let message: string;
  if (status === 'idle') {
    message = 'Configure the strategy and run a backtest.';
  } else if (status === 'running') {
    message = 'Replaying the reference history…';
  } else if (status === 'error') {
    message = error ?? 'The backtest could not run.';
  } else {
    const when = ranAt
      ? new Date(ranAt).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })
      : '';
    message = `Strategy ${strategy ?? '—'} · ${when}`;
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Status</CardTitle>
        <Badge variant={variant}>{label}</Badge>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{message}</p>
      </CardContent>
    </Card>
  );
}
