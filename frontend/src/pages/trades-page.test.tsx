import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider } from '@/theme/theme-provider';
import type { Trade } from '@/services';
import TradesPage from './trades-page';

const NOW = Date.now();

const TRADES: Trade[] = Array.from({ length: 12 }, (_, i) => ({
  id: `t${i}`,
  time: new Date(NOW - i * 60_000).toISOString(),
  strategy: i % 2 ? 'A' : 'B',
  action: i % 2 ? 'BUY' : 'SELL',
  symbol: i % 3 === 0 ? 'ETH' : 'BTC',
  price: 100 + i,
  amount: 1,
}));

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
      <TradesPage />
    </ThemeProvider>,
  );
}

describe('TradesPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders a paginated table with badges, unavailable fee/PnL, and export', async () => {
    stubFetch((url) =>
      url.includes('/api/trades') ? TRADES : { status: 'ok' },
    );
    renderPage();

    // Badges + status.
    expect((await screen.findAllByText('BUY')).length).toBeGreaterThan(0);
    expect(screen.getAllByText('Filled').length).toBeGreaterThan(0);
    // Fee / Realized PnL are honestly unavailable ("—").
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
    // Export action present.
    expect(
      screen.getByRole('button', { name: 'Export CSV' }),
    ).toBeInTheDocument();
    // Pagination: 12 rows, default page size 10 => 2 pages.
    expect(screen.getByText('Showing 1–10 of 12')).toBeInTheDocument();
    expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();
  });

  it('advances to the next page', async () => {
    stubFetch((url) =>
      url.includes('/api/trades') ? TRADES : { status: 'ok' },
    );
    renderPage();

    await screen.findByText('Showing 1–10 of 12');
    await userEvent.click(screen.getByRole('button', { name: 'Next page' }));
    expect(screen.getByText('Showing 11–12 of 12')).toBeInTheDocument();
  });

  it('filters via the search box', async () => {
    stubFetch((url) =>
      url.includes('/api/trades') ? TRADES : { status: 'ok' },
    );
    renderPage();

    const search = await screen.findByLabelText('Search trades');
    await userEvent.type(search, 'ETH'); // 4 of the 12 are ETH
    expect(await screen.findByText('4 of 12')).toBeInTheDocument();
  });

  it('shows an error banner when the backend is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    renderPage();
    expect(
      await screen.findByText('Unable to reach the NeXo backend'),
    ).toBeInTheDocument();
  });
});
