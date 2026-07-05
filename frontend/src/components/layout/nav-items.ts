import {
  ArrowLeftRight,
  BrainCircuit,
  History,
  LayoutDashboard,
  Settings,
  ShieldAlert,
  ShieldQuestion,
  Wallet,
  type LucideIcon,
} from 'lucide-react';
import { ROUTES } from '@/app/routes';

export interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  /** Optional short tag shown next to the label (e.g. future scope). */
  tag?: string;
}

/** Primary navigation, shared by the desktop sidebar and mobile drawer. */
export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', to: ROUTES.dashboard, icon: LayoutDashboard },
  { label: 'Portfolio', to: ROUTES.portfolio, icon: Wallet },
  { label: 'Strategies', to: ROUTES.strategies, icon: BrainCircuit },
  { label: 'Trade History', to: ROUTES.trades, icon: ArrowLeftRight },
  { label: 'Backtest', to: ROUTES.backtest, icon: History },
  { label: 'Risk Center', to: ROUTES.risk, icon: ShieldAlert },
  { label: 'Settings', to: ROUTES.settings, icon: Settings },
  { label: 'Admin', to: ROUTES.admin, icon: ShieldQuestion, tag: 'Soon' },
];
