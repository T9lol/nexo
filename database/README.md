# database/

PostgreSQL schema and migrations for NeXo v2.

Populated in **Phase 1** (Postgres foundation): SQLAlchemy models and Alembic
migrations for `users`, `bots`, `subscriptions`, `wallets`, `transactions`,
`trades`, `kyc`, and `risk_configs`. Local development uses a SQLite fallback so
the system stays runnable without a Postgres server; production uses
`DATABASE_URL`.

> NeXo v2 is a **paper-trading / simulation** platform. Wallet balances,
> deposits, withdrawals, and trades are real, persisted, auditable records of
> **simulated** value — not real money and not a real exchange.
