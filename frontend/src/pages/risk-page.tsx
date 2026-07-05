import { ShieldAlert } from 'lucide-react';
import {
  Badge,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  PageHeader,
  Switch,
} from '@/components/ui';

const POLICIES = [
  {
    label: 'Position-limit policy',
    description: 'Cap maximum position size (configurable in a later sprint).',
  },
  {
    label: 'Max daily loss',
    description: 'Halt trading past a daily loss threshold.',
  },
  {
    label: 'Exposure ceiling',
    description: 'Limit total market exposure across strategies.',
  },
];

export default function RiskPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Risk Center"
        description="Limits, exposure, and risk-policy controls."
        actions={<Badge variant="warning">Read-only in Sprint 1</Badge>}
      />

      <Card className="border-warning/40 bg-warning/5">
        <CardHeader className="flex-row items-start gap-3 space-y-0">
          <ShieldAlert
            className="mt-0.5 h-5 w-5 shrink-0 text-warning"
            aria-hidden="true"
          />
          <div className="flex flex-col gap-1">
            <CardTitle className="text-warning">Mandatory invariants</CardTitle>
            <CardDescription>
              Core execution safeguards (valid price/amount, no negative cash, no
              short inventory) are always enforced and cannot be disabled.
            </CardDescription>
          </div>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Configurable policies</CardTitle>
          <CardDescription>
            These toggles are placeholders in Sprint 1 and are not yet connected.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col divide-y divide-border">
          {POLICIES.map((policy) => (
            <div
              key={policy.label}
              className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0"
            >
              <div className="flex flex-col gap-0.5">
                <p className="text-sm font-medium text-foreground">
                  {policy.label}
                </p>
                <p className="text-xs text-muted-foreground">
                  {policy.description}
                </p>
              </div>
              <Switch disabled aria-label={policy.label} />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
