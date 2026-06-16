"""Run + audit persistence with a uniform store interface.

Two backends implement the same surface so the API, worker, and demo are
agnostic to whether a database is present:

* :class:`InMemoryStore` — the offline-first default; holds runs and audit
  entries in process memory. Used by tests and the demo with NO database.
* :class:`DatabaseStore` — persists to PostgreSQL (or any SQLAlchemy URL) via a
  session factory, so runs and the audit trail survive restarts.

A "run" is a plain dict snapshot (stable JSON shape the API returns directly);
an "audit entry" is likewise a dict. Both stores return the same shapes.
"""

import json
import time
import uuid
from typing import Any, Optional

from loguru import logger


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> float:
    return time.time()


class InMemoryStore:
    """In-process store for runs and audit entries (no database required)."""

    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}
        self._audit: list[dict[str, Any]] = []

    # ---- runs ---------------------------------------------------------------
    def create_run(self, issue_id: int, repo: str) -> dict[str, Any]:
        run_id = _new_id()
        run = {
            "id": run_id,
            "issue_id": issue_id,
            "repo": repo,
            "status": "pending",
            "plan": None,
            "branch": None,
            "files_changed": [],
            "tests_passed": None,
            "test_output": None,
            "approved": False,
            "pr_url": None,
            "error": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self._runs[run_id] = run
        return dict(run)

    def update_run(self, run_id: str, **fields: Any) -> Optional[dict[str, Any]]:
        run = self._runs.get(run_id)
        if run is None:
            return None
        run.update(fields)
        run["updated_at"] = _now()
        return dict(run)

    def get_run(self, run_id: str) -> Optional[dict[str, Any]]:
        run = self._runs.get(run_id)
        return dict(run) if run else None

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        runs = sorted(self._runs.values(), key=lambda r: r["created_at"], reverse=True)
        return [dict(r) for r in runs[:limit]]

    # ---- audit --------------------------------------------------------------
    def log_action(
        self,
        action: str,
        details: Optional[dict[str, Any]] = None,
        actor: str = "agent",
        run_id: Optional[str] = None,
    ) -> dict[str, Any]:
        entry = {
            "id": _new_id(),
            "run_id": run_id,
            "action": action,
            "actor": actor,
            "details": details or {},
            "timestamp": _now(),
        }
        self._audit.append(entry)
        logger.info(f"Audit: {action} (run={run_id})")
        return dict(entry)

    def get_audit(
        self, limit: int = 100, run_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        entries = self._audit
        if run_id is not None:
            entries = [e for e in entries if e["run_id"] == run_id]
        return [dict(e) for e in entries[-limit:]]


class DatabaseStore:
    """SQLAlchemy-backed store mirroring :class:`InMemoryStore`."""

    def __init__(self, session_factory: Any) -> None:
        # session_factory() yields a Session (DatabaseManager.get_session generator).
        self.session_factory = session_factory

    def _session(self):
        return next(self.session_factory())

    @staticmethod
    def _run_to_dict(row: Any) -> dict[str, Any]:
        return {
            "id": row.id,
            "issue_id": row.issue_id,
            "repo": row.repo,
            "status": row.status,
            "plan": row.plan,
            "branch": row.branch,
            "files_changed": json.loads(row.files_changed) if row.files_changed else [],
            "tests_passed": row.tests_passed,
            "test_output": row.test_output,
            "approved": row.approved,
            "pr_url": row.pr_url,
            "error": row.error,
            "created_at": row.created_at.timestamp() if row.created_at else None,
            "updated_at": row.updated_at.timestamp() if row.updated_at else None,
        }

    # ---- runs ---------------------------------------------------------------
    def create_run(self, issue_id: int, repo: str) -> dict[str, Any]:
        from .models import AgentRun

        session = self._session()
        try:
            run = AgentRun(
                issue_id=issue_id,
                repo=repo,
                status="pending",
                approved=False,
                files_changed=json.dumps([]),
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            return self._run_to_dict(run)
        finally:
            session.close()

    def update_run(self, run_id: str, **fields: Any) -> Optional[dict[str, Any]]:
        from .models import AgentRun

        session = self._session()
        try:
            run = session.get(AgentRun, run_id)
            if run is None:
                return None
            if "files_changed" in fields and isinstance(fields["files_changed"], list):
                fields["files_changed"] = json.dumps(fields["files_changed"])
            for key, value in fields.items():
                if hasattr(run, key):
                    setattr(run, key, value)
            session.add(run)
            session.commit()
            session.refresh(run)
            return self._run_to_dict(run)
        finally:
            session.close()

    def get_run(self, run_id: str) -> Optional[dict[str, Any]]:
        from .models import AgentRun

        session = self._session()
        try:
            run = session.get(AgentRun, run_id)
            return self._run_to_dict(run) if run else None
        finally:
            session.close()

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        from .models import AgentRun

        session = self._session()
        try:
            rows = (
                session.query(AgentRun)
                .order_by(AgentRun.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._run_to_dict(r) for r in rows]
        finally:
            session.close()

    # ---- audit --------------------------------------------------------------
    def log_action(
        self,
        action: str,
        details: Optional[dict[str, Any]] = None,
        actor: str = "agent",
        run_id: Optional[str] = None,
    ) -> dict[str, Any]:
        from .models import AuditEntry

        session = self._session()
        try:
            entry = AuditEntry(
                run_id=run_id,
                action=action,
                actor=actor,
                details=json.dumps(details or {}),
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)
            logger.info(f"Audit: {action} (run={run_id})")
            return {
                "id": entry.id,
                "run_id": entry.run_id,
                "action": entry.action,
                "actor": entry.actor,
                "details": details or {},
                "timestamp": entry.created_at.timestamp()
                if entry.created_at
                else _now(),
            }
        finally:
            session.close()

    def get_audit(
        self, limit: int = 100, run_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        from .models import AuditEntry

        session = self._session()
        try:
            query = session.query(AuditEntry)
            if run_id is not None:
                query = query.filter(AuditEntry.run_id == run_id)
            rows = query.order_by(AuditEntry.created_at.asc()).limit(limit).all()
            return [
                {
                    "id": r.id,
                    "run_id": r.run_id,
                    "action": r.action,
                    "actor": r.actor,
                    "details": json.loads(r.details) if r.details else {},
                    "timestamp": r.created_at.timestamp() if r.created_at else None,
                }
                for r in rows
            ]
        finally:
            session.close()
