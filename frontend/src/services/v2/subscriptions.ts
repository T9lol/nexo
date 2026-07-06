/** v2 bots + subscriptions service. */

import { v2Body, v2Request } from './client';
import type { Bot, Subscription } from './types';

export async function listBots(): Promise<Bot[]> {
  const data = await v2Request<{ bots: Bot[]; count: number }>('/api/v2/bots');
  return data.bots;
}

export async function listSubscriptions(): Promise<Subscription[]> {
  const data = await v2Request<{
    subscriptions: Subscription[];
    count: number;
  }>('/api/v2/subscriptions');
  return data.subscriptions;
}

export async function subscribe(
  botId: number,
  capital: number,
): Promise<Subscription> {
  return v2Request<Subscription>('/api/v2/subscriptions', {
    method: 'POST',
    body: v2Body({ bot_id: botId, capital }),
  });
}

function transition(
  id: number,
  action: 'pause' | 'resume' | 'cancel',
): Promise<Subscription> {
  return v2Request<Subscription>(`/api/v2/subscriptions/${id}/${action}`, {
    method: 'POST',
  });
}

export const pauseSubscription = (id: number) => transition(id, 'pause');
export const resumeSubscription = (id: number) => transition(id, 'resume');
export const cancelSubscription = (id: number) => transition(id, 'cancel');
