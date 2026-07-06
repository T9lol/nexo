/** v2 wallet service (paper funds). */

import { v2Body, v2Request } from './client';
import type { Paginated, Transaction, Wallet } from './types';

interface WalletTxResult {
  wallet: Wallet;
  transaction: Transaction;
}

export async function getWallet(): Promise<Wallet> {
  return v2Request<Wallet>('/api/v2/wallet');
}

export async function listTransactions(
  page = 1,
  pageSize = 20,
): Promise<Paginated & { transactions: Transaction[] }> {
  return v2Request(
    `/api/v2/wallet/transactions?page=${page}&page_size=${pageSize}`,
  );
}

export async function deposit(
  amount: number,
  reference?: string,
): Promise<WalletTxResult> {
  return v2Request<WalletTxResult>('/api/v2/wallet/deposit', {
    method: 'POST',
    body: v2Body({ amount, reference }),
  });
}

export async function requestWithdrawal(
  amount: number,
  reference?: string,
): Promise<WalletTxResult> {
  return v2Request<WalletTxResult>('/api/v2/wallet/withdraw', {
    method: 'POST',
    body: v2Body({ amount, reference }),
  });
}
