#!/usr/bin/env python3
"""End-to-end before/after walkthrough on the bundled demo_repo.

Runs with NO database, NO broker, NO API keys. It:

1. Provisions a disposable copy of ``demo_repo`` (a buggy ``calculator.py`` plus
   a failing test ``test_divide_by_zero_returns_none``).
2. Shows the BEFORE state: the sandbox test suite fails.
3. Runs the agent pipeline for issue #101 (fetch -> plan -> branch -> edit ->
   test). The pipeline stops at ``awaiting_approval`` — no PR yet.
4. Shows the AFTER state: tests now pass.
5. Approves the run, which opens a (mock) DRAFT pull request.
6. Prints the audit trail.

Exit code 0 on success.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from issue_pr_agent.agent import IssuePRAgent  # noqa: E402
from issue_pr_agent.github import build_github_client  # noqa: E402
from issue_pr_agent.sandbox import cleanup_sandbox, provision_sandbox  # noqa: E402
from issue_pr_agent.store import InMemoryStore  # noqa: E402
from issue_pr_agent.test_runner import LocalTestRunner  # noqa: E402


def _rule(title: str) -> None:
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def main() -> int:
    _rule("GitHub Issue-to-PR Agent — before/after walkthrough")

    store = InMemoryStore()
    sandbox = provision_sandbox()
    try:
        # 1. BEFORE: the sandbox tests fail on the division-by-zero bug.
        _rule("BEFORE: running the sandbox test suite")
        before = LocalTestRunner(cwd=sandbox).run_tests()
        print(f"tests passed: {before.passed}")
        print(f"summary:      {before.summary}")
        assert not before.passed, "expected the buggy sandbox to fail"

        # 2. Run the agent pipeline (offline, deterministic).
        _rule("AGENT: process issue #101")
        agent = IssuePRAgent(
            store=store,
            github_client=build_github_client("mock"),
            sandbox_path=sandbox,
            auto_approve=False,
        )
        run = agent.process_issue(101, "octocat/demo")
        print(f"status:        {run['status']}")
        print(f"branch:        {run['branch']}")
        print(f"files changed: {run['files_changed']}")
        print(f"tests passed:  {run['tests_passed']}")
        print("\nPlan:\n" + (run["plan"] or ""))
        assert run["status"] == "awaiting_approval"
        assert run["pr_url"] is None, "no PR before approval"

        # 3. APPROVAL GATE: open the draft PR only after a human approves.
        _rule("APPROVAL: human approves -> draft PR opened")
        approved = agent.approve_and_open_pr(run["id"], actor="human")
        print(f"status:  {approved['status']}")
        print(f"PR URL:  {approved['pr_url']}")
        assert approved["status"] == "completed"
        assert approved["pr_url"]

        # 4. AUDIT TRAIL
        _rule("AUDIT TRAIL")
        for entry in store.get_audit(run_id=run["id"]):
            print(f"  - {entry['action']:<18} {entry['details']}")

        _rule("DONE — fix verified, draft PR opened, fully audited")
        return 0
    finally:
        cleanup_sandbox(sandbox)


if __name__ == "__main__":
    raise SystemExit(main())
