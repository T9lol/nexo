import { Play } from 'lucide-react';
import { type ReactNode } from 'react';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';

const STRATEGY_LABELS: Record<string, string> = {
  auto: 'Auto (adaptive)',
  A: 'Strategy A',
  B: 'Strategy B',
};

function strategyLabel(value: string): string {
  return STRATEGY_LABELS[value] ?? value;
}

interface BacktestFormProps {
  strategy: string;
  strategies: string[];
  onStrategyChange: (strategy: string) => void;
  onRun: () => void;
  running: boolean;
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-foreground">{label}</span>
      {children}
      {hint ? (
        <span className="text-[11px] text-muted-foreground">{hint}</span>
      ) : null}
    </div>
  );
}

/**
 * Backtest configuration. Strategy is applied by the backend reference
 * backtest; asset, date range, and initial capital are fixed by the backend, so
 * they are shown disabled (never sent as ignored inputs).
 */
export function BacktestForm({
  strategy,
  strategies,
  onStrategyChange,
  onRun,
  running,
}: BacktestFormProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Configuration</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Field label="Strategy">
          <Select value={strategy} onValueChange={onStrategyChange}>
            <SelectTrigger aria-label="Strategy">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {strategies.map((option) => (
                <SelectItem key={option} value={option}>
                  {strategyLabel(option)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>

        <Field label="Asset" hint="Backend reference backtest runs on BTC only.">
          <Select value="BTC" disabled>
            <SelectTrigger aria-label="Asset">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="BTC">BTC</SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <Field
          label="Date Range"
          hint="Fixed historical window — custom ranges are not supported by the backend."
        >
          <div className="grid grid-cols-2 gap-2">
            <Input type="date" aria-label="From date" disabled />
            <Input type="date" aria-label="To date" disabled />
          </div>
        </Field>

        <Field label="Initial Capital" hint="Fixed at $10,000 by the backend.">
          <Input aria-label="Initial capital" value="$10,000.00" disabled readOnly />
        </Field>

        <Button onClick={onRun} loading={running} className="mt-1 w-full">
          {running ? null : <Play className="h-4 w-4" aria-hidden="true" />}
          {running ? 'Running…' : 'Run Backtest'}
        </Button>

        <p className="text-xs text-muted-foreground">
          Only the strategy is applied. Running briefly switches the engine to
          backtest mode and restores live afterward.
        </p>
      </CardContent>
    </Card>
  );
}
