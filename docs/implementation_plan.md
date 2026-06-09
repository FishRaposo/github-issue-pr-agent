# Implementation Plan - GitHub Issue-to-PR Automation Agent

This document details the step-by-step technical implementation plan and development milestones for **GitHub Issue-to-PR Automation Agent**.

---

## 1. Project Goal
An autonomous software agent that monitors GitHub repositories, plans code modifications for reported issues, runs tests, and creates draft pull requests.

---

## 2. Architecture & Component Map

The repository is structured as a standalone project conforming to operator workspace standards. The core module responsibilities are mapped below:

### 2.1 File Map & Responsibilities
* **`src/issue_pr_agent/github.py`**: GitHub client wrapper handling webhook triggers, cloning repos, and opening PR files.
* **`src/issue_pr_agent/planner.py`**: Reads issue descriptions and generates concrete file modification plans.
* **`src/issue_pr_agent/editor.py`**: Locates code boundaries, updates files safely, and handles merge conflicts.
* **`src/issue_pr_agent/test_runner.py`**: Executes local test suites and compiles run reports to include in pull request descriptions.

### 2.2 Shared Core Dependencies
This service imports standard layers from `shared-core` (sibling dependency library):
* `shared_core.config.BaseAppConfig`: Settings parsing, reading configs from `.env`.
* `shared_core.database.DatabaseManager`: SQL database engine instantiation and session factories.
* `shared_core.redis.RedisManager`: Caching connections and health checks.
* `shared_core.logging.setup_logging`: Structured log formats and correlation ID tracing.
* `shared_core.errors.BaseApplicationError`: Exception mapping and global handlers.

---

## 3. Database Schema & Data Models

### 3.1 Data Schema
PostgreSQL: `issues` (id, repo_fullname, issue_number, title, status, plan_json, pr_url, created_at), `agent_actions` (id, issue_id, action_type, details_json, duration_ms, timestamp).
Redis: Git repository checkout locks and execution queue state manager.

### 3.2 Redis Storage & Caching Patterns
* Caching: Utilizing `@cache` decorator with prefix keys.
* Concurrency: Lock critical tasks using `RedisLock` context managers.

---

## 4. Step-by-Step Implementation Sequence

The project development checklist is ordered into six milestones:

- `[ ]` **Milestone 1 (Design): Design repository sandbox environment, allowlisted directories, and webhook routing.**
- `[ ]` **Milestone 2 (Skeleton): Setup FastAPI payload webhook listener and local repository cloning commands.**
- `[ ]` **Milestone 3 (Core Loop): Implement file editing logic, test execution commands, and PR creation api.**
- `[ ]` **Milestone 4 (Reliability): Enforce strict path checks, block main-branch direct pushing, and set timeout bounds.**
- `[ ]` **Milestone 5 (Showcase): Demo issue-to-PR agent resolving a bug issue in a mock repository and creating a draft PR.**
- `[ ]` **Milestone 6 (Publish): Document sandbox boundaries, allowlisted repository guidelines, and git operations safety.**

---

## 5. Standard Makefile & Developer Commands

```bash
make install          # Set up virtual environment and local editable package
make dev              # Boot the microservice API server locally
make test             # Run local pytest / jest test suites
make lint             # Execute Ruff checks / ESLint verifications
make format           # Standardize style formatting
make typecheck        # Verify static types (Pyright / TypeScript)
make docker-up        # Spawn isolated local PostgreSQL and Redis service containers
make docker-down      # Teardown the isolated local containers stack
make demo             # Execute the runnable demo workflow
make clean            # Remove caches and temporary files
```

---

## 6. Verification & Testing Plan

### 6.1 Automated Tests
* **Core Logic Verification**: Tests for file edit syntax checking, git execution errors, sandbox path restrictions, and test run parsing.
* **Type Safety & Style**: Run `make typecheck` and `make lint` as a pipeline validation hook.
* **Mock Environments**: Utilize `MockDatabase` and `MockRedisClient` inside `tests/conftest.py` to assert correct lifecycle transactions without depending on live network services.

### 6.2 Manual Verification
* Deploy local PostgreSQL and Redis containers with `make docker-up`.
* Execute the runnable script demo `make demo` and review Loguru stdout records.
