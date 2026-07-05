import { Badge } from '@/components/ui';

/** Active (currently selected) vs Standby (candidate) status. */
export function StrategyStatusBadge({ active }: { active: boolean }) {
  return (
    <Badge variant={active ? 'positive' : 'default'}>
      <span
        className={
          active
            ? 'mr-1 inline-block h-1.5 w-1.5 rounded-full bg-positive'
            : 'mr-1 inline-block h-1.5 w-1.5 rounded-full bg-muted-foreground'
        }
        aria-hidden="true"
      />
      {active ? 'Active' : 'Standby'}
    </Badge>
  );
}
