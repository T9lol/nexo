import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
} from '@/components/ui';
import { PLACEHOLDER_USD_MYR_RATE, type FxPreference } from '@/services';

interface CurrencyCardProps {
  fx: FxPreference;
  onChange: (preference: FxPreference) => void;
}

function effectiveRate(fx: FxPreference): number {
  return fx.mode === 'manual' && fx.manualRate && fx.manualRate > 0
    ? fx.manualRate
    : PLACEHOLDER_USD_MYR_RATE;
}

export function CurrencyCard({ fx, onChange }: CurrencyCardProps) {
  const rate = effectiveRate(fx);
  const manual = fx.mode === 'manual';

  return (
    <Card>
      <CardHeader>
        <CardTitle>Currency & Exchange Rate</CardTitle>
        <CardDescription>
          Total assets are shown primarily in Ringgit (RM), with an approximate
          USD equivalent.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-center justify-between rounded-lg border border-border p-3 text-sm">
          <span className="text-muted-foreground">Primary currency</span>
          <span className="font-medium">MYR (RM) · USD approximate</span>
        </div>

        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium text-foreground">
            Exchange rate (USD → MYR)
          </span>
          <div
            className="flex flex-wrap gap-2"
            role="group"
            aria-label="Exchange rate mode"
          >
            <Button
              variant={!manual ? 'primary' : 'outline'}
              size="sm"
              aria-pressed={!manual}
              onClick={() =>
                onChange({ mode: 'automatic', manualRate: fx.manualRate })
              }
            >
              Automatic
            </Button>
            <Button
              variant={manual ? 'primary' : 'outline'}
              size="sm"
              aria-pressed={manual}
              onClick={() =>
                onChange({
                  mode: 'manual',
                  manualRate: fx.manualRate ?? PLACEHOLDER_USD_MYR_RATE,
                })
              }
            >
              Manual override
            </Button>
          </div>

          {manual ? (
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="fx-rate"
                className="text-xs text-muted-foreground"
              >
                Manual rate
              </label>
              <Input
                id="fx-rate"
                type="number"
                inputMode="decimal"
                step="0.01"
                min="0"
                value={fx.manualRate ?? ''}
                onChange={(event) => {
                  const parsed = Number(event.target.value);
                  onChange({
                    mode: 'manual',
                    manualRate:
                      event.target.value === '' || Number.isNaN(parsed)
                        ? null
                        : parsed,
                  });
                }}
                aria-label="Manual exchange rate"
                className="sm:w-[200px]"
              />
            </div>
          ) : null}

          <div className="mt-1 flex items-center gap-2 text-sm">
            <span className="tabular font-medium">
              1 USD ≈ {rate.toFixed(2)} MYR
            </span>
            <Badge variant={manual ? 'primary' : 'default'}>
              {manual ? 'Manual' : 'Placeholder'}
            </Badge>
          </div>
          <span className="text-[11px] text-muted-foreground">
            Automatic uses a static placeholder — there is no live FX source. A
            manual override is stored in this browser and applied across the
            terminal.
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
