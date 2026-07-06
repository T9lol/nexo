import {
  AlertTriangle,
  Banknote,
  FileClock,
  Flag,
  RefreshCw,
  ShieldQuestion,
  Users,
  Wrench,
} from 'lucide-react';
import { Badge, Button, Card, PageHeader } from '@/components/ui';
import { ConnectionStatus } from '@/features/dashboard/connection-status';
import { SystemHealthCard, UnavailablePanel } from '@/features/admin';
import { usePolling } from '@/hooks/use-polling';
import { getSystemHealth } from '@/services';

const UNAVAILABLE_PANELS = [
  {
    icon: Users,
    title: 'User Management',
    description: 'Create, disable, and assign roles to operator accounts.',
  },
  {
    icon: ShieldQuestion,
    title: 'KYC Review',
    description: 'Review and approve identity-verification submissions.',
  },
  {
    icon: Banknote,
    title: 'Deposit / Withdrawal Approval',
    description: 'Approve or reject funding requests.',
  },
  {
    icon: FileClock,
    title: 'Audit Logs',
    description: 'Immutable record of administrative and trading actions.',
  },
  {
    icon: Flag,
    title: 'Feature Flags',
    description: 'Toggle experimental features per environment.',
  },
  {
    icon: Wrench,
    title: 'Maintenance Mode',
    description: 'Take the platform offline for scheduled maintenance.',
  },
];

export default function AdminPage() {
  const {
    data: health,
    status,
    error,
    lastUpdated,
    refetch,
  } = usePolling(getSystemHealth, 10_000);

  const loading = status === 'loading';
  const disconnected = status === 'error' && !health;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Admin Console"
        description="Operator administration and platform health."
        actions={
          <div className="flex items-center gap-3">
            <ConnectionStatus
              status={status}
              error={error}
              lastUpdated={lastUpdated}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={refetch}
              aria-label="Refresh system health"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Refresh
            </Button>
          </div>
        }
      />

      <Card className="flex items-start gap-3 border-warning/40 bg-warning/5 p-4">
        <AlertTriangle
          className="mt-0.5 h-5 w-5 shrink-0 text-warning"
          aria-hidden="true"
        />
        <div className="flex flex-col gap-0.5">
          <p className="flex items-center gap-2 text-sm font-medium text-foreground">
            Admin features are future scope
            <Badge variant="warning">Future scope</Badge>
          </p>
          <p className="text-sm text-muted-foreground">
            These require server-side authorization and backends that are not
            part of this local terminal. The panels below are disabled
            placeholders — no user, KYC, financial, or audit data is stored or
            displayed.
          </p>
        </div>
      </Card>

      <SystemHealthCard health={health} loading={loading} error={disconnected} />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {UNAVAILABLE_PANELS.map((panel) => (
          <UnavailablePanel
            key={panel.title}
            icon={panel.icon}
            title={panel.title}
            description={panel.description}
          />
        ))}
      </div>
    </div>
  );
}
