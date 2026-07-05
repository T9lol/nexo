import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@/theme/theme-provider';
import type { DashboardState } from '@/services';
import PortfolioPage from './portfolio-page';

const now = Date.now();

const SAMPLE_STATE: DashboardState = {
  status: 'live',
  mode: 'UI-4 runtime',
  updated_at: new Date(now).toISOString(),
  market: { symbol: 'BTC', price: 100 },
  portfolio: { cash: 9500, asset: 5, equity: 10000, pnl: 25 },
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
    { time: new Date(now - 3000).toISOString(), value: 9990 },
    { time: new Date(now - 2000).toISOString(), value: 9995 },
    { time: new Date(now).toISOString(), value: 10000 },
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

function renderPage() {
  return render(
    <ThemeProvider>
      <PortfolioPage />
    </ThemeProvider>,
  );
}

describe('PortfolioPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders holdings, allocation, value, and detail from real state', async () => {
    stubFetch((url) => (url.includes('/api/state') ? SAMPLE_STATE : { status: 'ok' }));
    renderPage();

    // Total value in RM (summary).
    expect(await screen.findByText(/RM/)).toBeInTheDocument();
    // Holdings table shows the derived asset.
    expect((await screen.findAllByText('Bitcoin')).length).toBeGreaterThan(0);
    // Section card titles (rendered as headings) are present.
    expect(
      screen.getByRole('heading', { name: 'Holdings' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Allocation' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Portfolio Value' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Asset Detail' }),
    ).toBeInTheDocument();
  });

  it('filters holdings via the search box', async () => {
    stubFetch((url) => (url.includes('/api/state') ? SAMPLE_STATE : { status: 'ok' }));
    renderPage();

    const search = await screen.findByLabelText('Search holdings');
    await userEvent.type(search, 'zzz');

    expect(await screen.findByText('No matches')).toBeInTheDocument();
  });

  it('shows an error banner when the backend is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    renderPage();
    expect(
      await screen.findByText('Unable to reach the NeXo backend'),
    ).toBeInTheDocument();
  });
});
