# NeXo — Software Design Specification (SDS)

> Authoritative baseline for the NeXo frontend, established for **Sprint 1**.
> This document records the technical architecture. Product scope and screen
> intent live in [`NEXO_PRODUCT_SPEC.md`](./NEXO_PRODUCT_SPEC.md).

## 1. Purpose & scope

NeXo is a **personal/team quantitative trading terminal** — an internal tool for
operating and observing the NeXo trading engine. It is **not** a customer-facing
fintech platform. There is no onboarding funnel, KYC, deposits/withdrawals, or
multi-tenant billing.

Sprint 1 delivers the **production frontend foundation only**: application shell,
routing, theme system, responsive layout, a reusable component library, and
placeholder pages. No business logic, no data, no live connections.

## 2. System context

```
┌──────────────────────────┐        ┌─────────────────────────────┐
│  frontend/ (this SDS)    │        │  FastAPI backend (existing) │
│  React + TS + Vite SPA   │  ───▶  │  ui/ legacy dashboard,      │
│  served statically       │  HTTP/ │  /api/*, /ws (later sprints)│
│                          │   WS   │  NeXo runtime engine        │
└──────────────────────────┘        └─────────────────────────────┘
```

The existing FastAPI backend and the legacy vanilla `ui/` dashboard are
**preserved unchanged** in Sprint 1. The new SPA lives in `/frontend` and is
developed independently. Backend/WS integration is deferred to later sprints.

## 3. Technology stack

| Concern            | Choice                                              |
| ------------------ | --------------------------------------------------- |
| Framework          | React 18 + TypeScript (**strict**)                  |
| Build tool         | Vite (SPA)                                           |
| Package manager    | pnpm                                                 |
| Routing            | React Router (client-side)                           |
| Styling            | Tailwind CSS with **CSS-variable design tokens**    |
| Accessible a11y    | Radix UI primitives where behavior is required      |
| Variants           | class-variance-authority (CVA)                      |
| Icons              | Lucide                                               |
| Testing            | Vitest + React Testing Library + jest-dom           |
| Lint / format      | ESLint (flat config) + Prettier                     |

### Quality gates (must all pass)

1. `pnpm lint` — ESLint, zero errors.
2. `pnpm typecheck` — `tsc --noEmit`, TypeScript strict.
3. `pnpm test` — Vitest suite green.
4. `pnpm build` — production build succeeds.

## 4. Directory architecture (`/frontend`)

```
src/
  main.tsx            App entry (mounts providers + router)
  App.tsx             ThemeProvider + RouterProvider composition
  index.css           Tailwind layers + design tokens (:root / .dark)
  lib/                Framework-agnostic helpers (cn, constants)
  theme/              Theme provider (light | dark | system, persisted)
  app/                Route table, path constants, navigation config
  components/
    ui/               Reusable component library (the design system)
    layout/           App shell: sidebar, top nav, mobile drawer
  pages/              One placeholder module per route
  test/               Test setup (jest-dom, matchMedia shim)
```

**Import boundaries.** `pages` and `layout` depend on `ui`, `theme`, `lib`,
`app`. `ui` depends only on `lib` and Radix. No page imports another page. A
path alias `@/` maps to `src/` to avoid deep relative paths.

## 5. Theme system

- Three user choices: **light**, **dark**, **system**; the resolved theme is
  applied by toggling a `.dark` class on `<html>`.
- The choice is **persisted** in `localStorage` under `nexo-theme` and restored
  on load; `system` follows `prefers-color-scheme` live via a media-query
  listener.
- All colors are **semantic CSS variables** (HSL) defined once in `index.css`
  and consumed through Tailwind's `theme.extend.colors`. Components never
  hard-code hex values.

### Color semantics

| Token          | Role                                             |
| -------------- | ------------------------------------------------ |
| `background`   | App canvas (neutral/slate)                       |
| `surface`      | Cards, panels, elevated regions                  |
| `foreground`   | Primary text                                     |
| `muted(-fg)`   | Secondary text / subtle surfaces                 |
| `border`       | Hairlines, dividers                              |
| `primary`      | Brand / primary actions (emerald family)         |
| `positive`     | Gains / long / success (emerald)                 |
| `negative`     | Losses / short / danger (red)                    |
| `warning`      | Caution / risk states (amber)                    |
| `ring`         | Focus ring                                       |

## 6. Component library

Fourteen reusable primitives, each typed, themeable, and covering the required
interaction states — **loading, empty, error, disabled, focus, hover, active**:

`Button`, `Card`, `Input`, `Select`, `Switch`, `Tabs`, `Badge`, `Table`,
`Dialog`, `Dropdown`, `Tooltip`, `Skeleton`, `EmptyState`, `PageHeader`.

Behavioral components (Select, Switch, Tabs, Dialog, Dropdown, Tooltip) wrap
**Radix UI** primitives for accessibility (keyboard nav, focus management, ARIA)
and are styled with Tailwind + tokens. Presentational components (Button, Card,
Input, Badge, Table, Skeleton, EmptyState, PageHeader) are hand-built. Variants
are expressed with CVA so states are declarative and testable.

## 7. Layout & responsiveness

- **App shell** = collapsible desktop sidebar + top navigation + routed content.
- **Desktop (≥1024px):** persistent sidebar; user can collapse it to an
  icon rail (state persisted).
- **Tablet (768–1023px):** condensed layout, sidebar collapsible.
- **Mobile (<768px):** sidebar hidden; an accessible **navigation drawer**
  (Radix Dialog) opens from the top nav, with focus trap and Escape-to-close.
- No horizontal overflow at any breakpoint; content max-width constrained for
  readability on ultrawide displays.

## 8. Routing

Client-side routes: `/dashboard`, `/portfolio`, `/strategies`, `/trades`,
`/backtest`, `/risk`, `/settings`, `/admin`. `/` redirects to `/dashboard`, and
an unmatched path renders a **Not Found** page. Route paths and navigation
metadata are defined once in `app/` and consumed by both the router and the
sidebar/drawer so they cannot drift.

## 9. Out of scope for Sprint 1

API/WebSocket calls, mock/live trading data, authentication/KYC,
deposits/withdrawals, order entry or trading controls, and any business logic.
The **Admin** route is an explicit, clearly labeled future-scope placeholder.

## 10. Non-functional requirements

- TypeScript strict; no `any` in library code.
- Accessible: semantic HTML, keyboard operability, visible focus, sufficient
  contrast in both themes.
- Deterministic build via committed `pnpm-lock.yaml`.
- Clean, documented, maintainable code with clear module boundaries.
