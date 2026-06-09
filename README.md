# GitHub Issue-to-PR Agent

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![GitHub API](https://img.shields.io/badge/GitHub_API-v3-181717?logo=github&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3+-37814A?logo=celery&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

**An autonomous agent that reads GitHub issues, generates implementation plans, edits code in a sandboxed repository, runs tests, and opens draft pull requests — with strict safety boundaries at every step.**

## Why This Exists

Developer workflows are drowning in low-complexity, high-volume issues — typo fixes, missing input validation, simple refactors. These issues are well-scoped enough for automated resolution, but existing tools either lack safety guarantees or require deep integration into proprietary CI systems.

This project demonstrates that an AI-powered agent can safely bridge the gap between "issue filed" and "draft PR ready for review" without ever touching production branches, accessing secrets, or merging code autonomously. The key constraint is that every action is auditable, every target is allowlisted, and humans remain the final approvers.

## What It Demonstrates

- **GitHub API Integration** — reading issues by label, creating branches, opening draft PRs via the REST API
- **Agent Pipeline Orchestration** — chaining issue parsing → plan generation → code editing → test execution → PR creation into a single automated workflow
- **Safety-First Code Editing** — allowlisted repositories and file paths prevent the agent from modifying anything outside its sandbox
- **Automated Test Execution** — running the target repo's test suite after edits and gating PR creation on passing results
- **Human-in-the-Loop Approval** — draft PRs only, no merges, no pushes to `main`, explicit review required
- **Audit Trail Design** — every agent action logged with timestamps, inputs, outputs, and risk assessments
- **Celery Background Processing** — issue processing happens asynchronously via Redis-backed task queue
- **Structured Error Handling** — shared-core `BaseApplicationError` hierarchy for consistent API error responses

## Architecture

```mermaid
graph TD
    GH["GitHub Issues API"] -->|fetch labeled issues| IR["Issue Reader<br/>(github.py)"]
    IR -->|issue payload| PL["Code Planner<br/>(planner.py)"]
    PL -->|modification plan| ED["Code Editor<br/>(editor.py)"]
    ED -->|edited files| TR["Test Runner<br/>(test_runner.py)"]
    TR -->|pass/fail| AP["Approval Gate"]
    AP -->|approved| PR["PR Creator<br/>(github.py)"]
    PR -->|draft PR| GH

    API["FastAPI Gateway<br/>(main.py)"] -->|enqueue| RQ["Redis Queue"]
    RQ -->|dispatch| CW["Celery Worker<br/>(worker.py)"]
    CW -->|orchestrate| IR

    API -->|health, status| DB[(PostgreSQL)]
    CW -->|audit log| DB

    style AP fill:#ff9800,color:#000
    style GH fill:#24292e,color:#fff
```

The pipeline follows a strict linear flow: **read → plan → edit → test → approve → PR**. Each stage produces an output that feeds the next, and any failure aborts the pipeline with an audit record explaining what went wrong and why.

## Tech Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| API Framework | FastAPI + Uvicorn | Async-ready, Pydantic validation, auto-generated OpenAPI docs |
| Task Queue | Redis + Celery | Decouples long-running issue processing from the API request cycle |
| Database | PostgreSQL (pgvector:pg16) | Stores audit logs, issue tracking state, and plan history |
| GitHub Client | httpx | Async HTTP client for GitHub REST API v3 calls |
| Configuration | pydantic-settings | Type-safe config from `.env` files with validation |
| Logging | loguru (via shared-core) | Structured logging with service name context |
| Shared Library | [shared-core](../shared-core/) | Config, database, Redis, logging, and error utilities |
| Linting | ruff + pyright | Fast linting, import sorting, and static type checking |
| Testing | pytest | Unit and integration testing with FastAPI TestClient |

## Local Setup

```bash
# Enter the project directory
cd github-issue-pr-agent

# Copy environment template and configure
cp .env.example .env
# Edit .env to set GITHUB_TOKEN and LLM API keys

# Start infrastructure (PostgreSQL + Redis)
make docker-up

# Install dependencies (installs shared-core first)
make install

# Run the API server
make dev
# → FastAPI running at http://localhost:8000

# Verify health
curl http://localhost:8000/health
```

## Demo

The demo script in `examples/run_demo.py` simulates the full agent pipeline without requiring a live GitHub connection:

```bash
make demo
```

**What it does:**
1. Creates a temporary `calculator.py` file with a buggy `sum_numbers` function
2. `MockGitHubClient.get_issue(101)` returns a sample bug report about empty list handling
3. `CodePlanner.plan_changes()` generates a step-by-step fix plan
4. `CodeEditor.apply_fix()` patches the file with an empty-list guard
5. `LocalTestRunner.run_tests()` validates the fix passes
6. `MockGitHubClient.create_pull_request()` simulates opening a draft PR
7. Cleans up the temporary file

**Expected output:**
```
--- Running GitHub Issue-to-PR Agent Sim ---
Agent Plan:
 Plan for Issue #101:
1. Inspect src/calculator.py
2. Add empty list check in sum() method to return 0
3. Run test suite to verify success.
Applying fix to calculator.py...
Tests passed: True
PR Created: https://github.com/mock-repo/pulls/42
```

## Tests

```bash
make test
```

Current test coverage:
- **`tests/test_core.py`** — validates the `/health` endpoint returns 200 with correct service name (`github-issue-pr-agent`) and dependency status object

Planned test coverage:
- Unit tests for `CodePlanner.plan_changes()` with various issue formats
- Unit tests for `CodeEditor.apply_fix()` with allowlist enforcement
- Integration tests for the full pipeline with mocked GitHub API
- Safety tests verifying that disallowed paths and repos are rejected

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Returns service health with database and Redis connectivity status |

**Planned endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/issues/process` | Submit a GitHub issue URL for agent processing |
| `GET` | `/issues/{id}/status` | Check processing status of a submitted issue |
| `GET` | `/issues/{id}/plan` | Retrieve the generated implementation plan |
| `GET` | `/audit/log` | Query the audit trail of agent actions |
| `POST` | `/issues/{id}/approve` | Human approval gate before PR creation |

## Configuration

Key environment variables from `.env.example`:

| Variable | Purpose | Default |
|----------|---------|---------|
| `APP_NAME` | Service identifier in logs and health checks | `github-issue-pr-agent` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/postgres` |
| `REDIS_URL` | Redis connection for Celery broker and result backend | `redis://localhost:6379/0` |
| `GITHUB_TOKEN` | Personal access token for GitHub API (requires `repo` scope) | — |
| `OPENAI_API_KEY` | LLM provider for plan generation | — |
| `DEBUG` | Enable hot-reload and verbose logging | `true` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

## Known Limitations

- **Mock-only GitHub client** — `MockGitHubClient` returns hardcoded data; real GitHub API integration is not yet wired
- **Hardcoded fix logic** — `CodeEditor.apply_fix()` performs a string replacement rather than LLM-driven code generation
- **No allowlist enforcement** — the path/repo allowlist safety layer is designed but not yet implemented in code
- **Test runner is a stub** — `LocalTestRunner.run_tests()` always returns `True` without executing any actual tests
- **No audit persistence** — audit log storage to PostgreSQL is planned but not implemented
- **No approval gate** — human-in-the-loop approval flow is designed but not yet present in the API
- **Single-issue processing** — no batch processing or webhook-triggered pipeline yet
- **Template CI** — GitHub Actions workflow uses the shared template and may fail on `shared-core` import in isolated CI

## Roadmap

- [x] **Phase 0** — Project skeleton with FastAPI, health check, Docker Compose, CI
- [ ] **Phase 1** — Real GitHub API client, issue fetching by label, branch creation
- [ ] **Phase 2** — LLM-powered plan generation with Hermes agent framework
- [ ] **Phase 3** — Sandboxed code editing with allowlist enforcement and audit logging
- [ ] **Phase 4** — Subprocess test runner with output parsing and failure classification
- [ ] **Phase 5** — Draft PR creation with structured summary and risk assessment
- [ ] **Phase 6** — Human approval API endpoint and webhook integration
- [ ] **Phase 7** — Demo repository with before/after walkthrough and screenshots

## Related Projects

This project is part of a [multi-project AI infrastructure showcase](../). It integrates with:

- **[hermes-agent-framework](../hermes-agent-framework/)** — provides the agent orchestration framework for chaining planner → editor → tester steps
- **[async-workflow-engine](../async-workflow-engine/)** — workflow definition and execution engine for the issue processing pipeline
- **[llm-cost-latency-monitor](../llm-cost-latency-monitor/)** — tracks LLM API costs and latency for plan generation calls
- **[shared-core](../shared-core/)** — config, database, Redis, logging, and error handling utilities
