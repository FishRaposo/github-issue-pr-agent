"""Local git operations on the sandbox repo, with hard safety guards.

All git work happens inside the sandbox working tree via ``subprocess``. The
guards that matter:

* **No-main guard** — ``create_branch`` refuses to leave you on (or commit to) a
  protected branch; commits are rejected while ``HEAD`` is on ``main``/``master``.
* **Never push to protected** — ``push`` refuses to push a protected branch, and
  ``merge`` is intentionally unimplemented (the agent never merges).

Each method returns a :class:`GitResult` so callers can audit the exact command
outcome rather than a bare bool.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger

DEFAULT_PROTECTED = {"main", "master"}


@dataclass
class GitResult:
    """Outcome of a git command."""

    ok: bool
    detail: str = ""
    stdout: str = ""
    stderr: str = ""


class GitOps:
    """Safely manages git operations within the workspace sandbox."""

    def __init__(
        self,
        workspace_root: str = ".",
        protected_branches: Optional[set[str]] = None,
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.protected_branches = protected_branches or set(DEFAULT_PROTECTED)

    def _run(self, args: list[str], timeout: int = 20) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(self.workspace_root),
        )

    # ---- introspection ------------------------------------------------------
    def is_repo(self) -> bool:
        try:
            result = self._run(["rev-parse", "--is-inside-work-tree"])
            return result.returncode == 0 and result.stdout.strip() == "true"
        except Exception:
            return False

    def init_repo(self) -> GitResult:
        """Initialise a git repo in the sandbox (idempotent; for demos/tests)."""
        try:
            self._run(["init"])
            self._run(["config", "user.email", "agent@example.com"])
            self._run(["config", "user.name", "issue-pr-agent"])
            # Ensure we have an initial commit on a protected default branch.
            self._run(["add", "-A"])
            self._run(["commit", "-m", "initial", "--allow-empty"])
            self._run(["branch", "-M", "main"])
            return GitResult(ok=True, detail="initialised")
        except Exception as exc:
            return GitResult(ok=False, detail=str(exc))

    def get_current_branch(self) -> str:
        try:
            result = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
            return result.stdout.strip() or "main"
        except Exception:
            return "main"

    def is_protected_branch(self, branch: Optional[str] = None) -> bool:
        branch = branch or self.get_current_branch()
        return branch in self.protected_branches

    # ---- write operations ---------------------------------------------------
    def create_branch(self, branch_name: str) -> GitResult:
        """Create and switch to a feature branch (refuses protected names)."""
        if branch_name in self.protected_branches:
            msg = f"Refusing to create protected branch '{branch_name}'"
            logger.error(msg)
            return GitResult(ok=False, detail=msg)
        try:
            result = self._run(["checkout", "-b", branch_name])
            if result.returncode == 0:
                logger.info(f"Created branch: {branch_name}")
                return GitResult(ok=True, detail=branch_name, stdout=result.stdout)
            # Branch may already exist — try to switch.
            switch = self._run(["checkout", branch_name])
            if switch.returncode == 0:
                return GitResult(ok=True, detail=branch_name, stdout=switch.stdout)
            return GitResult(
                ok=False, detail=result.stderr.strip(), stderr=result.stderr
            )
        except Exception as exc:
            logger.error(f"Git error creating branch: {exc}")
            return GitResult(ok=False, detail=str(exc))

    def commit(self, message: str, files: Optional[list[str]] = None) -> GitResult:
        """Stage and commit changes; refuses to commit on a protected branch."""
        current = self.get_current_branch()
        if self.is_protected_branch(current):
            msg = f"Refusing to commit on protected branch '{current}'"
            logger.error(msg)
            return GitResult(ok=False, detail=msg)
        try:
            if files:
                self._run(["add", *files])
            else:
                self._run(["add", "-A"])
            result = self._run(["commit", "-m", message])
            if result.returncode == 0:
                logger.info(f"Committed on {current}: {message}")
                return GitResult(ok=True, detail=current, stdout=result.stdout)
            return GitResult(
                ok=False, detail=result.stderr.strip(), stderr=result.stderr
            )
        except Exception as exc:
            logger.error(f"Git error committing: {exc}")
            return GitResult(ok=False, detail=str(exc))

    def push(self, branch_name: str, remote: str = "origin") -> GitResult:
        """Push a feature branch; refuses to push a protected branch."""
        if branch_name in self.protected_branches:
            msg = f"Refusing to push protected branch '{branch_name}'"
            logger.error(msg)
            return GitResult(ok=False, detail=msg)
        try:
            result = self._run(["push", remote, branch_name], timeout=30)
            return GitResult(
                ok=result.returncode == 0,
                detail=result.stderr.strip() or "pushed",
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except Exception as exc:
            logger.error(f"Git error pushing: {exc}")
            return GitResult(ok=False, detail=str(exc))

    def merge(self, *_args, **_kwargs) -> GitResult:
        """The agent never merges — this is intentionally a hard no-op."""
        msg = "Merge is disabled: the agent never merges branches"
        logger.warning(msg)
        return GitResult(ok=False, detail=msg)

    def diff(self) -> str:
        """Return the working-tree diff (for audit / PR body)."""
        try:
            staged = self._run(["diff", "HEAD"])
            return staged.stdout
        except Exception:
            return ""
