import { Wallet } from 'lucide-react';
import { formatMYR, formatUSD, usdToMyr } from '@/lib/currency';
import type { ExchangeRate } from '@/services';
import { StatCard } from './stat-card';

interface TotalAssetsCardProps {
  /** Total equity in USD from the backend. */
  equityUsd?: number;
  rate?: ExchangeRate | null;
  loading?: boolean;
  className?: string;
}

/** Primary metric: total assets in RM (MYR) with an approximate USD value. */
export function TotalAssetsCard({
  equityUsd,
  rate,
  loading,
  className,
}: TotalAssetsCardProps) {
  const hasEquity = typeof equityUsd === 'number';
  const myr = hasEquity && rate ? usdToMyr(equityUsd, rate.rate) : null;

  return (
    <StatCard
      hero
      className={className}
      label="Total Assets"
      icon={Wallet}
      loading={loading || !hasEquity}
      value={myr != null ? formatMYR(myr) : formatUSD(equityUsd ?? 0)}
      sub={
        hasEquity ? (
          <span>
            &asymp; {formatUSD(equityUsd)}
            {rate?.isPlaceholder ? (
              <span className="ml-1 text-muted-foreground/80">
                &middot; approx. rate
              </span>
            ) : null}
          </span>
        ) : null
      }
    />
  );
}
