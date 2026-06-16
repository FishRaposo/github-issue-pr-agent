# Execution plan — github-issue-pr-agent

How this project went from a ~60% MVP skeleton to a fully implemented, tested, and
documented showcase, and how to verify it. This is the engineering log + runbook.

---

## Goal

A safe, offline-first GitHub issue-to-PR agent that:

- reads an issue, plans a fix, edits **allowlisted** paths in a **sandbox**, runs
  tests, and opens a **draft** PR **only after human approval**;
- runs and tests with **no API keys, no database, no broker**;
- becomes real when keyed (GitHub REST, OpenAI/Anthropic, PostgreSQL, Celery);
- leverages `shared_core` (v1.3.0) rather than re-mocking infrastructure.

---

## Starting state (skeleton)

- `MockGitHubClient` returned hardcoded data; `RealGitHubClient` did not exist.
- `CodePlanner` returned a static string; no structured plan.
- `CodeEditor` did a single literal `return val` replacement with weak path checks.
- `LocalTestRunner` was a thin stub; `GitOps.push` could push anything.
- `worker.py` had a trivial task; no orchestration, no approval gate, no run store.
- Only `/health` + ad-hoc sync endpoint existed; audit was a JSONL file.
- `demo_repo` had a buggy `calculator.py` but **no failing test** to drive the loop.
- Tests were shallow; docs described the skeleton.

---

## Work performed

### Domain logic (stubs → real)
1. **`config.py`** — added `GITHUB_MODE`, allow/block globs, protected branches,
   `AUTO_APPROVE`, `SANDBOX_REPO_PATH`, `DB_CONNECT_TIMEOUT`, with parsing helpers.
2. **`planner.py`** — structured `FixPlan`; sim default + real `LLMClientFactory`
   path with graceful fallback (mirrors `llm-cost-latency-monitor/sdk.py`).
3. **`editor.py`** — `check_path` safety gate (containment + allowlist + blocklist),
   `apply_edits`, `write_file`, structured `EditResult`/`SafetyReport`.
4. **`git_ops.py`** — `GitResult`, no-main guard on create/commit, refuse push of
   protected branches, `merge` hard no-op, `init_repo`, `diff`.
5. **`github.py`** — `MockGitHubClient` (deterministic) + `RealGitHubClient`
   (`BaseHTTPClient`, draft PRs) + `build_github_client` selector.
6. **`test_runner.py`** — real subprocess pytest with summary parsing + timeout.
7. **`sandbox.py`** — disposable repo provisioning (never edit in place).
8. **`agent.py`** — `IssuePRAgent` orchestrator + `FixStrategy` + the approval gate.
9. **`models.py` / `store.py` / `db.py`** — `agent_runs` + `audit_entries` schema,
   `InMemoryStore`/`DatabaseStore` parity, 2s DB probe with in-memory fallback.
10. **`worker.py`** — real Celery `process_issue_task` + `run_issue_pipeline`,
    importable with no broker.
11. **`main.py`** — `/issues/process`, `/issues/{id}/approve`, `/runs`, `/runs/{id}`,
    `/audit`, `/health`; lifespan DB probe; sync fallback when no broker.

### Demo fixture
- Added `demo_repo/test_calculator.py` with a **failing** case
  (`test_divide_by_zero_returns_none`) + `conftest.py` so the agent's fix flips it
  red → green.

### Persistence
- Added `alembic/` (`env.py`, `script.py.mako`, `versions/0001_initial_schema.py`)
  and `alembic.ini`. Schema also auto-created at runtime when the DB is reachable.

### Tests (shallow → comprehensive)
- `test_planner` (+golden), `test_editor`, `test_git_ops`, `test_test_runner`,
  `test_github`, `test_store` (in-memory + SQLite DB parity), `test_db`,
  `test_sandbox`, `test_agent` (e2e + approval gate + safety), `test_worker`,
  `test_api` (every endpoint, success + error). Shared `conftest.py` fixtures.

### Docs
- Rewrote `README.md` (one-liner, why, what, Mermaid architecture, stack, setup,
  demo, tests, limitations, roadmap), `docs/{architecture,design-decisions,
  failure-modes,security,roadmap}.md`, this execution plan, and `AGENTS.md`.

### Spine
- Updated `Makefile` (worker/migrate/upgrade targets, correct package paths),
  `requirements.txt` / `pyproject.toml` (celery, alembic, gitpython, pyyaml,
  psycopg, PyGithub), `.env.example`, and docker-compose container names.

---

## Verification runbook

```bash
# 1. venv
python -m venv .venv

# 2. install
.venv/Scripts/python -m pip install -e "../shared-core[dev,docparse]" numpy
.venv/Scripts/python -m pip install -e ".[dev]" celery alembic

# 3. lint (must be clean)
.venv/Scripts/python -m ruff format src/issue_pr_agent tests examples alembic
.venv/Scripts/python -m ruff check  src/issue_pr_agent tests examples alembic

# 4. tests (all pass; ~5 min — many spawn a real pytest subprocess)
.venv/Scripts/python -m pytest -q

# 5. demo (exits 0)
.venv/Scripts/python examples/run_demo.py
```

Expected: ruff clean, **92 passed**, demo exits `0` with a before(fail)/after(pass)
walkthrough and a printed audit trail.

---

## Notes & known gaps

- The full test suite is slow because ~20 tests run `pytest` in a subprocess against
  the sandbox (a real signal, intentionally). Run a subset during development, e.g.
  `pytest tests/test_api.py tests/test_store.py -q`.
- Applying free-form model patches and container isolation are intentionally future
  work (see `roadmap.md`). The safety gate, test loop, approval gate, and audit are
  all real and exercised today via the fixed `FixStrategy`.
