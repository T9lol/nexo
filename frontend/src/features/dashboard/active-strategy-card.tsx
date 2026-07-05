import { BrainCircuit } from 'lucide-react';
import { Badge } from '@/components/ui';
import type { DashboardState } from '@/services';
import { StatCard } from './stat-card';

interface ActiveStrategyCardProps {
  state?: DashboardState | null;
  loading?: boolean;
  className?: string;
}

export function ActiveStrategyCard({
  state,
  loading,
  className,
}: ActiveStrategyCardProps) {
  if (loading || !state) {
    return <StatCard className={className} label="Active Strategy" loading />;
  }

  const manual = state.control?.manual_override ?? false;

  return (
    <StatCard
      className={className}
      label="Active Strategy"
      icon={BrainCircuit}
      value={`Strategy ${state.selected_strategy}`}
      sub={
        <Badge variant={manual ? 'warning' : 'primary'}>
          {manual ? 'Manual override' : 'Adaptive routing'}
        </Badge>
      }
    />
  );
}
