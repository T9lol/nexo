import { Lock, type LucideIcon } from 'lucide-react';
import { Badge, Card, CardContent, CardHeader, CardTitle } from '@/components/ui';

interface UnavailablePanelProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

/** A clearly-disabled admin panel. Renders no data — the underlying feature has
 * no backend or authorization and nothing is fabricated. */
export function UnavailablePanel({
  icon: Icon,
  title,
  description,
}: UnavailablePanelProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex-row items-start justify-between space-y-0">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-muted-foreground">
            <Icon className="h-4 w-4" aria-hidden="true" />
          </span>
          <CardTitle className="text-sm">{title}</CardTitle>
        </div>
        <Badge variant="default">Unavailable</Badge>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-3">
        <p className="text-sm text-muted-foreground">{description}</p>
        <p className="mt-auto flex items-center gap-1.5 text-xs text-muted-foreground">
          <Lock className="h-3 w-3 shrink-0" aria-hidden="true" />
          Requires backend and authorization not available in this build.
        </p>
      </CardContent>
    </Card>
  );
}
