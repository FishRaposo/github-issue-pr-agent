"""Sandbox provisioning tests."""

from pathlib import Path

import pytest

from issue_pr_agent.sandbox import cleanup_sandbox, provision_sandbox


class TestSandbox:
    def test_provision_copies_demo_repo(self):
        path = provision_sandbox(init_git=False)
        try:
            assert (Path(path) / "calculator.py").exists()
            assert (Path(path) / "test_calculator.py").exists()
        finally:
            cleanup_sandbox(path)

    def test_provision_is_isolated_copy(self):
        a = provision_sandbox(init_git=False)
        b = provision_sandbox(init_git=False)
        try:
            assert a != b
            (Path(a) / "calculator.py").write_text("changed")
            assert (Path(b) / "calculator.py").read_text() != "changed"
        finally:
            cleanup_sandbox(a)
            cleanup_sandbox(b)

    def test_provision_with_git_init(self):
        from issue_pr_agent.git_ops import GitOps

        path = provision_sandbox(init_git=True)
        try:
            assert GitOps(workspace_root=path).is_repo()
        finally:
            cleanup_sandbox(path)

    def test_missing_source_raises(self):
        with pytest.raises(FileNotFoundError):
            provision_sandbox(source="/no/such/repo")

    def test_cleanup_is_idempotent(self):
        path = provision_sandbox(init_git=False)
        cleanup_sandbox(path)
        cleanup_sandbox(path)  # second call must not raise
        assert not Path(path).exists()
