# NeXo Frontend

Production frontend foundation for the **NeXo quantitative trading terminal**
(Sprint 1). React + TypeScript + Vite SPA. See the specs in
[`../docs/NEXO_SDS.md`](../docs/NEXO_SDS.md) and
[`../docs/NEXO_PRODUCT_SPEC.md`](../docs/NEXO_PRODUCT_SPEC.md).

> Sprint 1 is **foundation only**: layout, routing, theming, a reusable
> component library, and placeholder pages. No API/WebSocket connectivity, no
> mock data, no authentication or trading logic. The existing FastAPI backend
> and legacy `ui/` dashboard are untouched.

## Stack

React 18 · TypeScript (strict) · Vite · React Router · Tailwind CSS (CSS-variable
tokens) · Radix UI · Lucide · class-variance-authority · Vitest + React Testing
Library · ESLint + Prettier.

## Getting started

```bash
pnpm install
pnpm dev          # start the dev server
```

## Scripts

| Script            | Purpose                                  |
| ----------------- | ---------------------------------------- |
| `pnpm dev`        | Vite dev server                          |
| `pnpm build`      | Type-check then production build         |
| `pnpm preview`    | Preview the production build             |
| `pnpm lint`       | ESLint                                   |
| `pnpm typecheck`  | `tsc --noEmit` (strict)                  |
| `pnpm test`       | Vitest run                               |
| `pnpm format`     | Prettier write                           |

## Structure

```
src/
  app/          route table + path constants
  components/
    ui/         reusable component library (14 primitives)
    layout/     app shell: sidebar, top nav, mobile drawer
  pages/        one placeholder module per route
  theme/        light | dark | system theme provider (persisted)
  lib/          helpers (cn)
  test/         test setup
```

## Design tokens & theming

Colors are semantic CSS variables in `src/index.css` (`:root` = light,
`.dark` = dark) mapped into Tailwind. Theme choice (light/dark/system) is
persisted to `localStorage` and applied before paint to avoid a flash.
