import { cn } from '@/lib/cn';
import type { AsyncStatus } from '@/hooks/use-polling';

interface ConnectionStatusProps {
  status: AsyncStatus;
  error: Error | null;
  lastUpdated: number | null;
}

type ConnectionKind = 'connecting' | 'live' | 'stale' | 'disconnected';

const PRESENTATION: Record<
  ConnectionKind,
  { label: string; dot: string; text: string }
> = {
  connecting: {
    label: 'Connecting',
    dot: 'bg-muted-foreground',
    text: 'text-muted-foreground',
  },
  live: { label: 'Live', dot: 'bg-positive', text: 'text-positive' },
  stale: { label: 'Stale', dot: 'bg-warning', text: 'text-warning' },
  disconnected: {
    label: 'Disconnected',
    dot: 'bg-negative',
    text: 'text-negative',
  },
};

function resolveKind(
  status: AsyncStatus,
  error: Error | null,
): ConnectionKind {
  if (status === 'error') return 'disconnected';
  if (status === 'loading') return 'connecting';
  return error ? 'stale' : 'live';
}

/** Compact live-connection indicator for the dashboard header. */
export function ConnectionStatus({
  status,
  error,
  lastUpdated,
}: ConnectionStatusProps) {
  const kind = resolveKind(status, error);
  const { label, dot, text } = PRESENTATION[kind];

  return (
    <div className="flex items-center gap-2 text-xs">
      <span
        className={cn(
          'h-2 w-2 rounded-full',
          dot,
          kind === 'live' && 'shadow-[0_0_8px] shadow-positive/60',
        )}
        aria-hidden="true"
      />
      <span className={cn('font-medium', text)}>{label}</span>
      {lastUpdated ? (
        <span className="text-muted-foreground">
          &middot;{' '}
          {new Date(lastUpdated).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          })}
        </span>
      ) : null}
    </div>
  );
}
