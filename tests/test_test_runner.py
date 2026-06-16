"""Subprocess pytest runner tests against the real sandbox."""

from issue_pr_agent.editor import CodeEditor, Edit
from issue_pr_agent.test_runner import LocalTestRunner, make_runner

_DIVIDE_FIX = Edit(
    find="def divide(a, b):\n    return a / b",
    replace=(
        "def divide(a, b):\n    if b == 0:\n        return None\n    return a / b"
    ),
)


class TestLocalTestRunner:
    def test_buggy_sandbox_fails(self, sandbox_no_git):
        result = LocalTestRunner(cwd=sandbox_no_git).run_tests()
        assert not result.passed
        assert "failed" in result.summary

    def test_fixed_sandbox_passes(self, sandbox_no_git):
        CodeEditor(workspace_root=sandbox_no_git).apply_edits(
            "calculator.py", [_DIVIDE_FIX]
        )
        result = LocalTestRunner(cwd=sandbox_no_git).run_tests()
        assert result.passed
        assert "passed" in result.summary

    def test_result_fields(self, sandbox_no_git):
        result = LocalTestRunner(cwd=sandbox_no_git).run_tests()
        d = result.to_dict()
        assert set(d) >= {"passed", "returncode", "stdout", "stderr", "summary"}

    def test_make_runner_missing_path(self):
        assert make_runner("/path/does/not/exist") is None

    def test_make_runner_existing_path(self, sandbox_no_git):
        runner = make_runner(sandbox_no_git)
        assert isinstance(runner, LocalTestRunner)
