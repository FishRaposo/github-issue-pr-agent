"""Sandboxed code editor with allowlist / blocklist enforcement.

The editor is the agent's only write path into the target repository, so every
safety guard lives here:

* **Path containment** — the resolved real path must stay inside the sandbox
  root (blocks ``..`` traversal, absolute paths, and symlink escapes).
* **Allowlist** — the path must match one of the configured allow globs.
* **Blocklist** — the path must not match any block glob (``.github/**``,
  ``.env``, build/config files, ``**/secrets/**``).

Writes are applied as explicit search-and-replace edits so the change is
deterministic and auditable. ``apply_edits`` returns an :class:`EditResult`
describing exactly what happened (and why a write was refused).
"""

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from loguru import logger

# Conservative built-in defaults; overridden by AppConfig globs in production.
DEFAULT_ALLOWED = [
    "*.py",
    "*.txt",
    "*.md",
    "*.yaml",
    "*.yml",
    "*.json",
    "*.toml",
    "*.cfg",
    "*.ini",
]
DEFAULT_BLOCKED = [
    ".github/**",
    ".env",
    ".env.*",
    "Makefile",
    "pyproject.toml",
    "docker-compose.yml",
    "requirements.txt",
    "alembic.ini",
    "**/secrets/**",
]


@dataclass
class EditResult:
    """Outcome of an attempted edit."""

    ok: bool
    path: str
    reason: str = ""
    changed: bool = False
    matched_replacements: int = 0


@dataclass
class Edit:
    """A single search-and-replace operation."""

    find: str
    replace: str


@dataclass
class SafetyReport:
    """Why a path was accepted or rejected by the safety gate."""

    allowed: bool
    reason: str = ""
    rejections: list[str] = field(default_factory=list)


class CodeEditor:
    """Safely edits source files within a sandbox root under allow/block rules."""

    def __init__(
        self,
        workspace_root: str = ".",
        allowed_globs: Optional[list[str]] = None,
        blocked_globs: Optional[list[str]] = None,
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.allowed_globs = allowed_globs or list(DEFAULT_ALLOWED)
        self.blocked_globs = blocked_globs or list(DEFAULT_BLOCKED)

    # ---- safety -------------------------------------------------------------
    def _resolve_within_sandbox(self, filepath: str) -> Optional[Path]:
        """Resolve ``filepath`` and ensure it stays inside the sandbox root."""
        candidate = (self.workspace_root / filepath).resolve()
        try:
            candidate.relative_to(self.workspace_root)
        except ValueError:
            return None
        return candidate

    def check_path(self, filepath: str) -> SafetyReport:
        """Run the full safety gate for ``filepath`` without touching disk."""
        rejections: list[str] = []

        resolved = self._resolve_within_sandbox(filepath)
        if resolved is None:
            rejections.append("path_traversal")
            return SafetyReport(
                allowed=False,
                reason="Path escapes the sandbox root",
                rejections=rejections,
            )

        rel = resolved.relative_to(self.workspace_root).as_posix()

        # Blocklist takes precedence over the allowlist.
        for pattern in self.blocked_globs:
            if self._matches(rel, pattern):
                rejections.append(f"blocked:{pattern}")
                return SafetyReport(
                    allowed=False,
                    reason=f"Path matches blocked pattern '{pattern}'",
                    rejections=rejections,
                )

        if not any(self._matches(rel, p) for p in self.allowed_globs):
            rejections.append("not_allowlisted")
            return SafetyReport(
                allowed=False,
                reason="Path does not match any allowlist pattern",
                rejections=rejections,
            )

        return SafetyReport(allowed=True, reason="ok")

    @staticmethod
    def _matches(rel_path: str, pattern: str) -> bool:
        """Match a relative POSIX path against a glob (basename + full path).

        Adds two conveniences beyond ``fnmatch``: ``dir/**`` matches anything
        under ``dir`` (and ``dir`` itself), and a leading ``**/`` is treated as
        "anywhere including the root", so ``**/secrets/**`` also blocks a
        top-level ``secrets/`` directory.
        """
        basename = os.path.basename(rel_path)
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(basename, pattern):
            return True
        # ``dir/**`` -> matches ``dir`` and anything beneath it.
        if pattern.endswith("/**"):
            prefix = pattern[:-3]
            if rel_path == prefix or rel_path.startswith(prefix + "/"):
                return True
        # ``**/name/**`` -> matches ``name/...`` even at the repository root.
        if pattern.startswith("**/") and pattern.endswith("/**"):
            middle = pattern[3:-3]
            segments = rel_path.split("/")
            if middle in segments:
                return True
        return False

    # ---- editing ------------------------------------------------------------
    def apply_edits(self, filepath: str, edits: list[Edit]) -> EditResult:
        """Apply a list of search-and-replace edits after the safety gate."""
        report = self.check_path(filepath)
        if not report.allowed:
            logger.error(f"Edit refused for {filepath}: {report.reason}")
            return EditResult(ok=False, path=filepath, reason=report.reason)

        resolved = self._resolve_within_sandbox(filepath)
        assert resolved is not None  # guaranteed by check_path
        if not resolved.exists():
            return EditResult(ok=False, path=filepath, reason="File not found")

        original = resolved.read_text(encoding="utf-8")
        content = original
        matched = 0
        for edit in edits:
            if edit.find in content:
                matched += content.count(edit.find)
                content = content.replace(edit.find, edit.replace)

        if content == original:
            logger.info(f"No changes applied to {filepath}")
            return EditResult(
                ok=True, path=filepath, reason="No matching text", changed=False
            )

        resolved.write_text(content, encoding="utf-8")
        logger.info(f"Applied {matched} replacement(s) to {filepath}")
        return EditResult(
            ok=True,
            path=filepath,
            reason="ok",
            changed=True,
            matched_replacements=matched,
        )

    def write_file(self, filepath: str, content: str) -> EditResult:
        """Create or overwrite a file after the safety gate (used for new files)."""
        report = self.check_path(filepath)
        if not report.allowed:
            logger.error(f"Write refused for {filepath}: {report.reason}")
            return EditResult(ok=False, path=filepath, reason=report.reason)

        resolved = self._resolve_within_sandbox(filepath)
        assert resolved is not None
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return EditResult(ok=True, path=filepath, reason="ok", changed=True)
