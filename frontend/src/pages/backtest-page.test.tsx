import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@/theme/theme-provider';
import type { ControlState, DashboardState } from '@/services';
import BacktestPage from './backtest-page';

const CONTROL: ControlState = {
  trading_enabled: true,
  strategy_policy: 'auto',
  effective_strategy: 'A',
  manual_override: false,
  position_limit_enabled: true,
  mode: 'live',
  environment: 'local-simulation',
  allowed: { strategy_policy: ['auto', 'A', 'B'], mode: ['live', 'backtest'] },
};

const BACKTEST_SNAPSHOT: DashboardState = {
  status: 'live',
  mode: 'backtest review',
  updated_at: new Date().toISOString(),
  market: { symbol: 'BTC', price: 99 },
  portfolio: { cash: 99, asset: 0, equity: 99, pnl: -1 },
  selected_strategy: 'A',
  strategies: { A: { score: 1, weight: 1, updates: 1, adaptive: 1 } },
  trades: [
    {
      id: 'bt-1',
      time: new Date().toISOString(),
      strategy: 'A',
      action: 'BUY',
      symbol: 'BTC',
      price: 98,
      amount: 1,
    },
  ],
  equity_curve: [
    { time: new Date(Date.now() - 2000).toISOString(), value: 100 },
    { time: new Date(Date.now() - 1000).toISOString(), value: 110 },
    { time: new Date().toISOString(), value: 99 },
  ],
  control: { ...CONTROL, mode: 'backtest' },
};

function stubFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      const body = url.includes('/api/state') ? BACKTEST_SNAPSHOT : CONTROL;
      return { ok: true, status: 200, json: async () => body };
    }),
  );
}

function renderPage() {
  return render(
    <ThemeProvider>
      <BacktestPage />
    </ThemeProvider>,
  );
}

describe('BacktestPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('runs a backtest and renders results, charts, metrics, and trades', async () => {
    stubFetch();
    renderPage();

    // Before running: empty state + disabled export.
    expect(await screen.findByText('No backtest run yet')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Export report' }),
    ).toBeDisabled();

    await userEvent.click(screen.getByRole('button', { name: /Run Backtest/ }));

    // Results appear.
    expect(
      await screen.findByRole('heading', { name: 'Performance Metrics' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Equity Curve' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Drawdown' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Backtest Trades' }),
    ).toBeInTheDocument();
    // Real metric + honest unavailable metrics.
    expect(screen.getByText('Total Return')).toBeInTheDocument();
    expect(screen.getByText('No calendar time basis')).toBeInTheDocument();
    expect(screen.getByText('No per-trade PnL')).toBeInTheDocument();
    // Export now enabled.
    expect(
      screen.getByRole('button', { name: 'Export report' }),
    ).not.toBeDisabled();
  });

  it('shows a failed status when the backend is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    renderPage();

    await userEvent.click(screen.getByRole('button', { name: /Run Backtest/ }));
    expect(await screen.findByText('Failed')).toBeInTheDocument();
  });

  it('keeps asset, date range, and capital disabled (not sent to the backend)', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByLabelText('Initial capital')).toBeDisabled();
    expect(screen.getByLabelText('From date')).toBeDisabled();
    expect(screen.getByLabelText('To date')).toBeDisabled();
  });
});
