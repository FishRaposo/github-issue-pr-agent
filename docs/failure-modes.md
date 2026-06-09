# Failure Modes & Mitigation - GitHub Issue-to-PR Agent

This document details anticipated failure modes, detection strategies, and mitigation pathways for the GitHub Issue-to-PR Agent.

---

## 1. Directory Escape / Unsafe File Edits

- **Cause**: An issue contains malicious instructions designed to hijack the file-editing engine, prompting it to modify paths outside the allowed sandbox (e.g., `../../../etc/hosts` or system config files).
- **Impact**: Server file corruption, credential leakage, or remote code execution.
- **Detection**:
  - CodeEditor logs block events: `"Unsafe filepath attempted: {path}"`.
  - File modification commands exit with permission errors.
- **Mitigation**: Resolve target file paths to absolute paths and assert that they start with the allowlisted workspace directory. Block path separators like `..` or windows disk boundaries (`C:`) in relative parameters.
- **Future Fix**: Run the CodeEditor and TestRunner in a completely isolated, read-only container mount that has write access only to a temporary source repository mount.

---

## 2. GitHub API Rate Limits

- **Cause**: Processing a high volume of issues or frequent polling of repository states exhausts GitHub API token quotas.
- **Impact**: API calls fail with HTTP 403, halting issue checks and PR creation.
- **Detection**: GitHub API responses return `X-RateLimit-Remaining: 0` headers and HTTP 403 status codes.
- **Mitigation**: Implement exponential backoff when rate limit headers are detected. Configure webhook-driven invocation instead of poll-based loops.
- **Future Fix**: Implement token rotation or queue integration that spaces API calls dynamically based on remaining quota windows.

---

## 3. Hanging Test Executions (Infinite Loops)

- **Cause**: The agent modifies a loop condition in code that causes tests to run indefinitely (infinite loop).
- **Impact**: The TestRunner hangs, consuming CPU resources and blocking the queue for all subsequent agent runs.
- **Detection**:
  - Test subprocess duration exceeds maximum limits (e.g., >30 seconds).
  - High host CPU utilization.
- **Mitigation**: Enforce strict timeouts on test suite execution using subprocess parameters (`timeout=30` in Python `subprocess.run`).
- **Future Fix**: Terminate hanging processes automatically and log a test timeout failure observation so the agent knows its edit caused an infinite execution path.

---

## 4. Stale Branches & Merge Conflicts

- **Cause**: The agent creates a branch based on stale repository code, or multiple agents make edits concurrently to the same files.
- **Impact**: The PR creation fails due to git push rejection or immediate merge conflict warnings.
- **Detection**: Git command returns exit codes representing conflicts or branch rejection.
- **Mitigation**: Pull the latest changes from `main` before branching.
- **Future Fix**: Implement automatic rebasing in the git client. If conflicts occur, feed the conflict diff back to the Planner so it can resolve the file layout programmatically.
