import {
  createBrowserRouter,
  Navigate,
  type RouteObject,
} from 'react-router-dom';
import { AppShell } from '@/components/layout/app-shell';
import AdminPage from '@/pages/admin-page';
import BacktestPage from '@/pages/backtest-page';
import DashboardPage from '@/pages/dashboard-page';
import NotFoundPage from '@/pages/not-found-page';
import PortfolioPage from '@/pages/portfolio-page';
import RiskPage from '@/pages/risk-page';
import SettingsPage from '@/pages/settings-page';
import StrategiesPage from '@/pages/strategies-page';
import TradesPage from '@/pages/trades-page';
import { ROUTES } from './routes';

/** Route config. A pathless layout route wraps every page in the app shell.
 * Exported so tests can mount it with a memory router. */
export const routes: RouteObject[] = [
  {
    element: <AppShell />,
    children: [
      { path: '/', element: <Navigate to={ROUTES.dashboard} replace /> },
      { path: ROUTES.dashboard, element: <DashboardPage /> },
      { path: ROUTES.portfolio, element: <PortfolioPage /> },
      { path: ROUTES.strategies, element: <StrategiesPage /> },
      { path: ROUTES.trades, element: <TradesPage /> },
      { path: ROUTES.backtest, element: <BacktestPage /> },
      { path: ROUTES.risk, element: <RiskPage /> },
      { path: ROUTES.settings, element: <SettingsPage /> },
      { path: ROUTES.admin, element: <AdminPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
