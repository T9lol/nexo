import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@/theme/theme-provider';
import AdminPage from './admin-page';

function stubFetch(healthy = true) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      const body = url.includes('/api/health')
        ? { status: healthy ? 'ok' : 'degraded' }
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
      <AdminPage />
    </ThemeProvider>,
  );
}

describe('AdminPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows real system health and honest unavailable admin panels', async () => {
    stubFetch(true);
    renderPage();

    // Future-scope notice.
    expect(
      await screen.findByText('Admin features are future scope'),
    ).toBeInTheDocument();

    // Real system health.
    expect(
      screen.getByRole('heading', { name: 'System Health' }),
    ).toBeInTheDocument();
    expect(await screen.findByText('Healthy')).toBeInTheDocument();

    // All seven admin panels present and marked unavailable (no fabricated data).
    for (const title of [
      'User Management',
      'KYC Review',
      'Deposit Approval',
      'Withdrawal Approval',
      'Audit Logs',
      'Feature Flags',
      'Maintenance Mode',
    ]) {
      expect(
        screen.getByRole('heading', { name: title }),
      ).toBeInTheDocument();
    }
    expect(screen.getAllByText('Unavailable')).toHaveLength(7);
  });
});
