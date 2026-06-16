"""Celery worker with the real issue-processing domain task.

Built via ``shared_core.tasks.create_celery_app`` and importable without a
running broker (the broker URL is only contacted when a worker actually starts
or a task is dispatched). The task provisions a disposable sandbox, runs the
:class:`~.agent.IssuePRAgent` pipeline, and persists the run + audit trail to the
active store (DB-backed when available, else in-memory).
"""

from typing import Any, Optional

from shared_core.tasks import create_celery_app

from .config import AppConfig

config = AppConfig()
celery_app = create_celery_app(
    config.APP_NAME,
    broker_url=config.CELERY_BROKER_URL,
    backend_url=config.CELERY_RESULT_BACKEND,
)


def _resolve_store():
    """Return the active store: DB-backed when available, else in-memory."""
    from . import db as db_module

    db_module.check_db()
    return db_module.build_store()


def build_agent(store: Any, sandbox_path: str):
    """Construct an :class:`IssuePRAgent` wired from config + a store."""
    from .agent import IssuePRAgent
    from .github import build_github_client

    api_keys = {}
    if config.OPENAI_API_KEY:
        api_keys["openai"] = config.OPENAI_API_KEY.get_secret_value()
    if config.ANTHROPIC_API_KEY:
        api_keys["anthropic"] = config.ANTHROPIC_API_KEY.get_secret_value()

    token = config.GITHUB_TOKEN.get_secret_value() if config.GITHUB_TOKEN else None
    github_client = build_github_client(
        mode=config.GITHUB_MODE, token=token, base_url=config.GITHUB_API_URL
    )

    return IssuePRAgent(
        store=store,
        github_client=github_client,
        sandbox_path=sandbox_path,
        api_keys=api_keys,
        planner_model=config.PLANNER_MODEL,
        protected_branches=config.protected_branches(),
        allowed_globs=config.allowed_globs(),
        blocked_globs=config.blocked_globs(),
        auto_approve=config.AUTO_APPROVE,
    )


def run_issue_pipeline(
    issue_id: int,
    repo: str,
    store: Any = None,
    mocked_plan: Optional[str] = None,
) -> dict[str, Any]:
    """Synchronous core of the issue task (also called directly by the API/tests).

    Provisions a fresh sandbox from the bundled demo repo, runs the pipeline, and
    returns the resulting run snapshot. Cleans up the sandbox afterwards.
    """
    from .sandbox import cleanup_sandbox, provision_sandbox

    store = store or _resolve_store()
    sandbox_path = provision_sandbox()
    try:
        agent = build_agent(store, sandbox_path)
        return agent.process_issue(issue_id, repo, mocked_plan=mocked_plan)
    finally:
        cleanup_sandbox(sandbox_path)


@celery_app.task(name="issue_pr_agent.process_issue")
def process_issue_task(
    issue_id: int, repo: str, mocked_plan: Optional[str] = None
) -> dict[str, Any]:
    """Async task: run the full issue-to-PR pipeline up to the approval gate."""
    return run_issue_pipeline(issue_id, repo, mocked_plan=mocked_plan)
