/** Types mirroring the backend `/api/state` schema (read-only). */

export interface MarketState {
  symbol: string;
  price: number;
}

export interface PortfolioState {
  cash: number;
  asset: number;
  /** Total equity in USD (cash + asset × price). */
  equity: number;
  /** All-time PnL in USD. */
  pnl: number;
}

export interface StrategyStat {
  score: number;
  weight: number;
  updates: number;
  adaptive: number;
}

export type TradeAction = 'BUY' | 'SELL';

export interface Trade {
  id: string;
  time: string;
  strategy: string;
  action: TradeAction | string;
  symbol: string;
  price: number;
  amount: number;
}

export interface EquityPoint {
  time: string;
  value: number;
}

export interface ControlState {
  trading_enabled: boolean;
  strategy_policy: string;
  effective_strategy: string;
  manual_override: boolean;
  position_limit_enabled: boolean;
  mode: string;
  environment: string;
  allowed: {
    strategy_policy: string[];
    mode: string[];
  };
}

export interface DashboardState {
  status: string;
  mode: string;
  updated_at: string;
  market: MarketState;
  portfolio: PortfolioState;
  selected_strategy: string;
  strategies: Record<string, StrategyStat>;
  trades: Trade[];
  equity_curve: EquityPoint[];
  control: ControlState;
}
