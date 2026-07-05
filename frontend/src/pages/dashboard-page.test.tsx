import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@/theme/theme-provider';
import type { DashboardState } from '@/services';
import DashboardPage from './dashboard-page';

const now = Date.now();

const SAMPLE_STATE: DashboardState = {
  status: 'live',
  mode: 'UI-4 runtime',
  updated_at: new Date(now).toISOString(),
  market: { symbol: 'BTC', price: 100 },
  portfolio: { cash: 9500, asset: 5, equity: 10025.5, pnl: 25.5 },
  selected_strategy: 'A',
  strategies: { A: { score: 1, weight: 1, updates: 1, adaptive: 1 } },
  trades: [
    {
      id: 't1',
      time: new Date(now).toISOString(),
      strategy: 'A',
      action: 'BUY',
      symbol: 'BTC',
      price: 99.5,
      amount: 1,
    },
  ],
  equity_curve: [
    { time: new Date(now - 3000).toISOString(), value: 10000 },
    { time: new Date(now - 2000).toISOString(), value: 10010 },
    { time: new Date(now).toISOString(), value: 10025.5 },
  ],
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

function renderDashboard() {
  return render(
    <ThemeProvider>
      <DashboardPage />
    </ThemeProvider>,
  );
}

describe('DashboardPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders live data from /api/state', async () => {
    stubFetch((url) => (url.includes('/api/state') ? SAMPLE_STATE : { status: 'ok' }));
    renderDashboard();

    // Total Assets primary in RM (10025.5 × 4.7 placeholder rate).
    expect(await screen.findByText(/RM/)).toBeInTheDocument();
    // Active strategy resolved from state.
    expect((await screen.findAllByText('Strategy A')).length).toBeGreaterThan(0);
    // Recent trade rendered.
    expect(await screen.findByText('BUY')).toBeInTheDocument();
    // Chart + table titles present.
    expect(screen.getByText('Equity Curve')).toBeInTheDocument();
    expect(screen.getByText('Recent Trades')).toBeInTheDocument();
    // Period PnL cards honestly report unavailable.
    expect(
      (await screen.findAllByText('Pending analytics endpoint')).length,
    ).toBe(2);
  });

  it('shows an error banner when the backend is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    renderDashboard();
    expect(
      await screen.findByText('Unable to reach the NeXo backend'),
    ).toBeInTheDocument();
  });
});
