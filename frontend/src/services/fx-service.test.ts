import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  DEFAULT_FX_PREFERENCE,
  PLACEHOLDER_USD_MYR_RATE,
  getUsdMyrRate,
  readFxPreference,
  writeFxPreference,
} from './fx-service';

describe('fx preference', () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => localStorage.clear());

  it('defaults to the automatic placeholder', async () => {
    expect(readFxPreference()).toEqual(DEFAULT_FX_PREFERENCE);
    const rate = await getUsdMyrRate();
    expect(rate.isPlaceholder).toBe(true);
    expect(rate.source).toBe('placeholder');
    expect(rate.rate).toBe(PLACEHOLDER_USD_MYR_RATE);
  });

  it('uses a manual override when set', async () => {
    writeFxPreference({ mode: 'manual', manualRate: 4.5 });
    expect(readFxPreference()).toEqual({ mode: 'manual', manualRate: 4.5 });

    const rate = await getUsdMyrRate();
    expect(rate.rate).toBe(4.5);
    expect(rate.isPlaceholder).toBe(false);
    expect(rate.source).toBe('manual');
  });

  it('falls back to the placeholder for an invalid manual rate', async () => {
    writeFxPreference({ mode: 'manual', manualRate: 0 });
    expect(readFxPreference().manualRate).toBeNull();
    const rate = await getUsdMyrRate();
    expect(rate.isPlaceholder).toBe(true);
  });
});
