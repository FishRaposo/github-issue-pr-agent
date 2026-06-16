"""Audit-log compatibility shim.

The canonical audit trail now lives in :mod:`issue_pr_agent.store` (in-memory or
DB-backed, selected by the availability probe). This module keeps a tiny
process-local :class:`AuditLog` for ad-hoc logging and backwards compatibility;
new code should use the active store's ``log_action`` / ``get_audit`` instead.
"""

import time
from typing import Any, Optional

from loguru import logger


class AuditLog:
    """Minimal in-process audit log (delegates the real trail to the store)."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def log_action(
        self,
        action: str,
        details: Optional[dict[str, Any]] = None,
        actor: str = "system",
    ) -> dict[str, Any]:
        entry = {
            "timestamp": time.time(),
            "action": action,
            "actor": actor,
            "details": details or {},
        }
        self._entries.append(entry)
        logger.info(f"Audit: {action}")
        return entry

    def get_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._entries[-limit:])


audit_log = AuditLog()
