import { describe, expect, it } from 'vitest';
import { formatMYR, formatSignedUSD, formatUSD, usdToMyr } from './currency';

describe('currency', () => {
  it('formats MYR with the RM symbol', () => {
    const output = formatMYR(1234.5);
    expect(output).toContain('RM');
    expect(output).toContain('1,234.50');
  });

  it('formats USD with the $ symbol', () => {
    const output = formatUSD(1234.5);
    expect(output).toContain('$');
    expect(output).toContain('1,234.50');
  });

  it('adds an explicit sign for gains', () => {
    expect(formatSignedUSD(25)).toMatch(/^\+/);
    expect(formatSignedUSD(-25)).toMatch(/^-/);
  });

  it('converts USD to MYR by the given rate', () => {
    expect(usdToMyr(100, 4.7)).toBeCloseTo(470);
  });
});
