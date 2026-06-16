"""Sandbox provisioning helpers.

The agent never edits the pristine ``demo_repo`` in place — it works on a
disposable copy so the before/after walkthrough is repeatable and the original
buggy fixture is preserved. :func:`provision_sandbox` copies a source repo to a
fresh temp directory (optionally initialising git), and the returned path is what
the agent's editor/test-runner/git-ops operate on.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from loguru import logger

# Path to the bundled demo repository, resolved relative to this package.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
DEMO_REPO = PACKAGE_ROOT / "demo_repo"


def provision_sandbox(
    source: Optional[str] = None,
    init_git: bool = True,
) -> str:
    """Copy ``source`` (default: bundled demo_repo) into a temp dir.

    Returns the absolute path of the new sandbox. Caller owns cleanup.
    """
    src = Path(source) if source else DEMO_REPO
    if not src.exists():
        raise FileNotFoundError(f"Sandbox source not found: {src}")

    dest = Path(tempfile.mkdtemp(prefix="issue_pr_sandbox_"))
    # Copy contents into dest (dest already exists from mkdtemp).
    for item in src.iterdir():
        if item.name in {".git", "__pycache__", ".pytest_cache"}:
            continue
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    if init_git:
        from .git_ops import GitOps

        GitOps(workspace_root=str(dest)).init_repo()

    logger.info(f"Provisioned sandbox at {dest}")
    return str(dest)


def cleanup_sandbox(path: str) -> None:
    """Remove a provisioned sandbox directory."""
    shutil.rmtree(path, ignore_errors=True)
