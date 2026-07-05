import { History } from 'lucide-react';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  Input,
  PageHeader,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';

export default function BacktestPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Backtest"
        description="Configure a deterministic historical replay and review the results."
      />

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="bt-strategy"
                className="text-sm font-medium text-foreground"
              >
                Strategy
              </label>
              <Select disabled>
                <SelectTrigger id="bt-strategy">
                  <SelectValue placeholder="Strategy A" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="a">Strategy A</SelectItem>
                  <SelectItem value="b">Strategy B</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="bt-capital"
                className="text-sm font-medium text-foreground"
              >
                Starting capital
              </label>
              <Input
                id="bt-capital"
                inputMode="numeric"
                placeholder="10,000"
                disabled
              />
            </div>
            <Button disabled className="mt-1">
              Run backtest
            </Button>
            <p className="text-xs text-muted-foreground">
              Controls are placeholders in Sprint 1 and are not yet wired to the
              engine.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent>
            <EmptyState
              icon={History}
              title="No backtest run yet"
              description="Run a backtest to review the equity curve, trades, and summary metrics here."
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
