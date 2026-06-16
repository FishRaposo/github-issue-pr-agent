# Roadmap — github-issue-pr-agent

## Shipped (current build)

- **Safe pipeline end-to-end**: fetch issue → plan → branch → edit → commit → test →
  approval gate → draft PR, fully audited.
- **Offline-first / real-when-keyed**: deterministic mock GitHub + simulated planner
  by default; real GitHub REST (`BaseHTTPClient`) and real LLM (`LLMClientFactory`)
  behind config/keys.
- **Safety model**: allowlist + blocklist + sandbox containment in the editor;
  no-main guard, never-push-protected, never-merge in git ops; subprocess pytest with
  `shell=False` + timeout.
- **Approval gate**: no PR without explicit approval; PRs are always drafts.
- **Persistence**: `agent_runs` + `audit_entries` to PostgreSQL via SQLAlchemy /
  Alembic, with a transparent in-memory fallback selected by a 2s DB probe.
- **Real Celery task** importable with no broker; API falls back to synchronous
  execution when no broker is present.
- **API**: `/issues/process`, `/issues/{id}/approve`, `/runs`, `/runs/{id}`, `/audit`,
  `/health` — everything a dashboard needs.
- **Demo**: before/after walkthrough on `demo_repo` (failing test → passing test).
- **Tests**: unit (every module), integration (e2e on the demo repo), API (every
  endpoint, success + error), worker, safety guards, and golden planner output.

---

## Milestone 1 — Apply patches from the plan

- Let the planner emit structured edits; validate each against the **same**
  `CodeEditor.check_path` gate before it can touch disk.
- Add a dry-run "proposed diff" surfaced in the run and the PR body.
- Golden tests so a model regression cannot silently change applied edits.

## Milestone 2 — Containerized sandbox

- Run edit + test inside an ephemeral, network-isolated container with CPU/memory
  limits and a read-only repo mount except the working copy.
- Removes the "test code runs on host" residual risk.

## Milestone 3 — Multi-file refactors

- Plan and edit across several files with dependency awareness.
- Extend target-file inference beyond a single file per run.

## Milestone 4 — Trigger & throughput

- Webhook-driven invocation on a configurable label (e.g. `agent-ready`).
- Rate limiting + GitHub quota awareness (`X-RateLimit-Remaining`, backoff, token
  rotation).
- Concurrency control so parallel runs don't collide on a branch.

## Milestone 5 — Self-correction loop

- On a failing test run, feed the failure back to the planner and retry within a
  bounded attempt/cost budget, recording each attempt in the audit trail.

## Milestone 6 — Observability & integration

- Emit spans via `shared_core.tracing` for ingestion by an observability backend.
- Integrate with `llm-cost-latency-monitor` for planner cost/latency, and with
  `hermes-agent-framework` / `async-workflow-engine` for orchestration.
