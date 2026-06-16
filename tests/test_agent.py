"""End-to-end agent pipeline + approval-gate tests on the demo sandbox."""

import pytest

from issue_pr_agent.agent import DEMO_FIX, FixStrategy, IssuePRAgent
from issue_pr_agent.editor import Edit
from issue_pr_agent.github import MockGitHubClient, RealGitHubClient


def _agent(store, sandbox, auto_approve=False):
    return IssuePRAgent(
        store=store,
        github_client=MockGitHubClient(),
        sandbox_path=sandbox,
        auto_approve=auto_approve,
    )


class TestEndToEnd:
    def test_pipeline_stops_at_approval(self, memory_store, sandbox):
        run = _agent(memory_store, sandbox).process_issue(101, "owner/repo")
        assert run["status"] == "awaiting_approval"
        assert run["tests_passed"] is True
        assert run["files_changed"] == ["calculator.py"]
        assert run["pr_url"] is None  # no PR before approval

    def test_full_audit_trail(self, memory_store, sandbox):
        run = _agent(memory_store, sandbox).process_issue(101, "owner/repo")
        actions = [a["action"] for a in memory_store.get_audit(run_id=run["id"])]
        for expected in [
            "run_started",
            "issue_fetched",
            "plan_generated",
            "branch_created",
            "fix_applied",
            "tests_run",
            "awaiting_approval",
        ]:
            assert expected in actions

    def test_branch_is_not_main(self, memory_store, sandbox):
        run = _agent(memory_store, sandbox).process_issue(101, "owner/repo")
        assert run["branch"] == "agent/fix-issue-101"
        assert run["branch"] not in ("main", "master")

    def test_auto_approve_opens_pr(self, memory_store, sandbox):
        run = _agent(memory_store, sandbox, auto_approve=True).process_issue(
            101, "owner/repo"
        )
        assert run["status"] == "completed"
        assert run["pr_url"]


class TestApprovalGate:
    def test_approve_opens_draft_pr(self, memory_store, sandbox):
        agent = _agent(memory_store, sandbox)
        run = agent.process_issue(101, "owner/repo")
        approved = agent.approve_and_open_pr(run["id"], actor="human")
        assert approved["status"] == "completed"
        assert approved["approved"] is True
        assert approved["pr_url"]
        actions = [a["action"] for a in memory_store.get_audit(run_id=run["id"])]
        assert "approved" in actions and "pr_created" in actions

    def test_approve_unknown_run_raises(self, memory_store, sandbox):
        with pytest.raises(ValueError):
            _agent(memory_store, sandbox).approve_and_open_pr("nope")

    def test_cannot_approve_non_awaiting_run(self, memory_store, sandbox):
        agent = _agent(memory_store, sandbox)
        run = memory_store.create_run(101, "owner/repo")  # status pending
        with pytest.raises(PermissionError):
            agent.approve_and_open_pr(run["id"])

    def test_double_approval_is_idempotent_status(self, memory_store, sandbox):
        agent = _agent(memory_store, sandbox)
        run = agent.process_issue(101, "owner/repo")
        agent.approve_and_open_pr(run["id"])
        # second approval: run is now 'completed' (not awaiting); should refuse.
        with pytest.raises(PermissionError):
            agent.approve_and_open_pr(run["id"])

    def test_approved_run_with_pr_url_does_not_reopen(self, memory_store, sandbox):
        # A run re-entered at status 'approved' that already has a PR must NOT
        # open a second one; the existing run is returned unchanged.
        agent = _agent(memory_store, sandbox)
        run = agent.process_issue(101, "owner/repo")
        first = agent.approve_and_open_pr(run["id"])
        assert first["pr_url"]
        # Force the re-entry status the guard is meant to cover.
        memory_store.update_run(run["id"], status="approved")
        before = len(
            [
                a
                for a in memory_store.get_audit(run_id=run["id"])
                if a["action"] == "pr_created"
            ]
        )
        again = agent.approve_and_open_pr(run["id"])
        assert again["pr_url"] == first["pr_url"]
        after = len(
            [
                a
                for a in memory_store.get_audit(run_id=run["id"])
                if a["action"] == "pr_created"
            ]
        )
        assert after == before  # no second PR opened


class TestSafetyInPipeline:
    def test_fix_refused_when_target_blocked(self, memory_store, sandbox):
        # A fix strategy that targets a blocked path must fail the run.
        strategy = FixStrategy(
            target_file="pyproject.toml",
            edits=[Edit(find="a", replace="b")],
        )
        agent = IssuePRAgent(
            store=memory_store,
            github_client=MockGitHubClient(),
            sandbox_path=sandbox,
            fix_strategy=strategy,
        )
        run = agent.process_issue(101, "owner/repo")
        assert run["status"] == "failed"
        actions = [a["action"] for a in memory_store.get_audit(run_id=run["id"])]
        assert "fix_refused" in actions

    def test_failing_tests_block_approval(self, memory_store, sandbox):
        # A no-op fix leaves the bug -> tests fail -> never reaches approval.
        strategy = FixStrategy(
            target_file="calculator.py",
            edits=[Edit(find="NON_EXISTENT", replace="x")],
        )
        agent = IssuePRAgent(
            store=memory_store,
            github_client=MockGitHubClient(),
            sandbox_path=sandbox,
            fix_strategy=strategy,
        )
        run = agent.process_issue(101, "owner/repo")
        assert run["status"] == "failed"
        assert run["tests_passed"] is False

    def test_demo_fix_constant_is_wellformed(self):
        assert DEMO_FIX.target_file == "calculator.py"
        assert DEMO_FIX.edits and DEMO_FIX.edits[0].find


class _RecordingRealClient(RealGitHubClient):
    """A RealGitHubClient that records calls without touching the network.

    Subclassing keeps ``isinstance(self.github, RealGitHubClient)`` True (so the
    real-mode push branch in ``approve_and_open_pr`` runs) while overriding every
    method that would otherwise make an HTTP call.
    """

    def __init__(self):
        super().__init__(token="x")
        self.calls: list[str] = []

    def get_issue(self, issue_id, repo=""):
        return {"id": issue_id, "title": "t", "body": "", "labels": []}

    def create_branch(self, repo, branch, base="main"):
        self.calls.append("create_branch")
        return True

    def create_pull_request(
        self, repo, title, body, branch="", base="main", draft=True
    ):
        self.calls.append("create_pull_request")
        return "https://github.com/owner/repo/pull/7"


class TestRealModePush:
    def test_real_mode_publishes_branch_before_pr(self, memory_store, sandbox):
        # In real mode the branch lives only in the sandbox, so it must be
        # pushed/created on the remote BEFORE the PR references it.
        client = _RecordingRealClient()
        agent = IssuePRAgent(
            store=memory_store, github_client=client, sandbox_path=sandbox
        )
        run = agent.process_issue(101, "owner/repo")
        agent.approve_and_open_pr(run["id"])
        # The remote branch is created before the PR is opened.
        assert client.calls.index("create_branch") < client.calls.index(
            "create_pull_request"
        )
        actions = [a["action"] for a in memory_store.get_audit(run_id=run["id"])]
        assert "branch_pushed" in actions

    def test_mock_mode_does_not_push(self, memory_store, sandbox):
        # The offline mock path stays unchanged: no branch_pushed audit entry.
        agent = _agent(memory_store, sandbox)
        run = agent.process_issue(101, "owner/repo")
        agent.approve_and_open_pr(run["id"])
        actions = [a["action"] for a in memory_store.get_audit(run_id=run["id"])]
        assert "branch_pushed" not in actions
