/** Typed contracts for the v2 SaaS API (mirrors the backend responses). */

export interface Envelope<T> {
  success: boolean;
  data: T;
  meta?: unknown;
}

export interface User {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Wallet {
  balance: number;
  frozen_balance: number;
  available: number;
  currency: string;
}

export interface Transaction {
  id: number;
  user_id: number;
  type: string;
  amount: number;
  status: string;
  reference: string | null;
  created_at: string | null;
}

export interface Bot {
  id: number;
  key: string;
  name: string;
  description: string | null;
  strategy_ref: string;
  is_active: boolean;
}

export interface Subscription {
  id: number;
  bot_id: number;
  capital: number;
  status: string;
  created_at: string | null;
  bot?: { key: string; name: string };
}

export interface Trade {
  id: number;
  subscription_id: number;
  bot_id: number | null;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  value: number;
  pnl: number;
  status: string;
  executed_at: string | null;
}

export interface PortfolioPosition {
  subscription_id: number;
  bot: string | null;
  status: string;
  capital: number;
  cash: number;
  position: number;
  value: number;
  pnl: number;
  pnl_percent: number;
}

export interface Portfolio {
  symbol: string;
  price: number;
  total_capital: number;
  total_value: number;
  total_pnl: number;
  pnl_percent: number;
  open_positions: number;
  positions: PortfolioPosition[];
}

export interface RiskConfig {
  position_limit_enabled: boolean;
  max_position: number;
  daily_loss_limit: number | null;
}

export interface Paginated {
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}
