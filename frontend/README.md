# Issue → PR Console (frontend)

A production-looking operator console for the **GitHub Issue-to-PR agent**. It
lets you submit issues to the agent, watch the
`issue → plan → branch → edit → tests → approval → draft PR` pipeline, gate
approvals, and audit every action — all under a visually-emphasized safety
model (allowlisted paths, no-main guard, approval-before-PR).

Built with Next.js 14 (App Router) + React 18 + TypeScript + Tailwind +
lucide-react + recharts + react-markdown. Tested with Vitest +
@testing-library/react and Playwright.

## Pages

| Route        | Purpose                                                                    | Backend endpoint(s)                       |
| ------------ | -------------------------------------------------------------------------- | ----------------------------------------- |
| `/`          | Overview: live stats, runs-by-status chart, and the safety model           | `GET /runs`                               |
| `/process`   | Submit an issue and watch the pipeline + generated plan                     | `POST /issues/process`                    |
| `/runs`      | List of all runs with status filters                                       | `GET /runs`                               |
| `/runs/[id]` | Run detail: pipeline timeline, plan, before/after diff, tests, approval gate, per-run audit | `GET /runs/{id}`, `GET /audit?run_id=`, `POST /issues/{id}/approve` |
| `/audit`     | Append-only audit log with action-type filters and timestamps              | `GET /audit`                              |

## Quick start

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

The app runs **with no backend** thanks to demo mode (see below). To wire it to
the live FastAPI service, start the backend (`make run` / `uvicorn` in the
project root, listening on `:8000`) and the dashboard will use it automatically.

## Demo mode (no backend required)

The dashboard is **live-first**: every view first tries the real API at
`NEXT_PUBLIC_API_URL`. Behavior on failure is deliberate:

- **Backend unreachable** (offline / connection refused / timeout) → the view
  falls back to bundled mock data and shows a visible **"Demo mode"** badge. The
  bundled dataset reproduces the canonical demo (the `calculator.py`
  division-by-zero fix for issue #101) plus runs in every state: completed,
  awaiting approval, tests-failed, and safety-refused.
- **Real HTTP 4xx/5xx** from the backend → surfaced as an explicit **error
  state** (never masked by demo data), including the status code.
- **Writes in demo mode** (processing an issue, approving a run) are simulated
  locally and clearly labeled **"demo — not persisted"**.

This means you can fully explore the entire console — pipeline timeline, diff,
approval gate, audit trail — without running anything else.

## Environment

| Variable              | Default                 | Description                          |
| --------------------- | ----------------------- | ------------------------------------ |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the FastAPI backend.     |

Copy `.env.example` to `.env.local` to override.

## Scripts

```bash
npm run dev        # start the dev server
npm run build      # production build
npm start          # serve the production build
npm test           # run Vitest component/unit tests (no backend needed)
npm run test:e2e   # run Playwright smoke tests over the demo UI
npx tsc --noEmit   # type-check
```

## Tests

- **Vitest + @testing-library/react** — component and API-client tests under
  `tests/`. They render with bundled mock data and **pass with no backend**,
  covering the status badges, pipeline timeline, diff, audit timeline, safety
  panel, test results, the approval gate (demo write path), and the API client's
  live-first / demo-fallback / real-error behavior.
- **Playwright** — `e2e/smoke.spec.ts` drives the demo-mode UI: overview, runs
  list → detail, audit log, and a demo pipeline run on the process page.

## Docker

A `web` service is defined in the repository-root `docker-compose.yml`:

```bash
docker compose up web    # builds ./frontend and serves on :3000
```
