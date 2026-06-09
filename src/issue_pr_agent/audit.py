import json
import os
import time
from pathlib import Path
from typing import Any

from loguru import logger


class AuditLog:
    """Records agent actions with timestamps for traceability."""

    def __init__(self, log_path: str = "audit.jsonl"):
        self.log_path = Path(log_path)

    def log_action(
        self,
        action: str,
        details: dict[str, Any] | None = None,
        user: str = "system",
    ) -> None:
        entry = {
            "timestamp": time.time(),
            "action": action,
            "user": user,
            "details": details or {},
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"Audit: {action}")

    def get_logs(self, limit: int = 100) -> list[dict]:
        if not self.log_path.exists():
            return []
        entries: list[dict] = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries[-limit:]


audit_log = AuditLog()
