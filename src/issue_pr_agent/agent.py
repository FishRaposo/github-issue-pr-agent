"""The issue-to-PR orchestrator.

Ties the components into a safe, auditable pipeline and enforces the approval
gate. The lifecycle of a run:

1. ``create_run`` — register the run (status ``pending``).
2. ``get_issue`` — fetch the issue (mock or real GitHub).
3. ``plan_changes`` — produce a structured :class:`~.planner.FixPlan`.
4. ``create_branch`` — leave the protected default branch (no-main guard).
5. ``apply_fix`` — edit only allowlisted paths in the sandbox.
6. ``run_tests`` — prove the fix with a real pytest subprocess.
7. status ``awaiting_approval`` — **no PR is opened yet**.
8. ``approve_and_open_pr`` — a human (or ``AUTO_APPROVE``) approves, then a
   **draft** PR is opened. This is the only path that creates a PR.

Every step is recorded to the active store's audit trail.
"""

import json
from dataclasses import dataclass
from typing import Any, Optional

from loguru import logger

from .editor import CodeEditor, Edit
from .git_ops import GitOps
from .github import RealGitHubClient
from .planner import CodePlanner, FixPlan
from .test_runner import LocalTestRunner


@dataclass
class FixStrategy:
    """A deterministic edit recipe keyed to a target file.

    For the offline demo the agent knows the canonical fix for the bundled
    ``calculator.py`` bug. In a real deployment the editor would consume edits
    proposed by the LLM plan; here we keep the edit explicit and auditable.
    """

    target_file: str
    edits: list[Edit]
    new_files: Optional[dict[str, str]] = None


# Canonical fix for the demo_repo division-by-zero bug.
DEMO_FIX = FixStrategy(
    target_file="calculator.py",
    edits=[
        Edit(
            find="def divide(a, b):\n    return a / b",
            replace=(
                "def divide(a, b):\n"
                "    if b == 0:\n"
                "        return None\n"
                "    return a / b"
            ),
        )
    ],
)


