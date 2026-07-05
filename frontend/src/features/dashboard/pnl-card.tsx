import { TrendingDown, TrendingUp } from 'lucide-react';
import { formatSignedUSD } from '@/lib/currency';
import { cn } from '@/lib/cn';
import type { PnlPeriod } from '@/services';
import { StatCard } from './stat-card';

interface PnlCardProps {
  label: string;
  period?: PnlPeriod | null;
  loading?: boolean;
  className?: string;
}

/** Period PnL card. Renders an honest "unavailable" state while the backend
 * lacks a time-bucketed PnL endpoint. */
export function PnlCard({ label, period, loading, className }: PnlCardProps) {
  if (loading || !period) {
    return <StatCard className={className} label={label} loading />;
  }

  if (!period.available || period.value == null) {
    return (
      <StatCard
        className={className}
        label={label}
        unavailable
        unavailableHint="Pending analytics endpoint"
      />
    );
  }

  const positive = period.value >= 0;

  return (
    <StatCard
      className={className}
      label={label}
      icon={positive ? TrendingUp : TrendingDown}
      value={
        <span className={cn(positive ? 'text-positive' : 'text-negative')}>
          {formatSignedUSD(period.value)}
        </span>
      }
    />
  );
}
