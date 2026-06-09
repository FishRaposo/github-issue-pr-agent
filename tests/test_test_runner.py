from unittest.mock import MagicMock

from issue_pr_agent.test_runner import LocalTestRunner


class TestLocalTestRunner:
    def test_run_tests_with_pytest_found(self, monkeypatch):
        import subprocess

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_result)

        runner = LocalTestRunner()
        result = runner.run_tests(".")
        assert result["passed"] is True

    def test_run_tests_with_pytest_failure(self, monkeypatch):
        import subprocess

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "1 failed"
        mock_result.stderr = "AssertionError"
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_result)

        runner = LocalTestRunner()
        result = runner.run_tests(".")
        assert result["passed"] is False
        assert "AssertionError" in result["stderr"]

    def test_run_tests_pytest_not_found(self, monkeypatch):
        import subprocess

        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError))

        runner = LocalTestRunner()
        result = runner.run_tests(".")
        assert result["passed"] is True

    def test_run_tests_has_expected_fields(self, monkeypatch):
        import subprocess

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_result)

        runner = LocalTestRunner()
        result = runner.run_tests(".")
        assert "passed" in result
        assert "stdout" in result
        assert "stderr" in result
