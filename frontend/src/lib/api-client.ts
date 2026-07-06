/**
 * Minimal typed fetch wrapper for the NeXo backend. All service modules go
 * through this so error handling and the base URL live in one place.
 */

const API_BASE = (
  import.meta.env.VITE_API_URL ??
  import.meta.env.VITE_API_BASE_URL ??
  ''
).replace(/\/$/, '');

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { Accept: 'application/json' },
      ...init,
    });
  } catch (cause) {
    if ((cause as Error).name === 'AbortError') throw cause;
    throw new ApiError('Network request failed — is the backend running?');
  }

  if (!response.ok) {
    throw new ApiError(`Request failed (${response.status})`, response.status);
  }

  return (await response.json()) as T;
}
