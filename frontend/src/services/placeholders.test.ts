import { describe, expect, it } from 'vitest';
import { getPnlBreakdown } from './analytics-service';
import { getUsdMyrRate } from './fx-service';

describe('fx-service (placeholder)', () => {
  it('returns a flagged placeholder USD→MYR rate', async () => {
    const rate = await getUsdMyrRate();
    expect(rate.base).toBe('USD');
    expect(rate.quote).toBe('MYR');
    expect(rate.rate).toBeGreaterThan(0);
    expect(rate.isPlaceholder).toBe(true);
  });
});

describe('analytics-service (placeholder)', () => {
  it('reports period PnL as unavailable rather than inventing values', async () => {
    const breakdown = await getPnlBreakdown();
    expect(breakdown.today.available).toBe(false);
    expect(breakdown.today.value).toBeNull();
    expect(breakdown.month.available).toBe(false);
    expect(breakdown.month.value).toBeNull();
  });
});
