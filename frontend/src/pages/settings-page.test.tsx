import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@/theme/theme-provider';
import SettingsPage from './settings-page';

function stubFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      const body = url.includes('/api/health')
        ? { status: 'ok' }
        : {
            status: 'live',
            mode: 'UI-4 runtime',
            updated_at: new Date().toISOString(),
            market: { symbol: 'BTC', price: 100 },
            portfolio: { cash: 9500, asset: 5, equity: 10000, pnl: 25 },
            selected_strategy: 'A',
            strategies: {},
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
          };
      return { ok: true, status: 200, json: async () => body };
    }),
  );
}

function renderPage() {
  return render(
    <ThemeProvider>
      <SettingsPage />
    </ThemeProvider>,
  );
}

describe('SettingsPage', () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it('renders all settings sections with honest disabled states', async () => {
    stubFetch();
    renderPage();

    expect(
      await screen.findByRole('heading', { name: 'User Profile' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Appearance & Language' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Currency & Exchange Rate' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'API Keys' }),
    ).toBeInTheDocument();

    // Theme control works.
    await userEvent.click(screen.getByRole('button', { name: 'Dark' }));
    expect(document.documentElement).toHaveClass('dark');

    // API key management + notifications are disabled.
    expect(
      screen.getByRole('button', { name: 'Create API key' }),
    ).toBeDisabled();
    expect(screen.getByRole('switch', { name: 'Trade fills' })).toBeDisabled();
  });

  it('supports a manual exchange-rate override', async () => {
    stubFetch();
    renderPage();

    // Default is the automatic placeholder.
    expect(await screen.findByText('Placeholder')).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole('button', { name: 'Manual override' }),
    );
    const input = screen.getByLabelText('Manual exchange rate');
    await userEvent.clear(input);
    await userEvent.type(input, '4.55');

    expect(screen.getByText('Manual')).toBeInTheDocument();
    expect(screen.getByText(/1 USD ≈ 4\.55 MYR/)).toBeInTheDocument();
  });

  it('shows real system information from the backend', async () => {
    stubFetch();
    renderPage();
    // Environment appears in both the profile and system-info tiles.
    expect(
      (await screen.findAllByText('local-simulation')).length,
    ).toBeGreaterThan(0);
  });
});
