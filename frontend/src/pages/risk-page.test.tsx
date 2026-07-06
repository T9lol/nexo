import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@/theme/theme-provider';
import type { DashboardState } from '@/services';
import RiskPage from './risk-page';

function makeState(overrides?: Partial<DashboardState>): DashboardState {
  return {
    status: 'live',
    mode: 'UI-4 runtime',
    updated_at: new Date().toISOString(),
    market: { symbol: 'BTC', price: 100 },
    portfolio: { cash: 9800, asset: 2, equity: 10000, pnl: 0 },
    selected_strategy: 'A',
    strategies: { A: { score: 1, weight: 1, updates: 1, adaptive: 1 } },
    trades: [],
    equity_curve: [],
    control: {
      trading_enabled: true,
      strategy_policy: 'auto',
      effective_strategy: 'A',
      manual_override: false,
      position_limit_enabled: true,
      mode: 'live',
      environment: 'local-simulation',
      allowed: { strategy_policy: ['auto'], mode: ['live'] },
    },
    ...overrides,
  };
}

function stubFetch(state: DashboardState) {
  const mock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    const body = url.includes('/api/state') ? state : state.control;
    return { ok: true, status: 200, json: async () => body };
  });
  vi.stubGlobal('fetch', mock);
  return mock;
}

function renderPage() {
  return render(
    <ThemeProvider>
      <RiskPage />
    </ThemeProvider>,
  );
}

describe('RiskPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders overview, exposure, alerts, and controls', async () => {
    stubFetch(makeState());
    renderPage();

    expect(
      await screen.findByRole('heading', { name: 'Current Exposure' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Risk Alerts' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Emergency Stop' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Risk Configuration' }),
    ).toBeInTheDocument();
    // Real control present.
    expect(
      screen.getByRole('switch', { name: 'Position-limit policy' }),
    ).toBeInTheDocument();
    // Honest disabled config + disabled save.
    expect(screen.getByLabelText('Daily Loss Limit')).toBeDisabled();
    expect(screen.getByLabelText('Stop Loss')).toBeDisabled();
    expect(
      screen.getByRole('button', { name: 'Save configuration' }),
    ).toBeDisabled();
  });

  it('surfaces derived alerts when trading is paused', async () => {
    stubFetch(
      makeState({
        control: { ...makeState().control, trading_enabled: false },
      }),
    );
    renderPage();

    // "Trading paused" appears both as an alert and the emergency-card badge.
    expect((await screen.findAllByText('Trading paused')).length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByRole('button', { name: 'Resume Trading' }),
    ).toBeInTheDocument();
  });

  it('confirms and sends the emergency stop command', async () => {
    const mock = stubFetch(makeState());
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: 'Stop Trading' }));
    // Confirmation dialog opens.
    expect(await screen.findByText('Stop all trading?')).toBeInTheDocument();

    const dialog = screen.getByRole('dialog');
    await userEvent.click(within(dialog).getByRole('button', { name: 'Stop Trading' }));

    await waitFor(() =>
      expect(mock).toHaveBeenCalledWith(
        expect.stringContaining('/api/control/trading'),
        expect.objectContaining({ method: 'POST' }),
      ),
    );
  });

  it('shows an error banner when the backend is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    renderPage();
    expect(
      await screen.findByText('Unable to reach the NeXo backend'),
    ).toBeInTheDocument();
  });
});
