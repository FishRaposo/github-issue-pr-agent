import os
import tempfile

import pytest
from issue_pr_agent.editor import CodeEditor


class TestCodeEditor:
    def test_apply_fix_modifies_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.py")
            with open(filepath, "w") as f:
                f.write("def calc():\n    val = None\n    return val\n")

            editor = CodeEditor(workspace_root=tmpdir)
            result = editor.apply_fix("test.py")
            assert result is True

    def test_apply_fix_blocks_disallowed_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CodeEditor(workspace_root=tmpdir)
            result = editor.apply_fix("script.exe")
            assert result is False

    def test_apply_fix_blocks_root_traversal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CodeEditor(workspace_root=tmpdir)
            result = editor.apply_fix("../etc/passwd")
            assert result is False

    def test_apply_fix_blocks_blocked_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CodeEditor(workspace_root=tmpdir)
            result = editor.apply_fix(".env")
            assert result is False

    def test_allowed_extensions_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.md")
            with open(filepath, "w") as f:
                f.write("# Test\n")
            editor = CodeEditor(workspace_root=tmpdir)
            result = editor.apply_fix("test.md")
            assert result is True

    def test_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            editor = CodeEditor(workspace_root=tmpdir)
            result = editor.apply_fix("nonexistent.py")
            assert result is False
