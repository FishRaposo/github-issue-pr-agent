"""Subprocess-based pytest runner for the sandbox repository.

Runs the target repo's test suite in a child process and parses the exit code
and captured output into a structured :class:`TestRunResult`. This is how the
agent proves a fix actually works *before* any PR is opened — the before/after
walkthrough on ``demo_repo`` depends on it: the run fails first, then passes once
the editor applies the fix.
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger


@dataclass
class TestRunResult:
    """Structured outcome of a test run."""

    passed: bool
    returncode: int
    stdout: str = ""
    stderr: str = ""
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "summary": self.summary,
        }


class LocalTestRunner:
    """Executes pytest in a subprocess and parses the result."""

    def __init__(self, cwd: str = ".", timeout: int = 60):
        self.cwd = Path(cwd).resolve()
        self.timeout = timeout

    def run_tests(self, test_path: str = ".") -> TestRunResult:
        """Run pytest at ``test_path`` (relative to the sandbox cwd)."""
        cmd = [sys.executable, "-m", "pytest", test_path, "-q", "--tb=short"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.cwd),
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Tests timed out after {self.timeout}s")
            return TestRunResult(
                passed=False,
                returncode=-1,
                stderr=f"Timeout after {self.timeout}s",
                summary="timeout",
            )
        except FileNotFoundError as exc:
            logger.error(f"pytest could not be launched: {exc}")
            return TestRunResult(
                passed=False, returncode=-1, stderr=str(exc), summary="not_found"
            )

        # pytest exit code 0 => all passed; 5 => no tests collected.
        passed = result.returncode == 0
        summary = self._extract_summary(result.stdout)
        if passed:
            logger.info(f"Tests passed: {summary}")
        else:
            logger.warning(f"Tests failed (rc={result.returncode}): {summary}")
        return TestRunResult(
            passed=passed,
            returncode=result.returncode,
            stdout=result.stdout[-4000:],
            stderr=result.stderr[-2000:],
            summary=summary,
        )

    @staticmethod
    def _extract_summary(stdout: str) -> str:
        """Pull the final pytest summary line (e.g. '1 passed in 0.02s')."""
        for line in reversed(stdout.splitlines()):
            stripped = line.strip().strip("=").strip()
            if stripped and any(
                kw in stripped for kw in ("passed", "failed", "error", "no tests")
            ):
                return stripped
        return stdout.strip().splitlines()[-1] if stdout.strip() else ""


def make_runner(sandbox_path: str, timeout: int = 60) -> Optional[LocalTestRunner]:
    """Construct a runner for an existing sandbox path, or None if missing."""
    path = Path(sandbox_path)
    if not path.exists():
        return None
    return LocalTestRunner(cwd=str(path), timeout=timeout)
