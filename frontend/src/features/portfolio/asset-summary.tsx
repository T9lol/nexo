import {
  Coins,
  Landmark,
  TrendingDown,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { StatCard } from '@/features/dashboard/stat-card';
import { cn } from '@/lib/cn';
import {
  formatMYR,
  formatSignedUSD,
  formatUSD,
  usdToMyr,
} from '@/lib/currency';
import type { ExchangeRate } from '@/services';
import type { PortfolioSummary } from './portfolio-model';

interface AssetSummaryProps {
  summary?: PortfolioSummary | null;
  rate?: ExchangeRate | null;
  loading?: boolean;
}

function weightLabel(value: number, total: number): string {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return `${pct.toFixed(0)}% of portfolio`;
}

/** Portfolio Asset Summary: total value (RM + approx USD), invested, cash, PnL. */
export function AssetSummary({ summary, rate, loading }: AssetSummaryProps) {
  const hasData = !!summary;
  const busy = loading || !hasData;
  const totalMyr =
    summary && rate ? usdToMyr(summary.totalUsd, rate.rate) : null;
  const pnl = summary?.pnlUsd ?? 0;
  const pnlPositive = pnl >= 0;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        hero
        label="Total Value"
        icon={Wallet}
        loading={busy}
        value={
          totalMyr != null
            ? formatMYR(totalMyr)
            : formatUSD(summary?.totalUsd ?? 0)
        }
        sub={
          summary ? (
            <span>
              &asymp; {formatUSD(summary.totalUsd)}
              {rate?.isPlaceholder ? (
                <span className="ml-1 text-muted-foreground/80">
                  &middot; approx. rate
                </span>
              ) : null}
            </span>
          ) : null
        }
      />
      <StatCard
        label="Invested"
        icon={Coins}
        loading={busy}
        value={formatUSD(summary?.investedUsd ?? 0)}
        sub={
          summary ? weightLabel(summary.investedUsd, summary.totalUsd) : null
        }
      />
      <StatCard
        label="Cash"
        icon={Landmark}
        loading={busy}
        value={formatUSD(summary?.cashUsd ?? 0)}
        sub={summary ? weightLabel(summary.cashUsd, summary.totalUsd) : null}
      />
      <StatCard
        label="All-time PnL"
        icon={pnlPositive ? TrendingUp : TrendingDown}
        loading={busy}
        value={
          <span className={cn(pnlPositive ? 'text-positive' : 'text-negative')}>
            {formatSignedUSD(pnl)}
          </span>
        }
      />
    </div>
  );
}
