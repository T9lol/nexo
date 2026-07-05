# NeXo handoff for Claude Code

## Current state

- Repository: `kriswu5240-collab/nexo`
- Previous stable release: `v1.0` at commit `837abd5`
- Current release target: `v1.1`
- Current local branch: `ui/dashboard-mvp`
- This branch contains uncommitted UI-1 work. Inspect `git status` and preserve it.
- Do not push, merge, tag, or release without explicit user approval.

## Existing product layer (UI-1)

- FastAPI app: `ui/dashboard.py`
- Frontend: `ui/static/index.html`, `styles.css`, `app.js`
- UI state test: `tests/test_dashboard.py`
- Dashboard uses a deterministic `DashboardStore` mock provider.
- Panels: equity/PnL curve, portfolio, live trades, Strategy A/B state.
- Local environment: `.venv`
- Browser screenshot: `C:/Users/admin/Documents/Codex/2026-07-05/w/outputs/nexo-ui1-dashboard.png`

## UI-2 objective

Connect the Dashboard to real NeXo runtime data while preserving the existing
domain boundaries.

1. Introduce a clean dashboard provider/adapter interface.
2. Keep the current mock provider as a deterministic demo fallback.
3. Add a real provider driven by EventBus, StrategyManager, ExecutionEngine,
   Portfolio, Analytics, and MarketDataFeed.
4. Expose real portfolio, equity history, executed trades, selected strategy,
   scores, and weights through the existing `/api/state` schema.
5. Start read-only: do not add live-order, risk-disable, or real-money controls.
6. Keep UI rendering stable; avoid introducing a frontend framework unless
   there is a concrete need.
7. Add unit tests and run a browser-level test before declaring completion.

## Architecture constraints

- Strategies generate signals only; they never mutate portfolio state.
- Risk checks happen before execution mutates state.
- UI code must not directly modify Portfolio, RiskEngine, or strategy weights.
- Backtest and live runtime paths must remain independently testable.
- Be precise that the selector is heuristic, not trained ML/RL.

## Commands

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m uvicorn ui.dashboard:app --reload
```

Dashboard: `http://127.0.0.1:8000`

## Working style

- Inspect the code and current diff before editing.
- Explain the UI-2 integration plan to the user before large changes.
- Preserve unrelated work.
- Do not publish externally without the user's explicit approval.
