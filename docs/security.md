# Security Boundaries & Rules - GitHub Issue-to-PR Agent

This document details the security model, token scope, and execution boundaries for the GitHub Issue-to-PR Agent. Due to its write-access capabilities to code repositories, strict boundaries are vital.

---

## 1. Directory and File Sandbox Boundaries

- **Strict Path Allowlisting**: The `CodeEditor` must validate that target file modifications resolve to paths inside the allowlisted directory. Absolute path normalization (`os.path.realpath`) is required to block directory traversal attacks.
- **Protected Configurations**: The agent is blocked from writing to system configuration files, such as `pyproject.toml`, `requirements.txt`, `Makefile`, `.gitignore`, `.github/workflows/*`, or git hooks (`.git/hooks/*`), preventing environment hijack.
- **Ephemeral Git Working Tree**: Code operations must take place on isolated, short-lived development branches.

---

## 2. GitHub Token Scoping & Access Controls

- **Draft-Only Scope**: The GITHUB_TOKEN used by the agent must have the minimum permissions required:
  - `issues: read/write` (to fetch descriptions and write status logs).
  - `pull_requests: write` (to create drafts).
  - `contents: write` (on development branches only).
- **Protected Branch Enforcement**: The agent must not possess permission to push directly to protected branches (like `main` or `master`) or override pull request branch protection rules.
- **Zero Access to Secrets**: The agent must run in an environment that isolates repository secrets (such as production keys or deployment configurations) from the execution worker.

---

## 3. Command Execution Boundaries

- **No Shell Parameter Injection**: Subprocess executions in the `TestRunner` must avoid dynamic shell spawning (`shell=False` in Python subprocess). Command arguments must be passed as lists rather than raw strings to prevent shell token injection.
- **Input Sanitization**: Issue text must be treated as untrusted data. Issue descriptions must never be fed directly into evaluation pipelines or command parameters.

---

## 4. Audit Trail

- **Immutable Execution Log**: Every git branch creation, file modification, test execution, and pull request generation must write an append-only log record detailing timestamps, diffs, and LLM reasoning steps.
- **Security Alerts**: Any blocked access attempt (e.g. unsafe file editing request) must immediately halt execution and trigger system administrator alerts.
