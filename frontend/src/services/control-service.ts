import { apiFetch } from '@/lib/api-client';
import type { ControlState } from './types';

/** Runtime control endpoints (existing backend). */

export function getControl(signal?: AbortSignal): Promise<ControlState> {
  return apiFetch<ControlState>('/api/control', { signal });
}

function postControl(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): Promise<ControlState> {
  return apiFetch<ControlState>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });
}

/** Set the routing policy ('auto' | 'A' | 'B'). Respected by the backtest. */
export function setStrategyPolicy(
  policy: string,
  signal?: AbortSignal,
): Promise<ControlState> {
  return postControl('/api/control/strategy', { policy }, signal);
}

/** Switch runtime mode ('live' | 'backtest'). */
export function setRuntimeMode(
  mode: 'live' | 'backtest',
  signal?: AbortSignal,
): Promise<ControlState> {
  return postControl('/api/control/mode', { mode }, signal);
}
