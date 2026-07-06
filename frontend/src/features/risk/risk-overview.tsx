import { Activity, Landmark, ShieldAlert, Wallet } from 'lucide-react';
import { Badge } from '@/components/ui';
import { StatCard } from '@/features/dashboard/stat-card';
import { formatUSD } from '@/lib/currency';
import type { RiskOverview } from './risk-model';

interface RiskOverviewCardsProps {
  overview?: RiskOverview | null;
  loading?: boolean;
}

export function RiskOverviewCards({
  overview,
  loading,
}: RiskOverviewCardsProps) {
  const busy = loading || !overview;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="Portfolio Value"
        icon={Wallet}
        loading={busy}
        value={formatUSD(overview?.equity ?? 0)}
      />
      <StatCard
        label="Current Exposure"
        icon={ShieldAlert}
        loading={busy}
        value={formatUSD(overview?.exposureValue ?? 0)}
        sub={
          overview
            ? `${overview.exposurePct.toFixed(0)}% of portfolio`
            : undefined
        }
      />
      <StatCard
        label="Cash Buffer"
        icon={Landmark}
        loading={busy}
        value={formatUSD(overview?.cash ?? 0)}
        sub={overview ? `${overview.cashPct.toFixed(0)}% of portfolio` : undefined}
      />
      <StatCard
        label="Trading Status"
        icon={Activity}
        loading={busy}
        value={
          <Badge variant={overview?.tradingEnabled ? 'positive' : 'negative'}>
            {overview?.tradingEnabled ? 'Active' : 'Paused'}
          </Badge>
        }
        sub={
          overview
            ? overview.positionLimitEnabled
              ? 'Position-limit policy on'
              : 'Position-limit policy off'
            : undefined
        }
      />
    </div>
  );
}
