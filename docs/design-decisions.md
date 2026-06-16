# Design decisions — github-issue-pr-agent

Key technical choices and their trade-offs. Each is an *intentional* decision in
service of the project's thesis: a coding agent whose autonomy is bounded,
auditable, and reversible.

---

## 1. Approval gate before any PR

- **Decision.** The pipeline stops at `awaiting_approval` after a successful test
  run. The **only** code path that creates a pull request is
  `IssuePRAgent.approve_and_open_pr`, reached via `POST /issues/{id}/approve` (or
  `AUTO_APPROVE=true` for unattended demos). PRs are always created as **drafts**.
- **Rationale.** Human-in-the-loop is the strongest single guardrail for an agent
  that writes code. Separating "propose" from "open PR" makes the human the firebreak
  against both bad fixes and prompt-injected ones.
- **Trade-off.** The agent cannot fully automate the path to a merged PR. Acceptable —
  that is the point.

---

## 2. Allowlist + blocklist + sandbox containment in one gate

- **Decision.** Every write goes through `CodeEditor.check_path`, which enforces (a)
  sandbox containment via `Path.resolve()`, (b) an allowlist of editable globs, and
  (c) a blocklist that takes precedence (`.github/**`, `.env*`, build/config files,
  `**/secrets/**`).
- **Rationale.** A hallucination or prompt injection that names a dangerous path is
  refused at the boundary regardless of intent. Centralising all three checks in one
  function means there is exactly one place to audit.
- **Trade-off.** The agent cannot touch dependencies (`requirements.txt`) or CI
  config. That flexibility is deliberately traded away for safety.

---

## 3. Disposable sandbox, never edit in place

- **Decision.** `sandbox.provision_sandbox` copies the target repo into a temp dir
  (optionally `git init`-ing it). The agent's editor, git ops, and test runner all
  operate on the copy; the pristine repo is never modified.
- **Rationale.** Makes the before/after walkthrough repeatable and guarantees a
  failed or malicious run cannot corrupt the source of truth.
- **Trade-off.** A copy per run costs I/O. Negligible for the demo; a container mount
  is the production evolution.

---

## 4. Fixed `FixStrategy` instead of applying model patches

- **Decision.** The planner produces a real plan (sim or LLM), but the actual edit is
  a deterministic `FixStrategy` (search/replace `Edit`s) that still flows through the
  same safety gate any real patch would.
- **Rationale.** Applying arbitrary model output to disk is the genuinely dangerous
  step. Decoupling it lets the safety model, the test loop, the approval gate, and the
  audit trail all be exercised and tested **today**, deterministically and offline,
  without trusting model output to touch files.
- **Trade-off.** The agent does not yet fix arbitrary issues end-to-end. Wiring
  validated model patches into the editor is roadmap item #1.

---

## 5. No-main guard and no-merge in git ops

- **Decision.** `GitOps` refuses to create/commit-on/push protected branches and
  implements `merge` as a hard no-op.
- **Rationale.** Even with a misconfigured token, the local layer refuses the
  dangerous operations, so safety does not depend solely on GitHub branch protection.
- **Trade-off.** The agent can never self-merge. Intended.

---

## 6. Subprocess pytest (not in-process, not Docker yet)

- **Decision.** `LocalTestRunner` runs `pytest` via `subprocess.run([...],
  shell=False)` with an argument list and a timeout, capturing the exit code and a
  parsed summary.
- **Rationale.** A subprocess gives a clean pass/fail signal and isolation from the
  agent's own interpreter, while staying lightweight for local/CI runs. `shell=False`
  + arg list removes shell-injection surface; the timeout bounds runaway tests.
- **Trade-off.** Test code still runs on the host. Network-isolated container
  execution is the next hardening step (roadmap #2).

---

## 7. Two stores behind one interface, selected by a DB probe

- **Decision.** `InMemoryStore` and `DatabaseStore` implement the same methods.
  `db.check_db()` probes the database with a 2s connect timeout on startup and selects
  the backend; everything else is backend-agnostic.
- **Rationale.** Offline-first: tests and the demo run with no database, while
  production gets durable, queryable history with no code change. This mirrors the
  `db_available` pattern used across the showcase (`llm-cost-latency-monitor`).
- **Trade-off.** A small amount of duplicated surface between the two stores, covered
  by parity tests.

---

## 8. Leverage `shared_core` instead of re-mocking

- **Decision.** Config (`BaseAppConfig`), logging, error handling, health, the HTTP
  client (`BaseHTTPClient`), the LLM factory (`LLMClientFactory`), Celery bootstrap,
  the DB managers, and test mocks (`MockDatabase`) all come from `shared_core`.
- **Rationale.** Consistency across the showcase, less bespoke infrastructure to
  maintain, and a single source of truth for cross-cutting concerns.
- **Trade-off.** A dependency on `shared_core`'s evolving API — pinned to `v1.3.0`.
