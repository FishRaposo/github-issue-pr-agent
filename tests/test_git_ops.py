"""Git operations tests: branch creation, no-main guard, no push/merge."""

from issue_pr_agent.editor import CodeEditor, Edit
from issue_pr_agent.git_ops import GitOps


class TestGitOps:
    def test_sandbox_is_repo(self, sandbox):
        assert GitOps(workspace_root=sandbox).is_repo()

    def test_starts_on_protected_branch(self, sandbox):
        g = GitOps(workspace_root=sandbox)
        assert g.get_current_branch() == "main"
        assert g.is_protected_branch()

    def test_create_feature_branch(self, sandbox):
        g = GitOps(workspace_root=sandbox)
        result = g.create_branch("agent/fix-1")
        assert result.ok
        assert g.get_current_branch() == "agent/fix-1"
        assert not g.is_protected_branch()

    def test_refuse_create_protected_branch(self, sandbox):
        g = GitOps(workspace_root=sandbox)
        assert not g.create_branch("main").ok
        assert not g.create_branch("master").ok

    def test_refuse_commit_on_main(self, sandbox):
        g = GitOps(workspace_root=sandbox)
        # make a change while on main
        CodeEditor(workspace_root=sandbox).apply_edits(
            "calculator.py", [Edit(find="def add", replace="def added")]
        )
        result = g.commit("should be refused")
        assert not result.ok
        assert "protected" in result.detail.lower()

    def test_commit_allowed_on_feature_branch(self, sandbox):
        g = GitOps(workspace_root=sandbox)
        g.create_branch("agent/fix-2")
        CodeEditor(workspace_root=sandbox).apply_edits(
            "calculator.py",
            [
                Edit(
                    find="    return a / b",
                    replace="    if b == 0:\n        return None\n    return a / b",
                )
            ],
        )
        result = g.commit("fix: guard divide", files=["calculator.py"])
        assert result.ok

    def test_refuse_push_protected(self, sandbox):
        g = GitOps(workspace_root=sandbox)
        assert not g.push("main").ok
        assert not g.push("master").ok

    def test_merge_disabled(self, sandbox):
        g = GitOps(workspace_root=sandbox)
        result = g.merge()
        assert not result.ok
        assert "never merge" in result.detail.lower()

    def test_custom_protected_set(self, sandbox):
        g = GitOps(workspace_root=sandbox, protected_branches={"release"})
        # main is no longer protected here, but release is.
        assert not g.create_branch("release").ok
