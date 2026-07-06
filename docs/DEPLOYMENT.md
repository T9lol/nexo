# Deployment

NeXo v2 deploys as two services: the **FastAPI backend** (Railway) with a
**PostgreSQL** database, and the **Vite frontend** (Vercel).

> NeXo is an educational **paper-trading / simulation** platform. Wallets,
> deposits, withdrawals, and trades are real, persisted records of *simulated*
> value — not real money and not a live exchange.

## Architecture

```
Frontend (Vite/React) ──HTTPS──▶ Backend (FastAPI) ──▶ PostgreSQL
   Vercel                          Railway                Railway
                                     └─ bot worker (background thread)
```

## Backend → Railway

The repo root contains a `Dockerfile` (build context = repo root; it needs both
`backend/` and `database/`) and `railway.json`.

1. Create a Railway project and add a **PostgreSQL** plugin (provides
   `DATABASE_URL`).
2. Deploy this repo. Railway builds the `Dockerfile`, which on start runs
   `alembic upgrade head` and then `uvicorn ui.dashboard:app`.
3. Set environment variables (see `backend/.env.example`):
   - `DATABASE_URL` — provided by the Railway Postgres plugin.
   - `NEXO_JWT_SECRET` — **required**; a long random secret (auth mints tokens
     with it).
   - `NEXO_CORS_ORIGINS` — your Vercel frontend origin (e.g.
     `https://your-app.vercel.app`). Never a wildcard.
   - `PORT` — provided by Railway automatically.

The backend serves interactive API docs at `/docs`.

## Frontend → Vercel

`frontend/vercel.json` configures the Vite build and SPA routing.

1. Import the repo into Vercel with **Root Directory = `frontend`**.
2. Vercel runs `pnpm install` + `pnpm build` (output `dist`).
3. Set the environment variable:
   - `VITE_API_URL` — the deployed backend URL, e.g.
     `https://your-backend.up.railway.app`.

## Local development

```bash
# Backend (SQLite fallback; no DB server needed)
cd backend
pip install -e ".[dashboard,test]"
NEXO_JWT_SECRET=dev-secret uvicorn ui.dashboard:app --reload --port 8002

# Frontend (proxies /api to the backend)
cd ../frontend
pnpm install
pnpm dev
```

For a Postgres-backed local run, set `DATABASE_URL` and run
`alembic -c ../database/alembic.ini upgrade head` from `backend/` first.

## CI

`.github/workflows/tests.yml` runs the backend test suite (Python 3.10/3.12,
SQLite) + a migration check, and the frontend typecheck/lint/test/build.
