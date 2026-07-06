/**
 * Browser-local settings. These are UI preferences stored only in this browser
 * (localStorage) — there is no user/account backend, so nothing here is a
 * server-side record. Notification delivery and API-key management require a
 * backend that does not exist yet and are reported as unavailable.
 */

const SETTINGS_STORAGE_KEY = 'nexo-settings';

export interface LocalSettings {
  /** Cosmetic label shown in this browser only (not a server account). */
  displayName: string;
  /** UI language code. Only 'en' is currently available. */
  language: string;
}

export const DEFAULT_LOCAL_SETTINGS: LocalSettings = {
  displayName: '',
  language: 'en',
};

export const AVAILABLE_LANGUAGES = [{ code: 'en', label: 'English' }] as const;

export function readLocalSettings(): LocalSettings {
  try {
    const raw = window.localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!raw) return DEFAULT_LOCAL_SETTINGS;
    const parsed = JSON.parse(raw) as Partial<LocalSettings>;
    return {
      displayName:
        typeof parsed.displayName === 'string' ? parsed.displayName : '',
      language: typeof parsed.language === 'string' ? parsed.language : 'en',
    };
  } catch {
    return DEFAULT_LOCAL_SETTINGS;
  }
}

export function writeLocalSettings(
  patch: Partial<LocalSettings>,
): LocalSettings {
  const next = { ...readLocalSettings(), ...patch };
  try {
    window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(next));
  } catch {
    /* storage unavailable — keep in-memory only */
  }
  return next;
}

/** Notification delivery is not implemented (no backend). */
export const NOTIFICATION_DELIVERY_AVAILABLE = false;

/** API-key management requires a backend key service (none exists). Secrets are
 * never stored in the browser. */
export const API_KEY_MANAGEMENT_AVAILABLE = false;
