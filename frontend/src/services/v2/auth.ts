/** v2 authentication service. */

import { clearTokens, getRefreshToken, setTokens } from './auth-store';
import { v2Body, v2Request } from './client';
import type { TokenPair, User } from './types';

export async function register(email: string, password: string): Promise<User> {
  return v2Request<User>('/api/v2/auth/register', {
    method: 'POST',
    body: v2Body({ email, password }),
  });
}

export async function login(
  email: string,
  password: string,
): Promise<TokenPair> {
  const tokens = await v2Request<TokenPair>('/api/v2/auth/login', {
    method: 'POST',
    body: v2Body({ email, password }),
  });
  setTokens(tokens.access_token, tokens.refresh_token);
  return tokens;
}

export async function logout(): Promise<void> {
  const refresh = getRefreshToken();
  if (refresh) {
    try {
      await v2Request('/api/v2/auth/logout', {
        method: 'POST',
        body: v2Body({ refresh_token: refresh }),
      });
    } catch {
      /* revoke best-effort; clear locally regardless */
    }
  }
  clearTokens();
}

export async function me(): Promise<User> {
  return v2Request<User>('/api/v2/auth/me');
}
