"""FastAPI application for the GitHub Issue-to-PR agent.

Offline-first: boots and serves with no database (in-memory store), no broker,
and no API keys. When a database is reachable, runs and the audit trail persist
to PostgreSQL via the ``db_available`` probe. When Celery has a broker, issue
processing is dispatched asynchronously; otherwise the API runs the pipeline
synchronously so the demo and tests need no broker.

Exposes everything a dashboard would need: submit/approve runs, and read the
audit trail, run list, and individual run detail.
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from shared_core.errors import (
    BaseApplicationError,
    NotFoundError,
    application_error_handler,
)
from shared_core.health import check_health
from shared_core.logging import RequestLoggingMiddleware, setup_logging
from shared_core.redis import RedisManager

from . import db as db_module
from .config import AppConfig
from .github import build_github_client
from .store import InMemoryStore

config = AppConfig()
setup_logging(level=config.LOG_LEVEL, service_name=config.APP_NAME)

# In-memory fallback store; replaced by a DB-backed store on startup when the
# database is reachable. Tests patch this attribute directly.
store: object = InMemoryStore()

# Built lazily so importing the app never requires a DB driver. Tests patch this.
db_manager: object = None
redis_manager = RedisManager(config.REDIS_URL)


def _api_keys() -> dict:
    keys = {}
    if config.OPENAI_API_KEY:
        keys["openai"] = config.OPENAI_API_KEY.get_secret_value()
    if config.ANTHROPIC_API_KEY:
        keys["anthropic"] = config.ANTHROPIC_API_KEY.get_secret_value()
    return keys


def _github_client():
    token = config.GITHUB_TOKEN.get_secret_value() if config.GITHUB_TOKEN else None
    return build_github_client(
        mode=config.GITHUB_MODE, token=token, base_url=config.GITHUB_API_URL
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Probe the database on startup and select the persistence backend."""
    global store, db_manager
    db_module.check_db()
    if db_module.db_available:
        db_manager = db_module.db_manager
        store = db_module.build_store()
    yield


app = FastAPI(
    title=config.APP_NAME,
    version="1.0.0",
    description=(
        "Autonomous agent that reads GitHub issues, plans a fix, edits code in a "
        "sandbox under strict safety guards, runs tests, and — after human "
        "approval — opens a draft PR."
    ),
    lifespan=lifespan,
)

app.add_exception_handler(BaseApplicationError, application_error_handler)
app.add_middleware(RequestLoggingMiddleware)


# ---- request models --------------------------------------------------------
class IssueRequest(BaseModel):
    """Payload for submitting an issue to the agent."""

    issue_id: int = Field(..., description="GitHub issue number")
    repo: str = Field(default="owner/repo", description="owner/name slug")
    mocked_plan: Optional[str] = Field(
        default=None, description="Force a deterministic offline plan hint"
    )
    sync: bool = Field(
        default=False,
        description="Run synchronously instead of dispatching to Celery",
    )


# ---- endpoints -------------------------------------------------------------
@app.post("/issues/process", status_code=202)
def process_issue(req: IssueRequest):
    """Submit an issue for processing.

    Dispatches to the Celery worker when a broker is reachable; otherwise (or
    when ``sync=true``) runs the pipeline inline and returns the run snapshot.
    The pipeline stops at ``awaiting_approval`` — no PR is opened until approval.
    """
    from .worker import process_issue_task, run_issue_pipeline

    if req.sync:
        run = run_issue_pipeline(
            req.issue_id, req.repo, store=store, mocked_plan=req.mocked_plan
        )
        return {"status": "completed", "run": run}

    try:
        task = process_issue_task.delay(req.issue_id, req.repo, req.mocked_plan)
        return {"status": "queued", "task_id": task.id}
    except Exception:
        # No broker available — fall back to a synchronous run.
        run = run_issue_pipeline(
            req.issue_id, req.repo, store=store, mocked_plan=req.mocked_plan
        )
        return {"status": "completed", "run": run}


@app.post("/issues/{issue_id}/approve")
def approve_issue(issue_id: int, run_id: Optional[str] = Query(default=None)):
    """Approve a run awaiting approval and open a DRAFT pull request.

    Resolves the target run by ``run_id`` (preferred) or the most recent run for
    ``issue_id``. Returns 404 if no matching run, 409 if it is not awaiting
    approval.
    """
    from .agent import IssuePRAgent

    target = None
    if run_id:
        target = store.get_run(run_id)
    else:
        for run in store.list_runs(limit=200):
            if run["issue_id"] == issue_id:
                target = run
                break
    if target is None:
        raise NotFoundError(f"No run found for issue {issue_id}")

    agent = IssuePRAgent(
        store=store,
        github_client=_github_client(),
        sandbox_path=config.SANDBOX_REPO_PATH,
        api_keys=_api_keys(),
        planner_model=config.PLANNER_MODEL,
        protected_branches=config.protected_branches(),
        allowed_globs=config.allowed_globs(),
        blocked_globs=config.blocked_globs(),
    )
    try:
        run = agent.approve_and_open_pr(target["id"], actor="human")
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "approved", "run": run}


@app.get("/runs")
def list_runs(limit: int = Query(default=50, ge=1, le=500)):
    """List recent agent runs (most recent first)."""
    return {"runs": store.list_runs(limit)}


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    """Return a single run by id, including its plan and test outcome."""
    run = store.get_run(run_id)
    if run is None:
        raise NotFoundError(f"Run {run_id} not found")
    return run


@app.get("/audit")
def get_audit(
    limit: int = Query(default=100, ge=1, le=1000),
    run_id: Optional[str] = Query(default=None),
):
    """Return the audit trail, optionally filtered by run."""
    return {"audit": store.get_audit(limit=limit, run_id=run_id)}


@app.get("/health")
def health_check():
    """Service health, probing database and Redis connectivity.

    In offline mode (no DB manager) reports the database as offline and degraded
    rather than failing — the service still serves runs from the in-memory store.
    """
    if db_manager is None:
        try:
            redis_healthy = redis_manager.ping()
        except Exception:
            redis_healthy = False
        return {
            "status": "degraded",
            "service": config.APP_NAME,
            "dependencies": {
                "database": "offline",
                "redis": "online" if redis_healthy else "offline",
            },
        }
    return check_health(db_manager, redis_manager, config.APP_NAME)


def main():
    """Run the development server."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