class IssuePRAgent:
    """Orchestrates the safe issue-to-PR pipeline against a sandbox repo."""

    def __init__(
        self,
        store: Any,
        github_client: Any,
        sandbox_path: str,
        api_keys: Optional[dict] = None,
        planner_model: str = "gpt-4o-mini",
        protected_branches: Optional[set[str]] = None,
        allowed_globs: Optional[list[str]] = None,
        blocked_globs: Optional[list[str]] = None,
        auto_approve: bool = False,
        fix_strategy: Optional[FixStrategy] = None,
    ):
        self.store = store
        self.github = github_client
        self.sandbox_path = sandbox_path
        self.auto_approve = auto_approve
        self.fix_strategy = fix_strategy or DEMO_FIX

        self.planner = CodePlanner(api_keys=api_keys, model=planner_model)
        self.editor = CodeEditor(
            workspace_root=sandbox_path,
            allowed_globs=allowed_globs,
            blocked_globs=blocked_globs,
        )
        self.git = GitOps(
            workspace_root=sandbox_path, protected_branches=protected_branches
        )
        self.runner = LocalTestRunner(cwd=sandbox_path)

    # ---- pipeline -----------------------------------------------------------
    def process_issue(
        self,
        issue_id: int,
        repo: str,
        mocked_plan: Optional[str] = None,
    ) -> dict[str, Any]:
        """Run steps 1-7. Stops at ``awaiting_approval`` — no PR is opened."""
        run = self.store.create_run(issue_id=issue_id, repo=repo)
        run_id = run["id"]
        self.store.log_action(
            "run_started", {"issue_id": issue_id, "repo": repo}, run_id=run_id
        )

        try:
            issue = self.github.get_issue(issue_id, repo)
            self.store.log_action(
                "issue_fetched", {"title": issue["title"]}, run_id=run_id
            )

            plan: FixPlan = self.planner.plan_changes(
                issue, mocked_response=mocked_plan
            )
            self.store.update_run(run_id, status="planned", plan=plan.to_text())
            self.store.log_action(
                "plan_generated",
                {"target": plan.target_file, "steps": len(plan.steps)},
                run_id=run_id,
            )

            # No-main guard: always move off the protected branch first.
            branch = f"agent/fix-issue-{issue_id}"
            if self.git.is_repo():
                br = self.git.create_branch(branch)
                if not br.ok:
                    return self._fail(run_id, f"branch creation failed: {br.detail}")
                self.store.log_action(
                    "branch_created", {"branch": branch}, run_id=run_id
                )
            self.store.update_run(run_id, branch=branch)

            changed = self._apply_fix(run_id)
            if changed is None:
                return self._fail(run_id, "fix refused by safety gate")
            self.store.update_run(run_id, files_changed=changed)
            self.store.log_action("fix_applied", {"files": changed}, run_id=run_id)

            if self.git.is_repo() and changed:
                commit = self.git.commit(
                    f"fix: issue #{issue_id} - {issue['title'][:60]}",
                    files=changed,
                )
                if commit.ok:
                    self.store.log_action(
                        "changes_committed", {"branch": branch}, run_id=run_id
                    )

            test_result = self.runner.run_tests()
            self.store.update_run(
                run_id,
                tests_passed=test_result.passed,
                test_output=test_result.summary,
            )
            self.store.log_action(
                "tests_run",
                {"passed": test_result.passed, "summary": test_result.summary},
                run_id=run_id,
            )

            if not test_result.passed:
                self.store.update_run(run_id, status="failed", error="tests failed")
                self.store.log_action("run_failed", {"reason": "tests"}, run_id=run_id)
                return self.store.get_run(run_id)

            self.store.update_run(run_id, status="awaiting_approval")
            self.store.log_action("awaiting_approval", {}, run_id=run_id)

            if self.auto_approve:
                return self.approve_and_open_pr(run_id, actor="auto")

            return self.store.get_run(run_id)
        except Exception as exc:  # noqa: BLE001 - record and report, never crash API
            logger.exception("process_issue failed")
            return self._fail(run_id, f"{type(exc).__name__}: {exc}")

    def _apply_fix(self, run_id: str) -> Optional[list[str]]:
        """Apply the fix strategy; return changed paths or None if refused."""
        changed: list[str] = []
        strategy = self.fix_strategy

        if strategy.new_files:
            for path, content in strategy.new_files.items():
                result = self.editor.write_file(path, content)
                if not result.ok:
                    self.store.log_action(
                        "fix_refused",
                        {"path": path, "reason": result.reason},
                        run_id=run_id,
                    )
                    return None
                changed.append(path)

        if strategy.edits:
            result = self.editor.apply_edits(strategy.target_file, strategy.edits)
            if not result.ok:
                self.store.log_action(
                    "fix_refused",
                    {"path": strategy.target_file, "reason": result.reason},
                    run_id=run_id,
                )
                return None
            if result.changed:
                changed.append(strategy.target_file)

        return changed

    # ---- approval gate ------------------------------------------------------
    def approve_and_open_pr(self, run_id: str, actor: str = "human") -> dict[str, Any]:
        """Approve a run that is awaiting approval and open a DRAFT PR."""
        run = self.store.get_run(run_id)
        if run is None:
            raise ValueError(f"Unknown run {run_id}")

        if run["status"] not in ("awaiting_approval", "approved"):
            self.store.log_action(
                "approval_rejected",
                {"reason": f"run in status '{run['status']}'"},
                actor=actor,
                run_id=run_id,
            )
            raise PermissionError(
                f"Run {run_id} is not awaiting approval (status={run['status']})"
            )

        # Idempotency: 'approved' is an accepted re-entry status, but if a PR was
        # already opened for this run we must NOT open a second one — return the
        # existing run unchanged. (A 'completed' run is already rejected above.)
        if run.get("pr_url"):
            return run

        self.store.update_run(run_id, approved=True, status="approved")
        self.store.log_action("approved", {"actor": actor}, actor=actor, run_id=run_id)

        issue = self.github.get_issue(run["issue_id"], run["repo"])
        plan_text = run.get("plan") or ""
        pr_body = (
            f"Automated fix for issue #{run['issue_id']}.\n\n"
            f"{plan_text}\n\nFiles changed: "
            f"{json.dumps(run.get('files_changed', []))}"
        )
        branch = run.get("branch") or ""

        # In real mode the feature branch lives only in the disposable sandbox,
        # so we must publish it to the remote before the PR can reference it.
        # The mock/sim/offline path keeps everything in-process and skips this.
        if isinstance(self.github, RealGitHubClient) and branch:
            self.github.create_branch(run["repo"], branch)
            pushed = self.git.push(branch)
            self.store.log_action(
                "branch_pushed",
                {"branch": branch, "ok": pushed.ok, "detail": pushed.detail},
                actor=actor,
                run_id=run_id,
            )

        pr_url = self.github.create_pull_request(
            run["repo"],
            f"fix: {issue['title']}",
            pr_body,
            branch=branch,
            draft=True,
        )
        self.store.update_run(run_id, pr_url=pr_url, status="completed")
        self.store.log_action(
            "pr_created", {"pr_url": pr_url, "draft": True}, actor=actor, run_id=run_id
        )
        return self.store.get_run(run_id)

    def _fail(self, run_id: str, reason: str) -> dict[str, Any]:
        self.store.update_run(run_id, status="failed", error=reason)
        self.store.log_action("run_failed", {"reason": reason}, run_id=run_id)
        return self.store.get_run(run_id)
