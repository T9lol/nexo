import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@/theme/theme-provider';
import type { DashboardState } from '@/services';
import StrategiesPage from './strategies-page';

const SAMPLE_STATE: DashboardState = {
  status: 'live',
  mode: 'UI-4 runtime',
  updated_at: new Date().toISOString(),
  market: { symbol: 'BTC', price: 100 },
  portfolio: { cash: 9500, asset: 5, equity: 10000, pnl: 25 },
  selected_strategy: 'A',
  strategies: {
    A: { score: 30, weight: 1.2, updates: 10, adaptive: 36 },
    B: { score: 20, weight: 1.0, updates: 5, adaptive: 20 },
  },
  trades: [
    { id: '1', time: new Date().toISOString(), strategy: 'A', action: 'BUY', symbol: 'BTC', price: 99, amount: 1 },
    { id: '2', time: new Date().toISOString(), strategy: 'B', action: 'SELL', symbol: 'BTC', price: 101, amount: 1 },
  ],
  equity_curve: [],
  control: {
    trading_enabled: true,
    strategy_policy: 'auto',
    effective_strategy: 'A',
    manual_override: false,
    position_limit_enabled: true,
    mode: 'live',
    environment: 'local-simulation',
    allowed: { strategy_policy: ['auto', 'A', 'B'], mode: ['live', 'backtest'] },
  },
};

function stubFetch(handler: (url: string) => unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      status: 200,
      json: async () => handler(String(input)),
    })),
  );
}

function renderPage() {
  return render(
    <ThemeProvider>
      <StrategiesPage />
    </ThemeProvider>,
  );
}

describe('StrategiesPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('lists strategies with metrics, detail, status, and comparison', async () => {
    stubFetch((url) => (url.includes('/api/state') ? SAMPLE_STATE : { status: 'ok' }));
    renderPage();

    // Strategy list rows.
    expect((await screen.findAllByText('Strategy A')).length).toBeGreaterThan(0);
    expect(screen.getAllByText('Strategy B').length).toBeGreaterThan(0);
    // Status indicator (A is active).
    expect(screen.getAllByText('Active').length).toBeGreaterThan(0);
    // Card sections.
    expect(screen.getByRole('heading', { name: 'Strategies' })).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Strategy Detail' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Performance Comparison' }),
    ).toBeInTheDocument();
    // Performance score shown in the detail.
    expect(screen.getAllByText('Performance Score').length).toBeGreaterThan(0);
  });

  it('shows honest unavailable metrics and a disabled enable toggle', async () => {
    stubFetch((url) => (url.includes('/api/state') ? SAMPLE_STATE : { status: 'ok' }));
    renderPage();

    // PnL / Win Rate / Max Drawdown are honestly unavailable.
    expect(
      (await screen.findAllByText('No per-strategy endpoint')).length,
    ).toBe(3);
    // Enable/disable toggle is present but disabled.
    const toggle = screen.getByRole('switch', { name: 'Enable strategy A' });
    expect(toggle).toBeDisabled();
  });

  it('shows an error banner when the backend is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    renderPage();
    expect(
      await screen.findByText('Unable to reach the NeXo backend'),
    ).toBeInTheDocument();
  });
});
