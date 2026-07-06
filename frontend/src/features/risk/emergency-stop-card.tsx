import { Ban, Play } from 'lucide-react';
import { useState } from 'react';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui';
import { cn } from '@/lib/cn';
import { ConfirmDialog } from './confirm-dialog';

interface EmergencyStopCardProps {
  tradingEnabled: boolean;
  pending?: boolean;
  onSetTrading: (enabled: boolean) => void;
}

export function EmergencyStopCard({
  tradingEnabled,
  pending,
  onSetTrading,
}: EmergencyStopCardProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);

  return (
    <Card
      className={cn(
        'flex flex-col',
        !tradingEnabled && 'border-negative/40 bg-negative/5',
      )}
    >
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Emergency Stop</CardTitle>
        <Badge variant={tradingEnabled ? 'positive' : 'negative'}>
          {tradingEnabled ? 'Trading active' : 'Trading paused'}
        </Badge>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          Immediately halt all trading. Positions, history, and scores are
          preserved; new fills are blocked until you resume.
        </p>
        {tradingEnabled ? (
          <Button
            variant="destructive"
            loading={pending}
            onClick={() => setConfirmOpen(true)}
            className="w-full"
          >
            {pending ? null : <Ban className="h-4 w-4" aria-hidden="true" />}
            Stop Trading
          </Button>
        ) : (
          <Button
            variant="primary"
            loading={pending}
            onClick={() => onSetTrading(true)}
            className="w-full"
          >
            {pending ? null : <Play className="h-4 w-4" aria-hidden="true" />}
            Resume Trading
          </Button>
        )}
      </CardContent>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Stop all trading?"
        description="This activates the emergency stop and blocks new fills until you resume. Market data and dashboards keep updating."
        confirmLabel="Stop Trading"
        destructive
        onConfirm={() => onSetTrading(false)}
      />
    </Card>
  );
}
