import os

from loguru import logger

ALLOWED_EXTENSIONS = {".py", ".txt", ".md", ".yaml", ".yml", ".json", ".toml"}
BLOCKED_PATHS = {
    ".github",
    ".env",
    "Makefile",
    "pyproject.toml",
    "docker-compose.yml",
    "requirements.txt",
}


class CodeEditor:
    """Safely edits source code files within predefined folders."""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)

    def apply_fix(self, filepath: str) -> bool:
        full_path = os.path.realpath(
            os.path.join(self.workspace_root, filepath)
        )
        if not full_path.startswith(self.workspace_root):
            logger.error(f"Blocked directory traversal: {filepath}")
            return False

        filename = os.path.basename(full_path)
        if filename in BLOCKED_PATHS:
            logger.error(f"Blocked path: {filename}")
            return False

        ext = os.path.splitext(full_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.error(f"Blocked extension: {ext}")
            return False

        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            return False

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        fixed_content = content.replace(
            "return val",
            "if not val:\n            return 0\n        return val",
        )

        if fixed_content == content:
            logger.info(f"No changes needed for: {filepath}")
            return True

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        logger.info(f"Applied fix to: {filepath}")
        return True
