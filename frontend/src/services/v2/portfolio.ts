/** v2 portfolio + trades + risk services. */

import { v2Body, v2Request } from './client';
import type { Paginated, Portfolio, RiskConfig, Trade } from './types';

export async function getPortfolio(): Promise<Portfolio> {
  return v2Request<Portfolio>('/api/v2/portfolio');
}

export async function listTrades(
  params: {
    page?: number;
    pageSize?: number;
    side?: string;
    subscriptionId?: number;
  } = {},
): Promise<Paginated & { trades: Trade[] }> {
  const q = new URLSearchParams();
  q.set('page', String(params.page ?? 1));
  q.set('page_size', String(params.pageSize ?? 20));
  if (params.side) q.set('side', params.side);
  if (params.subscriptionId)
    q.set('subscription_id', String(params.subscriptionId));
  return v2Request(`/api/v2/trades?${q.toString()}`);
}

export async function getRiskConfig(): Promise<RiskConfig> {
  return v2Request<RiskConfig>('/api/v2/risk');
}

export async function updateRiskConfig(
  config: RiskConfig,
): Promise<RiskConfig> {
  return v2Request<RiskConfig>('/api/v2/risk', {
    method: 'PUT',
    body: v2Body(config),
  });
}
