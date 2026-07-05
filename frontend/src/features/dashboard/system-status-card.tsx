import { Activity } from 'lucide-react';
import { Badge } from '@/components/ui';
import type { BadgeProps } from '@/components/ui';
import type { DashboardState } from '@/services';
import { StatCard } from './stat-card';

interface SystemStatusCardProps {
  state?: DashboardState | null;
  loading?: boolean;
  className?: string;
}

export function SystemStatusCard({
  state,
  loading,
  className,
}: SystemStatusCardProps) {
  if (loading || !state) {
    return <StatCard className={className} label="System Status" loading />;
  }

  const mode = state.control?.mode ?? state.mode;
  const trading = state.control?.trading_enabled ?? true;
  const backtest = mode === 'backtest';

  const variant: BadgeProps['variant'] = backtest
    ? 'warning'
    : trading
      ? 'positive'
      : 'warning';
  const label = backtest
    ? 'Backtest'
    : trading
      ? 'Live · Trading'
      : 'Live · Paused';

  return (
    <StatCard
      className={className}
      label="System Status"
      icon={Activity}
      value={<Badge variant={variant}>{label}</Badge>}
      sub={
        <span className="uppercase tracking-wide">
          {state.control?.environment ?? 'local'}
        </span>
      }
    />
  );
}
