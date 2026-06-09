# AGENTS.md — github-issue-pr-agent

## What This Is

An autonomous agent that reads GitHub issues with a specific label, generates an LLM-powered implementation plan, edits code in a sandboxed target repository, runs the test suite, and opens a draft PR — all within strict safety boundaries (allowlisted repos, allowlisted paths, no main push, no merge, no secret access). Wave 3 project that will integrate with hermes-agent-framework, async-workflow-engine, and llm-cost-latency-monitor.

## Commands

```bash
make install          # pip install -e ../shared-core && pip install -r requirements.txt
make dev              # python src/issue_pr_agent/main.py (FastAPI on :8000)
make test             # pytest (tests/test_core.py)
make lint             # ruff check .
make format           # ruff format .
make typecheck        # pyright src/
make docker-up        # docker compose up -d (Postgres pgvector:pg16 + Redis 7)
make docker-down      # docker compose down
make demo             # python examples/run_demo.py (runs mock issue-to-PR pipeline)
make clean            # remove __pycache__, .pytest_cache, etc.
```

## Entry Point

`src/issue_pr_agent/main.py` — FastAPI app with `/health` endpoint. Imports `AppConfig` from `issue_pr_agent.config`, uses `shared_core.logging.setup_logging`, `shared_core.database.DatabaseManager`, `shared_core.redis.RedisManager`, and `shared_core.errors.BaseApplicationError`.

## Source Modules

```
src/issue_pr_agent/
├── __init__.py        # Package docstring: "GitHub Issue-to-PR Automation Agent."
├── main.py            # FastAPI app, /health endpoint, DB + Redis managers, error handler registration
├── config.py          # AppConfig(BaseAppConfig) — APP_NAME = "github-issue-pr-agent"
├── errors.py          # application_error_handler() — converts BaseApplicationError to JSON
├── github.py          # MockGitHubClient — get_issue(), create_pull_request() (hardcoded mock data)
├── planner.py         # CodePlanner — plan_changes(issue) returns step-by-step fix plan string
├── editor.py          # CodeEditor — apply_fix(filepath) does string replacement on source files
├── test_runner.py     # LocalTestRunner — run_tests() stub, always returns True
└── worker.py          # Celery app config + sample_background_task(x, y) template task
```

## Planned Modules (Not Yet Implemented)

When building out the full agent, expect these subpackages per the build plan:

- `github/` — real GitHub API client (issues, branches, PRs), replaces MockGitHubClient
- `planner/` — LLM-powered plan generation using Hermes agent framework
- `editor/` — sandboxed file editing with allowlist enforcement
- `test_runner/` — subprocess-based pytest execution with output parsing
- `approvals/` — human-in-the-loop approval gate API
- `audit/` — PostgreSQL-backed audit trail for all agent actions

## Docker Services

- **postgres**: pgvector/pgvector:pg16 on `:5432` (container: `template_postgres`)
- **redis**: redis:7-alpine on `:6379` (container: `template_redis`)

Note: container names still use the template prefix `template_*` — rename to `issue_pr_agent_*` when customizing.

## Layout

```
github-issue-pr-agent/
├── src/issue_pr_agent/       # Main source package (9 modules)
├── tests/test_core.py        # Health endpoint test
├── examples/run_demo.py      # Mock pipeline demo
├── docs/                     # architecture.md, design-decisions.md, failure-modes.md, roadmap.md, security.md
├── .github/workflows/ci.yml  # ruff check, ruff format --check, pytest
├── docker-compose.yml        # Postgres + Redis
├── Makefile                  # Standard targets
├── .env.example              # Includes GITHUB_TOKEN
├── pyproject.toml             # Project metadata
├── requirements.txt          # Runtime dependencies
├── ruff.toml                 # Lint config
├── pyrightconfig.json        # Type checking config
└── pytest.ini                # Test config
```

## Current State

**Skeleton stage.** The project has the standard template structure with domain-specific stubs:

- `MockGitHubClient` returns hardcoded issue data and fake PR URLs — not connected to real GitHub API
- `CodePlanner` generates a static plan string — no LLM integration yet
- `CodeEditor` does a literal string replacement — no allowlist checking, no AST-aware editing
- `LocalTestRunner` always returns `True` — no subprocess execution
- `worker.py` has a template `sample_background_task` — not wired to the issue processing pipeline
- Only one API endpoint exists (`/health`)
- No audit logging, no approval gate, no real configuration for target repos

The demo (`examples/run_demo.py`) does work end-to-end with mock data.

## Key Dependencies

Beyond shared-core (config, database, redis, logging, errors):

| Package | Purpose |
|---------|---------|
| `httpx` | HTTP client for GitHub REST API v3 (will replace mock client) |
| `celery` | Background task queue for async issue processing |
| `pyyaml` | Configuration parsing for allowlists and workflow definitions |
| `sqlalchemy` | ORM for audit log persistence |

**Future additions expected:**
- `PyGithub` or raw `httpx` for full GitHub API coverage
- Hermes agent framework integration (from `../hermes-agent-framework`)
- LLM provider SDK (OpenAI/Anthropic) for plan generation

## When to Update This AGENTS.md

Update when:
- `MockGitHubClient` is replaced with a real GitHub API client
- New modules are added under `src/issue_pr_agent/` (especially the planned subpackages)
- Allowlist enforcement is implemented in `CodeEditor`
- New API endpoints are added beyond `/health`
- Worker tasks are wired to the actual issue processing pipeline
- Approval gate or audit logging is implemented
- Docker Compose services change (e.g., adding a sandbox container for code execution)
- Integration with hermes-agent-framework or async-workflow-engine is established
