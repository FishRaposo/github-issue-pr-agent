import subprocess
from pathlib import Path

from loguru import logger


class GitOps:
    """Safely manages git operations within the workspace sandbox."""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()

    def create_branch(self, branch_name: str) -> bool:
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.workspace_root),
            )
            if result.returncode == 0:
                logger.info(f"Created branch: {branch_name}")
                return True
            logger.warning(f"Failed to create branch: {result.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Git error creating branch: {e}")
            return False

    def commit(self, message: str, files: list[str] | None = None) -> bool:
        try:
            if files:
                subprocess.run(
                    ["git", "add"] + files,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=str(self.workspace_root),
                )
            else:
                subprocess.run(
                    ["git", "add", "-A"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=str(self.workspace_root),
                )

            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.workspace_root),
            )
            if result.returncode == 0:
                logger.info(f"Committed: {message}")
                return True
            logger.warning(f"Failed to commit: {result.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Git error committing: {e}")
            return False

    def push(self, branch_name: str, remote: str = "origin") -> bool:
        try:
            result = subprocess.run(
                ["git", "push", remote, branch_name],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace_root),
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Git error pushing: {e}")
            return False

    def get_current_branch(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.workspace_root),
            )
            return result.stdout.strip() or "main"
        except Exception:
            return "main"

    def is_main_branch(self) -> bool:
        branch = self.get_current_branch()
        return branch in ("main", "master")


git_ops = GitOps()
