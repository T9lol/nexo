/**
 * Currency helpers. The terminal presents Total Assets primarily in Malaysian
 * Ringgit (MYR / "RM") with an approximate USD equivalent. The backend is
 * USD-denominated; MYR is derived via an exchange rate supplied by the FX
 * service.
 */

const myrFormatter = new Intl.NumberFormat('ms-MY', {
  style: 'currency',
  currency: 'MYR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const usdFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatMYR(value: number): string {
  return myrFormatter.format(value);
}

export function formatUSD(value: number): string {
  return usdFormatter.format(value);
}

export function formatSignedUSD(value: number): string {
  return `${value >= 0 ? '+' : ''}${usdFormatter.format(value)}`;
}

/** Convert a USD amount to MYR using the given USD→MYR rate. */
export function usdToMyr(usd: number, usdMyrRate: number): number {
  return usd * usdMyrRate;
}
