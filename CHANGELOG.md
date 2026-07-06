# Changelog

All notable changes to NeXo are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-06

First unified release of NeXo as a full trading terminal: the event-driven
engine, a versioned REST API, and a React web frontend. This aligns all
components under a single product version (`1.0.0`).

### Added — REST API (`/api/v1`)

- **API platform**: centralized configuration, structured JSON logging with an
  in-memory audit trail, global exception handling, standardized success/error
  envelopes, request validation, CORS, and OpenAPI documentation.
- **Authentication & RBAC**: JWT-ready authentication abstractions with
  User/Admin role-based authorization. No users, credentials, or tokens are
  issued by the service; protected routes enforce access when a JWT secret is
  configured.
- **Versioned routes** alongside preserved, now-deprecated legacy `/api/*`
  routes (with `Deprecation`/`Link` headers).
- **Dashboard module**: summary (Total Assets in RM with approximate USD,
  today's/monthly PnL, active strategy, system status), equity curve, recent
  trades.
- **Portfolio module**: summary, holdings, allocation, value history, and
  per-asset details.
- **Strategy Center**: list, details, comparison, and enable/disable, with real
  evaluator metrics (score, weight, observations, trade counts).
- **Trade History**: filtering, pagination, per-trade details, and CSV export.
- **Backtest Center**: run the deterministic reference backtest, status, equity
  curve, drawdown, performance metrics, trade list, and CSV report.
- **Risk Center**: overview, current/portfolio exposure, configuration, alerts,
  emergency stop, and save-settings — delegating to the engine's real controls.
- **Settings**: profile, theme, language, currency, exchange-rate management
  (automatic + manual override + fallback), notifications, API keys, system info.
- **Admin Console** (admin RBAC): user management, KYC review, deposit and
  withdrawal approval, audit logs, system health, feature flags, and maintenance
  mode (with enforcement middleware).

### Added — Frontend (React + TypeScript)

- Production terminal with eight modules: Dashboard, Portfolio, Strategy Center,
  Trade History, Backtest Center, Risk Center, Settings, and Admin Console.
- Design system with CSS-variable theming (light/dark/system), responsive
  layout, Recharts visualizations, and RM-primary currency with approximate USD.
- Honest integration: real backend data where available; typed service contracts
  and clearly unavailable/disabled states elsewhere — no fabricated data.

### Principles

- The API and frontend only read and control the **real trading engine**; they
  never duplicate business logic or fabricate trading data.
- Capabilities without a backend (user records, KYC, deposits/withdrawals,
  notification delivery, API-key issuance) return honest unavailable/empty states
  rather than mock data.

### Preserved

- The legacy engine, CLI modes (`compare`, `backtest`, `live`), WebSocket
  streaming, static UI-1 dashboard, and all existing behavior remain unchanged.

### Changed

- Version aligned to `1.0.0` across the package, API, and frontend.
- Prettier configured with `endOfLine: "auto"` for cross-platform formatting.
