import { apiFetch } from '@/lib/api-client';
import type { DashboardState, Trade } from './types';

/** Existing backend endpoint: full dashboard state snapshot. */
export function getDashboardState(
  signal?: AbortSignal,
): Promise<DashboardState> {
  return apiFetch<DashboardState>('/api/state', { signal });
}

/** Existing backend endpoint: recent executed trades. */
export function getTrades(signal?: AbortSignal): Promise<Trade[]> {
  return apiFetch<Trade[]>('/api/trades', { signal });
}

export interface HealthResponse {
  status: string;
}

/** Existing backend endpoint: liveness probe. */
export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/api/health', { signal });
}
