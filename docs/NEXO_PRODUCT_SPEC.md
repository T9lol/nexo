# NeXo — Product Specification

> Product scope and screen intent for the NeXo terminal. Technical architecture
> lives in [`NEXO_SDS.md`](./NEXO_SDS.md). This document is the authoritative
> baseline established for **Sprint 1**.

## 1. Product definition

NeXo is a **professional quantitative trading terminal** for a personal or small
team operating the NeXo trading engine. The audience is a trader/operator, not a
retail consumer. The experience should feel like an **institutional desk tool**:
data-dense but **calm** and legible — explicitly *not* crypto-casino styling
(no neon gradients, no confetti, no hype).

## 2. Design principles

1. **Clarity over decoration.** Every pixel earns its place; whitespace and
   hierarchy do the work.
2. **Calm density.** Show a lot without shouting: restrained color, tabular
   numerals, consistent spacing scale.
3. **Trust through consistency.** One component library, one token set, uniform
   states everywhere.
4. **Meaningful color.** Neutral/slate surfaces; **emerald = positive**,
   **red = negative**, **amber = warning/caution**. Color encodes financial
   meaning, never mood.
5. **Accessible by default.** Keyboard-first, visible focus, contrast-safe in
   light and dark.
6. **Responsive everywhere.** Usable on desktop, tablet, and mobile.

## 3. Theme

Light mode, dark mode, **system preference**, and a **persisted** explicit user
choice. Dark mode is the expected default for a trading desk; light mode is a
first-class equal. Neither theme sacrifices contrast or the positive/negative
color semantics.

## 4. Navigation model

A left sidebar (collapsible on desktop, drawer on mobile) plus a top bar. Primary
destinations:

| Route         | Screen        | Purpose (future sprints)                                  |
| ------------- | ------------- | --------------------------------------------------------- |
| `/dashboard`  | Dashboard     | At-a-glance equity, exposure, live status, key signals.   |
| `/portfolio`  | Portfolio     | Positions, allocation, cash, P&L breakdown.               |
| `/strategies` | Strategies    | Strategy roster, scores/weights, enable/select policy.    |
| `/trades`     | Trade History | Executed fills, filters, export.                          |
| `/backtest`   | Backtest      | Configure and review historical replays.                  |
| `/risk`       | Risk Center   | Limits, exposure, risk-policy controls and warnings.      |
| `/settings`   | Settings      | Preferences, theme, connections, account.                 |
| `/admin`      | Admin         | **Future scope** — operator/admin tooling (placeholder).  |

`/` redirects to **Dashboard**. Unknown paths show a **Not Found** screen with a
route back to the Dashboard.

## 5. Screen intent (Sprint 1 = placeholders)

Each screen ships in Sprint 1 as a **placeholder**: a `PageHeader` (title +
description), and a body communicating that the screen is scaffolded for a future
sprint (using `EmptyState`/`Skeleton`/`Card` where illustrative). No data, no
controls with side effects.

- **Dashboard** — landing surface; future home for equity curve, KPIs, live feed.
- **Portfolio** — future positions/allocation tables and charts.
- **Strategies** — future strategy cards and policy selection.
- **Trade History** — future filterable trade table.
- **Backtest** — future backtest configuration + results review.
- **Risk Center** — future limits and risk-policy switches with warning states.
- **Settings** — theme control is functional in Sprint 1; other settings are
  placeholders.
- **Admin** — **clearly labeled future-scope**; visibly gated as not-yet-available.

## 6. Component states (required across the library)

Every interactive component demonstrates and supports: **default, hover, active,
focus (visible ring), disabled, loading, error, empty**. These states are part of
the deliverable, not an afterthought — they are the vocabulary the later data
screens will rely on.

## 7. Explicitly out of scope (Sprint 1)

- Real or mock trading data; API/WebSocket connectivity.
- Authentication, KYC, deposits, withdrawals, funding.
- Order entry, trading controls, or any state-changing business logic.
- Admin functionality beyond a labeled placeholder.

## 8. Success criteria for Sprint 1

- All eight routes plus redirect and Not Found render within the responsive
  shell, at desktop/tablet/mobile with no horizontal overflow.
- Theme switching (light/dark/system) works and persists.
- The 14-component library is usable, themed, accessible, and covers the
  required states.
- Lint, typecheck, tests, and production build all pass.
