import { type HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

/** Loading placeholder with a subtle shimmer (disabled under reduced motion). */
export function Skeleton({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'skeleton-shimmer relative overflow-hidden rounded-md bg-muted',
        className,
      )}
      aria-hidden="true"
      {...props}
    />
  );
}
