/** Canonical route paths. Consumed by the router and the navigation config so
 * the two can never drift. */
export const ROUTES = {
  dashboard: '/dashboard',
  portfolio: '/portfolio',
  strategies: '/strategies',
  trades: '/trades',
  backtest: '/backtest',
  risk: '/risk',
  settings: '/settings',
  admin: '/admin',
} as const;

export type RoutePath = (typeof ROUTES)[keyof typeof ROUTES];
