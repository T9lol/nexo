/**
 * Foreign-exchange service.
 *
 * The backend does not expose a live FX endpoint. The rate used for the RM
 * display therefore comes from a browser-local preference:
 *  - "automatic": a static, clearly-flagged placeholder (no live source).
 *  - "manual": a user-provided override, stored locally only.
 *
 * This is an honest display preference — it never fabricates trading data or
 * backend behaviour. Swap the "automatic" branch for a real endpoint call when
 * one exists.
 */

export interface ExchangeRate {
  base: 'USD';
  quote: 'MYR';
  rate: number;
  /** True while this is a static placeholder rather than a live/manual quote. */
  isPlaceholder: boolean;
  source: 'placeholder' | 'manual';
  asOf: string;
}

/** Approximate USD→MYR rate used until a live FX source is wired up. */
export const PLACEHOLDER_USD_MYR_RATE = 4.7;

const FX_STORAGE_KEY = 'nexo-fx';

export type FxMode = 'automatic' | 'manual';

export interface FxPreference {
  mode: FxMode;
  /** USD→MYR rate used when mode is 'manual'. */
  manualRate: number | null;
}

export const DEFAULT_FX_PREFERENCE: FxPreference = {
  mode: 'automatic',
  manualRate: null,
};

export function readFxPreference(): FxPreference {
  try {
    const raw = window.localStorage.getItem(FX_STORAGE_KEY);
    if (!raw) return DEFAULT_FX_PREFERENCE;
    const parsed = JSON.parse(raw) as Partial<FxPreference>;
    const mode: FxMode = parsed.mode === 'manual' ? 'manual' : 'automatic';
    const manualRate =
      typeof parsed.manualRate === 'number' && parsed.manualRate > 0
        ? parsed.manualRate
        : null;
    return { mode, manualRate };
  } catch {
    return DEFAULT_FX_PREFERENCE;
  }
}

export function writeFxPreference(preference: FxPreference): void {
  try {
    window.localStorage.setItem(FX_STORAGE_KEY, JSON.stringify(preference));
  } catch {
    /* storage unavailable — keep in-memory only */
  }
}

/** Resolve the effective USD→MYR rate from the stored preference. */
export function getUsdMyrRate(_signal?: AbortSignal): Promise<ExchangeRate> {
  const preference = readFxPreference();
  if (
    preference.mode === 'manual' &&
    preference.manualRate &&
    preference.manualRate > 0
  ) {
    return Promise.resolve({
      base: 'USD',
      quote: 'MYR',
      rate: preference.manualRate,
      isPlaceholder: false,
      source: 'manual',
      asOf: new Date().toISOString(),
    });
  }
  return Promise.resolve({
    base: 'USD',
    quote: 'MYR',
    rate: PLACEHOLDER_USD_MYR_RATE,
    isPlaceholder: true,
    source: 'placeholder',
    asOf: new Date().toISOString(),
  });
}
