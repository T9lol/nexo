/**
 * Access/refresh token store for the v2 SaaS API. Tokens are held in memory and
 * mirrored to localStorage so a session survives a page reload. No business
 * logic — just credential storage.
 */

const ACCESS_KEY = 'nexo_v2_access';
const REFRESH_KEY = 'nexo_v2_refresh';

let accessToken: string | null = readStorage(ACCESS_KEY);
let refreshToken: string | null = readStorage(REFRESH_KEY);

function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string | null): void {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    /* storage unavailable (SSR / private mode) — memory only */
  }
}

export function setTokens(access: string, refresh: string): void {
  accessToken = access;
  refreshToken = refresh;
  writeStorage(ACCESS_KEY, access);
  writeStorage(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  accessToken = null;
  refreshToken = null;
  writeStorage(ACCESS_KEY, null);
  writeStorage(REFRESH_KEY, null);
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function getRefreshToken(): string | null {
  return refreshToken;
}

export function isAuthenticated(): boolean {
  return accessToken !== null;
}
