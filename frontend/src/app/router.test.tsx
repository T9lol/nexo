import { render, screen } from '@testing-library/react';
import { MemoryRouter, useRoutes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { TooltipProvider } from '@/components/ui';
import { ThemeProvider } from '@/theme/theme-provider';
import { routes } from './router';

function RoutedApp() {
  return useRoutes(routes);
}

function renderAt(path: string) {
  return render(
    <ThemeProvider>
      <TooltipProvider>
        <MemoryRouter initialEntries={[path]}>
          <RoutedApp />
        </MemoryRouter>
      </TooltipProvider>
    </ThemeProvider>,
  );
}

describe('router', () => {
  it('redirects / to the dashboard', async () => {
    renderAt('/');
    expect(
      await screen.findByRole('heading', { level: 1, name: 'Dashboard' }),
    ).toBeInTheDocument();
  });

  it('renders the settings route', async () => {
    renderAt('/settings');
    expect(
      await screen.findByRole('heading', { level: 1, name: 'Settings' }),
    ).toBeInTheDocument();
  });

  it('renders the admin console', async () => {
    renderAt('/admin');
    expect(
      await screen.findByRole('heading', { level: 1, name: 'Admin Console' }),
    ).toBeInTheDocument();
  });

  it('shows a not found page for unknown routes', async () => {
    renderAt('/does-not-exist');
    expect(await screen.findByText('Page not found')).toBeInTheDocument();
  });
});
