import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { clearTokens, getAccessToken } from './auth-store';
import * as auth from './auth';
import * as wallet from './wallet';

interface Call {
  url: string;
  init: RequestInit;
}

function envelope(data: unknown) {
  return { ok: true, status: 200, json: async () => ({ success: true, data }) };
}

describe('v2 API client', () => {
  let calls: Call[];

  beforeEach(() => {
    localStorage.clear();
    clearTokens();
    calls = [];
  });

  afterEach(() => vi.unstubAllGlobals());

  function stub(handler: (call: Call) => unknown) {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: RequestInfo | URL, init: RequestInit = {}) => {
        const call = { url: String(url), init };
        calls.push(call);
        return handler(call);
      }),
    );
  }

  it('login stores tokens and returns the user', async () => {
    stub(() =>
      envelope({
        access_token: 'a1',
        refresh_token: 'r1',
        token_type: 'bearer',
        expires_in: 900,
        user: { id: 1, email: 'u@test.co', role: 'user', is_active: true },
      }),
    );

    const result = await auth.login('u@test.co', 'password123');
    expect(result.user.email).toBe('u@test.co');
    expect(getAccessToken()).toBe('a1');
    expect(calls[0]?.url).toContain('/api/v2/auth/login');
  });

  it('attaches the bearer token on authenticated requests', async () => {
    stub((call) => {
      if (call.url.includes('/login')) {
        return envelope({
          access_token: 'a1',
          refresh_token: 'r1',
          token_type: 'bearer',
          expires_in: 900,
          user: { id: 1, email: 'u@test.co', role: 'user', is_active: true },
        });
      }
      return envelope({
        balance: 100,
        frozen_balance: 0,
        available: 100,
        currency: 'MYR',
      });
    });

    await auth.login('u@test.co', 'password123');
    await wallet.getWallet();

    const walletCall = calls.find((c) => c.url.includes('/api/v2/wallet'));
    const headers = (walletCall?.init.headers ?? {}) as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer a1');
  });

  it('refreshes the token once on a 401 and retries', async () => {
    // Seed tokens as if already logged in.
    stub(() =>
      envelope({
        access_token: 'a1',
        refresh_token: 'r1',
        token_type: 'bearer',
        expires_in: 900,
        user: { id: 1, email: 'u@test.co', role: 'user', is_active: true },
      }),
    );
    await auth.login('u@test.co', 'password123');

    let walletHits = 0;
    stub((call) => {
      if (call.url.includes('/api/v2/wallet')) {
        walletHits += 1;
        if (walletHits === 1)
          return { ok: false, status: 401, json: async () => ({}) };
        return envelope({
          balance: 50,
          frozen_balance: 0,
          available: 50,
          currency: 'MYR',
        });
      }
      if (call.url.includes('/api/v2/auth/refresh')) {
        return envelope({
          access_token: 'a2',
          refresh_token: 'r2',
          token_type: 'bearer',
          expires_in: 900,
          user: { id: 1, email: 'u@test.co', role: 'user', is_active: true },
        });
      }
      return envelope({});
    });

    const w = await wallet.getWallet();
    expect(w.available).toBe(50);
    expect(walletHits).toBe(2); // original + retry
    expect(getAccessToken()).toBe('a2'); // rotated
  });
});
