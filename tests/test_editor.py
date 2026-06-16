"""Editor safety tests: allowlist, blocklist, traversal, and edits."""

from pathlib import Path

from issue_pr_agent.editor import CodeEditor, Edit


class TestSafetyGate:
    def test_allowed_extension_passes(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        assert ed.check_path("calculator.py").allowed

    def test_disallowed_extension_blocked(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        report = ed.check_path("malware.exe")
        assert not report.allowed
        assert "not_allowlisted" in report.rejections

    def test_traversal_blocked(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        report = ed.check_path("../../etc/passwd")
        assert not report.allowed
        assert "path_traversal" in report.rejections

    def test_absolute_path_blocked(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        # An absolute path outside the sandbox must be rejected.
        assert not ed.check_path("/etc/hosts").allowed

    def test_dotenv_blocked(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        report = ed.check_path(".env")
        assert not report.allowed
        assert any(r.startswith("blocked") for r in report.rejections)

    def test_github_dir_blocked(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        assert not ed.check_path(".github/workflows/ci.yml").allowed

    def test_secrets_dir_blocked_at_root(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        assert not ed.check_path("secrets/key.py").allowed

    def test_secrets_dir_blocked_nested(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        assert not ed.check_path("app/secrets/key.py").allowed

    def test_blocklist_overrides_allowlist(self, sandbox_no_git):
        # pyproject.toml matches *.toml (allow) but is on the blocklist.
        ed = CodeEditor(workspace_root=sandbox_no_git)
        assert not ed.check_path("pyproject.toml").allowed

    def test_custom_globs(self, sandbox_no_git):
        ed = CodeEditor(
            workspace_root=sandbox_no_git,
            allowed_globs=["*.md"],
            blocked_globs=[],
        )
        assert ed.check_path("README.md").allowed
        assert not ed.check_path("calculator.py").allowed


class TestApplyEdits:
    def test_apply_edit_changes_file(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        result = ed.apply_edits(
            "calculator.py",
            [
                Edit(
                    find="def divide(a, b):\n    return a / b",
                    replace=(
                        "def divide(a, b):\n    if b == 0:\n"
                        "        return None\n    return a / b"
                    ),
                )
            ],
        )
        assert result.ok and result.changed
        content = (Path(sandbox_no_git) / "calculator.py").read_text()
        assert "if b == 0" in content

    def test_edit_refused_for_blocked_path(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        result = ed.apply_edits(".env", [Edit(find="a", replace="b")])
        assert not result.ok

    def test_edit_missing_file(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        result = ed.apply_edits("nonexistent.py", [Edit(find="a", replace="b")])
        assert not result.ok
        assert result.reason == "File not found"

    def test_no_matching_text_is_ok_but_unchanged(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        result = ed.apply_edits(
            "calculator.py", [Edit(find="THIS_DOES_NOT_EXIST", replace="x")]
        )
        assert result.ok and not result.changed

    def test_write_new_file_allowlisted(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        result = ed.write_file("helpers.py", "x = 1\n")
        assert result.ok and result.changed
        assert (Path(sandbox_no_git) / "helpers.py").exists()

    def test_write_refused_for_blocked_path(self, sandbox_no_git):
        ed = CodeEditor(workspace_root=sandbox_no_git)
        result = ed.write_file(".github/x.yml", "x")
        assert not result.ok
