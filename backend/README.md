# NeXo backend

FastAPI application: the event-driven simulation engine (`core`, `execution`,
`intelligence`, `state`, `strategies`, `backtest`), the versioned `/api/v1` REST
API (`api/`), and the v2 persistence layer (`db/`).

```bash
pip install -e ".[dashboard,test]"
python -m uvicorn ui.dashboard:app --reload --port 8002   # API + docs at /docs
python -m unittest discover -s tests -v                   # test suite
```

Database migrations live in `../database/` (Alembic). Local dev uses a SQLite
fallback (`DATABASE_URL` unset); production uses PostgreSQL via `DATABASE_URL`.

> NeXo is an educational **paper-trading / simulation** platform — no real money,
> no exchange, not financial advice.
