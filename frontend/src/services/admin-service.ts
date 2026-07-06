import { getDashboardState, getHealth } from './dashboard-service';

/**
 * Admin service.
 *
 * The only admin capability the backend genuinely supports is a health/status
 * read (via /api/health + /api/state). Everything else in an admin console —
 * user management, KYC review, deposit approval, withdrawal approval, audit
 * logs, feature flags, and maintenance mode — requires backends and server-side
 * authorization that do not exist in this local terminal. Those are exposed as
 * typed contracts that reject, so the UI can render clearly-disabled panels
 * without fabricating users, records, transactions, logs, flags, or behaviour.
 */

export const USER_MANAGEMENT_AVAILABLE = false;
export const KYC_REVIEW_AVAILABLE = false;
export const DEPOSIT_APPROVAL_AVAILABLE = false;
export const WITHDRAWAL_APPROVAL_AVAILABLE = false;
export const AUDIT_LOG_AVAILABLE = false;
export const FEATURE_FLAGS_AVAILABLE = false;
export const MAINTENANCE_MODE_AVAILABLE = false;

function unavailable(feature: string): Promise<never> {
  return Promise.reject(
    new Error(
      `${feature} requires a backend and server-side authorization that are not available in this build.`,
    ),
  );
}

export function listUsers(): Promise<never> {
  return unavailable('User management');
}

export function listKycRecords(): Promise<never> {
  return unavailable('KYC review');
}

export function listDepositRequests(): Promise<never> {
  return unavailable('Deposit approval');
}

export function listWithdrawalRequests(): Promise<never> {
  return unavailable('Withdrawal approval');
}

export function listAuditLogs(): Promise<never> {
  return unavailable('Audit logs');
}

export function listFeatureFlags(): Promise<never> {
  return unavailable('Feature flags');
}

export function setMaintenanceMode(_enabled: boolean): Promise<never> {
  return unavailable('Maintenance mode');
}

// -- Real: system health ----------------------------------------------------

export interface SystemHealth {
  healthy: boolean;
  status: string;
  mode: string;
  environment: string;
}

export async function getSystemHealth(
  signal?: AbortSignal,
): Promise<SystemHealth> {
  const [health, state] = await Promise.all([
    getHealth(signal),
    getDashboardState(signal),
  ]);
  return {
    healthy: health.status === 'ok',
    status: health.status,
    mode: state.control?.mode ?? state.mode,
    environment: state.control?.environment ?? 'local-simulation',
  };
}
