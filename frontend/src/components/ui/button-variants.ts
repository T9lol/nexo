import { cva, type VariantProps } from 'class-variance-authority';

/** Button styling variants. Kept separate from the component so the component
 * module only exports components (Fast Refresh friendly). */
export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary:
          'bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/95',
        secondary:
          'bg-muted text-foreground hover:bg-muted/70 active:bg-muted/90',
        outline:
          'border border-input bg-transparent hover:bg-muted active:bg-muted/70',
        ghost: 'hover:bg-muted active:bg-muted/70',
        destructive:
          'bg-negative text-negative-foreground hover:bg-negative/90 active:bg-negative/95',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-9 px-4',
        lg: 'h-11 px-6 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  },
);

export type ButtonVariantProps = VariantProps<typeof buttonVariants>;
