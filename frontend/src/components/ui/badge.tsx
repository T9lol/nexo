import { type HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';
import { badgeVariants, type BadgeVariantProps } from './badge-variants';

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & BadgeVariantProps;

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}
