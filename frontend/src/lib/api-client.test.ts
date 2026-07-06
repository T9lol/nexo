import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiFetch } from './api-client';

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns parsed JSON on success', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ hello: 'world' }),
      }),
    );
    await expect(apiFetch('/x')).resolves.toEqual({ hello: 'world' });
  });

  it('throws an ApiError with the status on a non-ok response', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue({ ok: false, status: 503, json: async () => ({}) }),
    );
    await expect(apiFetch('/x')).rejects.toMatchObject({
      name: 'ApiError',
      status: 503,
    });
  });

  it('throws an ApiError when the network request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    await expect(apiFetch('/x')).rejects.toBeInstanceOf(ApiError);
  });
});
