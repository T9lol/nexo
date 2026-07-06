import { Save } from 'lucide-react';
import { useState } from 'react';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Switch,
} from '@/components/ui';
import { ConfirmDialog } from './confirm-dialog';

interface RiskConfigCardProps {
  positionLimitEnabled: boolean;
  maxPosition: number;
  pending?: boolean;
  onSetPositionLimit: (enabled: boolean) => void;
}

function ConfigField({
  label,
  value,
  placeholder,
  hint,
}: {
  label: string;
  value: string;
  placeholder?: string;
  hint: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-foreground">{label}</span>
      <Input
        value={value}
        placeholder={placeholder}
        aria-label={label}
        disabled
        readOnly
      />
      <span className="text-[11px] text-muted-foreground">{hint}</span>
    </div>
  );
}

/**
 * Risk configuration. The position-limit policy toggle is real (applies
 * immediately); the remaining limits have no backend endpoint, so they are
 * shown disabled and Save is disabled (never persisting ignored inputs).
 */
export function RiskConfigCard({
  positionLimitEnabled,
  maxPosition,
  pending,
  onSetPositionLimit,
}: RiskConfigCardProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleToggle = () => {
    if (positionLimitEnabled) {
      setConfirmOpen(true); // disabling requires confirmation
    } else {
      onSetPositionLimit(true);
    }
  };

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Risk Configuration</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-center justify-between gap-3 rounded-lg border border-border p-3">
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-medium text-foreground">
              Position-limit policy
            </span>
            <span className="text-xs text-muted-foreground">
              Enforce a maximum position size. Applies immediately.
            </span>
          </div>
          <Switch
            checked={positionLimitEnabled}
            onCheckedChange={handleToggle}
            disabled={pending}
            aria-label="Position-limit policy"
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <ConfigField
            label="Max Position Size"
            value={`${maxPosition} BTC`}
            hint="Fixed by the backend risk engine."
          />
          <ConfigField
            label="Daily Loss Limit"
            value=""
            placeholder="e.g. $500"
            hint="Not configurable via the backend."
          />
          <ConfigField
            label="Max Drawdown Limit"
            value=""
            placeholder="e.g. 10%"
            hint="Not configurable via the backend."
          />
          <ConfigField
            label="Stop Loss"
            value=""
            placeholder="e.g. 5%"
            hint="Not configurable via the backend."
          />
          <ConfigField
            label="Take Profit"
            value=""
            placeholder="e.g. 10%"
            hint="Not configurable via the backend."
          />
        </div>

        <div className="flex flex-col gap-3 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-md text-xs text-muted-foreground">
            Saving these limits is not supported by the backend yet. The
            position-limit policy and emergency stop apply immediately via their
            own controls.
          </p>
          <Button
            variant="outline"
            size="sm"
            disabled
            title="The backend does not support saving risk limits."
            aria-label="Save configuration"
          >
            <Save className="h-4 w-4" aria-hidden="true" />
            Save Configuration
          </Button>
        </div>
      </CardContent>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Disable position-limit policy?"
        description="Positions may exceed the configured cap. Hard execution invariants (valid price/amount, no negative cash, no short) remain enforced."
        confirmLabel="Disable policy"
        destructive
        onConfirm={() => onSetPositionLimit(false)}
      />
    </Card>
  );
}
