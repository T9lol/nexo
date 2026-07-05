/**
 * Foreign-exchange service — PLACEHOLDER.
 *
 * The backend does not yet expose an FX endpoint. This returns a static,
 * clearly-flagged approximate USD→MYR rate so the Total Assets card can present
 * a Ringgit value. It invents no trading data; swap the implementation for a
 * real endpoint call when one exists (the signature can stay the same).
 */

export interface ExchangeRate {
  base: 'USD';
  quote: 'MYR';
  rate: number;
  /** True while this is a static placeholder rather than a live quote. */
  isPlaceholder: boolean;
  asOf: string;
}

/** Approximate USD→MYR rate used until a live FX source is wired up. */
export const PLACEHOLDER_USD_MYR_RATE = 4.7;

export function getUsdMyrRate(_signal?: AbortSignal): Promise<ExchangeRate> {
  return Promise.resolve({
    base: 'USD',
    quote: 'MYR',
    rate: PLACEHOLDER_USD_MYR_RATE,
    isPlaceholder: true,
    asOf: new Date().toISOString(),
  });
}
