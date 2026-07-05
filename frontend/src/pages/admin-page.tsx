import { ShieldQuestion } from 'lucide-react';
import { Badge, EmptyState, PageHeader } from '@/components/ui';

export default function AdminPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Admin"
        description="Operator and administration tooling."
        actions={<Badge variant="warning">Future scope</Badge>}
      />

      <EmptyState
        icon={ShieldQuestion}
        title="Admin is not available yet"
        description="This area is reserved for future operator tooling — user management, audit logs, and engine administration — and is intentionally a placeholder in Sprint 1."
      />
    </div>
  );
}
