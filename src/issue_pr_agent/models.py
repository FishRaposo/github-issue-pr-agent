"""SQLAlchemy models for run tracking and the audit trail.

Two tables back the agent's persistence layer:

* ``agent_runs`` — one row per issue-processing run, holding its lifecycle state
  (``pending`` -> ``planned`` -> ``awaiting_approval`` -> ``approved`` ->
  ``completed`` / ``failed``), the generated plan, test outcome, and PR URL.
* ``audit_entries`` — an append-only log of every action the agent takes, linked
  back to its run so a reviewer can reconstruct exactly what happened.
"""

from shared_core.database import Base, TimestampMixin, UUIDMixin
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text


class AgentRun(Base, UUIDMixin, TimestampMixin):
    """A single issue-to-PR processing run."""

    __tablename__ = "agent_runs"

    issue_id = Column(Integer, nullable=False, index=True)
    repo = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="pending", index=True)
    plan = Column(Text, nullable=True)
    branch = Column(String(255), nullable=True)
    files_changed = Column(Text, nullable=True)  # JSON-encoded list of paths
    tests_passed = Column(Boolean, nullable=True)
    test_output = Column(Text, nullable=True)
    approved = Column(Boolean, nullable=False, default=False)
    pr_url = Column(String(500), nullable=True)
    error = Column(String(1000), nullable=True)


class AuditEntry(Base, UUIDMixin, TimestampMixin):
    """An append-only record of one agent action."""

    __tablename__ = "audit_entries"

    run_id = Column(String(36), ForeignKey("agent_runs.id"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    actor = Column(String(64), nullable=False, default="agent")
    details = Column(Text, nullable=True)  # JSON-encoded dict
