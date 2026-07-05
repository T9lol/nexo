import { cva, type VariantProps } from 'class-variance-authority';

/** Badge styling variants. Kept separate from the component so the component
 * module only exports components (Fast Refresh friendly). */
export const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-muted text-muted-foreground',
        primary: 'border-transparent bg-primary/15 text-primary',
        positive: 'border-transparent bg-positive/15 text-positive',
        negative: 'border-transparent bg-negative/15 text-negative',
        warning: 'border-transparent bg-warning/15 text-warning',
        outline: 'border-border text-foreground',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
);

export type BadgeVariantProps = VariantProps<typeof badgeVariants>;
