# AGENTS.md — github-issue-pr-agent

## What This Is

An autonomous agent that reads a GitHub issue, generates an implementation plan,
edits code in a sandboxed copy of a target repo under strict safety boundaries,
runs the test suite, and — only after human approval — opens a **draft** PR.
Offline-first (no keys / DB / broker required) and real-when-keyed (GitHub REST,
OpenAI/Anthropic, PostgreSQL, Celery). Built on `shared-core` v1.3.0.

## Commands

```bash
make install      # pip install -e ../shared-core[dev,docparse] + this project ([dev])
make dev          # python -m issue_pr_agent.main (FastAPI on :8000)
make test         # pytest (full suite; ~5 min — subprocess pytest runs)
make lint         # ruff check src/issue_pr_agent tests examples alembic
make format       # ruff format src/issue_pr_agent tests examples alembic
make typecheck    # pyright src/
make demo         # python examples/run_demo.py (before/after walkthrough, exits 0)
make worker       # celery -A issue_pr_agent.worker worker (needs a broker)
make migrate      # alembic revision --autogenerate
make upgrade      # alembic upgrade head
make docker-up    # docker compose up -d (Postgres + Redis)
make clean        # remove caches
```

## Entry Point

`src/issue_pr_agent/main.py` — FastAPI app. Probes the DB on startup (lifespan) and
selects the persistence backend. Endpoints: `POST /issues/process`,
`POST /issues/{id}/approve`, `GET /runs`, `GET /runs/{id}`, `GET /audit`,
`GET /health`.

## Source Modules

```
src/issue_pr_agent/
├── __init__.py       # package docstring
├── config.py         # AppConfig(BaseAppConfig): GITHUB_MODE, allow/block globs,
│                     #   protected branches, AUTO_APPROVE, sandbox path, DB timeout
├── main.py           # FastAPI app + all endpoints + lifespan DB probe
├── agent.py          # IssuePRAgent orchestrator + FixStrategy + approval gate
├── planner.py        # CodePlanner + FixPlan (sim default / LLMClientFactory real)
├── editor.py         # CodeEditor: allowlist + blocklist + sandbox containment
├── git_ops.py        # GitOps: no-main guard, never push protected, never merge
├── github.py         # MockGitHubClient + RealGitHubClient + build_github_client
├── test_runner.py    # LocalTestRunner: subprocess pytest (shell=False, timeout)
├── sandbox.py        # provision_sandbox / cleanup_sandbox (disposable repo copy)
├── store.py          # InMemoryStore + DatabaseStore (runs + audit, same interface)
├── db.py             # check_db (2s probe) + build_store (DB or in-memory)
├── models.py         # AgentRun, AuditEntry (SQLAlchemy, shared_core Base)
├── worker.py         # Celery process_issue_task + run_issue_pipeline (no-broker ok)
├── audit.py          # thin AuditLog shim (canonical trail lives in store.py)
└── errors.py         # re-exports shared_core.errors.application_error_handler
```

## shared_core Usage

`config.BaseAppConfig`, `logging.setup_logging` + `RequestLoggingMiddleware`,
`errors.application_error_handler` + typed errors, `health.check_health`,
`database.{DatabaseManager,Base,UUIDMixin,TimestampMixin}`, `redis.RedisManager`,
`clients.BaseHTTPClient` (GitHub REST), `llm.LLMClientFactory` (planner),
`tasks.create_celery_app` (worker), `testing.MockDatabase` (tests).

## Safety Boundaries (the point of the project)

- **Editor**: every write passes `check_path` — sandbox containment (`Path.resolve`)
  + allowlist + blocklist (`.github/**`, `.env*`, build/config, `**/secrets/**`).
- **Git**: no create/commit/push on `main`/`master`; `merge` is a hard no-op.
- **Approval gate**: pipeline stops at `awaiting_approval`; only
  `approve_and_open_pr` creates a PR, always as a draft.
- **Tests must pass** before a run is approvable.
- **Audit**: every action (incl. refusals) is recorded to the store.

See `docs/security.md` for secrets, tool/file boundaries, and prompt-injection.

## Demo / Sandbox

`demo_repo/` ships a buggy `calculator.py` (`divide` has no zero guard) and
`test_calculator.py` with a failing case. The agent provisions a disposable copy,
applies the fix, and the failing test flips to passing — the before/after the demo
and `test_agent.py` verify.

## Tests

`tests/` — unit (every module), integration (e2e on demo_repo), API (every
endpoint, success + error), worker, safety guards, golden planner output. All run
with NO network / DB / keys. `MockDatabase` (SQLite) exercises the DB store.

## Tech / Containers

FastAPI, Celery, SQLAlchemy + Alembic, httpx. Docker compose: `pgagent_postgres`
(pgvector:pg16, :5432), `pgagent_redis` (redis:7, :6379).

## When to Update This AGENTS.md

- New modules under `src/issue_pr_agent/`, new endpoints, or new safety guards.
- Changes to the allowlist/blocklist or approval flow.
- Schema changes (add an Alembic revision under `alembic/versions/`).
- New `shared_core` modules adopted, or the pinned version changes.
