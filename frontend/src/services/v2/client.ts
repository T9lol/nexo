/**
 * v2 request helper: attaches the bearer token, unwraps the standardized
 * envelope, and transparently refreshes the access token once on a 401.
 */

import { ApiError, apiFetch } from '@/lib/api-client';
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from './auth-store';
import type { Envelope, TokenPair } from './types';

function jsonHeaders(extra?: HeadersInit): Record<string, string> {
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    ...(extra as Record<string, string>),
  };
}

async function tryRefresh(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  try {
    const res = await apiFetch<Envelope<TokenPair>>('/api/v2/auth/refresh', {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify({ refresh_token: refresh }),
    });
    setTokens(res.data.access_token, res.data.refresh_token);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

export async function v2Request<T>(
  path: string,
  init: RequestInit = {},
  allowRefresh = true,
): Promise<T> {
  const token = getAccessToken();
  const headers = jsonHeaders(init.headers);
  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    const res = await apiFetch<Envelope<T>>(path, { ...init, headers });
    return res.data;
  } catch (error) {
    if (
      allowRefresh &&
      error instanceof ApiError &&
      error.status === 401 &&
      getRefreshToken()
    ) {
      if (await tryRefresh()) return v2Request<T>(path, init, false);
    }
    throw error;
  }
}

export function v2Body(payload: unknown): string {
  return JSON.stringify(payload);
}
