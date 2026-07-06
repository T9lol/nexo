# NeXo Terminal — Screenshots

This folder holds screenshots of the NeXo Terminal frontend for the README and
release notes. They are generated from a running dev server (not committed as
part of automated builds) so they always reflect the current UI.

## Pages

| File | Page | What it shows |
|---|---|---|
| `dashboard.png` | Dashboard | Total Assets (RM primary, approximate USD), Today's/Monthly PnL, Active Strategy, System Status, live equity curve, and recent trades. |
| `portfolio.png` | Portfolio | Asset summary, holdings table, allocation pie, and value history. |
| `strategies.png` | Strategy Center | Strategy list, performance metrics, and comparison chart. |
| `trades.png` | Trade History | Searchable, paginated trade table with filters and CSV export. |
| `backtest.png` | Backtest Center | Configuration, equity/drawdown charts, performance metrics, and trade list. |
| `risk.png` | Risk Center | Risk overview, exposure, limits, alerts, and emergency stop. |
| `settings.png` | Settings | Profile, theme, language, currency & exchange rate, notifications, API keys, system info. |
| `admin.png` | Admin Console | System health plus the seven admin panels (User Management, KYC Review, Deposit Approval, Withdrawal Approval, Audit Logs, Feature Flags, Maintenance Mode). |

## How to regenerate

1. Start the backend API:

   ```bash
   python -m uvicorn ui.dashboard:app --port 8002
   ```

2. Start the frontend:

   ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```

3. Open `http://localhost:5173`, navigate to each page above, and capture a
   screenshot (light or dark theme) into this folder using the file names in the
   table.

The terminal polls the live engine, so values will differ between captures; that
is expected — no data is mocked.
