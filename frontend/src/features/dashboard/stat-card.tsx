import { type LucideIcon } from 'lucide-react';
import { type ReactNode } from 'react';
import { Card, CardContent, CardHeader, Skeleton } from '@/components/ui';
import { cn } from '@/lib/cn';

export interface StatCardProps {
  label: string;
  icon?: LucideIcon;
  loading?: boolean;
  /** Render an honest "not available" placeholder instead of a value. */
  unavailable?: boolean;
  unavailableHint?: string;
  value?: ReactNode;
  sub?: ReactNode;
  className?: string;
  /** Emphasize this card as the primary metric. */
  hero?: boolean;
}

/** KPI card with consistent loading / unavailable / value states. */
export function StatCard({
  label,
  icon: Icon,
  loading,
  unavailable,
  unavailableHint,
  value,
  sub,
  className,
  hero,
}: StatCardProps) {
  return (
    <Card
      className={cn(
        'flex flex-col',
        hero && 'border-primary/30 bg-primary/[0.03]',
        className,
      )}
    >
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
        {Icon ? (
          <Icon
            className="h-4 w-4 shrink-0 text-muted-foreground"
            aria-hidden="true"
          />
        ) : null}
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        {loading ? (
          <>
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-4 w-20" />
          </>
        ) : unavailable ? (
          <>
            <span className="text-2xl font-semibold text-muted-foreground">
              &mdash;
            </span>
            <span className="text-xs text-muted-foreground">
              {unavailableHint ?? 'Not yet available'}
            </span>
          </>
        ) : (
          <>
            <div
              className={cn(
                'font-semibold tracking-tight tabular',
                hero ? 'text-3xl' : 'text-2xl',
              )}
            >
              {value}
            </div>
            {sub ? (
              <div className="text-xs text-muted-foreground">{sub}</div>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
