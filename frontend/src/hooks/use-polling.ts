import { useCallback, useEffect, useRef, useState } from 'react';

export type AsyncStatus = 'loading' | 'success' | 'error';

export interface PollingResult<T> {
  data: T | null;
  error: Error | null;
  status: AsyncStatus;
  /** Epoch ms of the last successful fetch, or null. */
  lastUpdated: number | null;
  refetch: () => void;
}

/**
 * Polls an async fetcher on an interval with abort handling. Once data has been
 * loaded, later failures keep the last good data (status stays `success`) and
 * surface via `error` so the UI can show a "stale" indicator instead of
 * blanking out. Skips ticks while the tab is hidden.
 */
export function usePolling<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  intervalMs = 5000,
): PollingResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [status, setStatus] = useState<AsyncStatus>('loading');
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const [manualTrigger, setManualTrigger] = useState(0);

  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refetch = useCallback(() => setManualTrigger((n) => n + 1), []);

  useEffect(() => {
    const controller = new AbortController();

    const tick = async () => {
      try {
        const result = await fetcherRef.current(controller.signal);
        if (controller.signal.aborted) return;
        setData(result);
        setError(null);
        setStatus('success');
        setLastUpdated(Date.now());
      } catch (caught) {
        if (controller.signal.aborted) return;
        if ((caught as Error).name === 'AbortError') return;
        setError(caught as Error);
        setStatus((prev) => (prev === 'success' ? 'success' : 'error'));
      }
    };

    void tick();
    const id = window.setInterval(() => {
      if (!document.hidden) void tick();
    }, intervalMs);

    return () => {
      controller.abort();
      window.clearInterval(id);
    };
  }, [intervalMs, manualTrigger]);

  return { data, error, status, lastUpdated, refetch };
}
