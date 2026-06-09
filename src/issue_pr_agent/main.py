from fastapi import FastAPI
from pydantic import BaseModel
from shared_core.database import DatabaseManager
from shared_core.errors import BaseApplicationError, application_error_handler
from shared_core.health import check_health
from shared_core.logging import setup_logging
from shared_core.redis import RedisManager

from .audit import audit_log
from .config import AppConfig
from .editor import CodeEditor
from .git_ops import git_ops
from .github import GitHubClient
from .planner import CodePlanner
from .test_runner import LocalTestRunner
from .worker import process_issue_task

config = AppConfig()
setup_logging(level=config.LOG_LEVEL, service_name=config.APP_NAME)

app = FastAPI(title=config.APP_NAME, version="0.1.0")
db_manager = DatabaseManager(
    config.DATABASE_URL,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_timeout=config.DB_POOL_TIMEOUT,
)
redis_manager = RedisManager(config.REDIS_URL)

app.add_exception_handler(BaseApplicationError, application_error_handler)

gh_client = GitHubClient(token=config.GITHUB_TOKEN)
planner = CodePlanner()
editor = CodeEditor()
test_runner = LocalTestRunner()


class IssueRequest(BaseModel):
    issue_id: int
    repo: str = "owner/repo"


@app.post("/issues/process")
def process_issue(req: IssueRequest):
    task = process_issue_task.delay(req.issue_id, req.repo)
    return {"task_id": task.id, "status": "queued"}


@app.post("/issues/process/sync")
def process_issue_sync(req: IssueRequest):
    audit_log.log_action("process_started", {"issue_id": req.issue_id, "repo": req.repo})
    issue = gh_client.get_issue(req.issue_id, req.repo)
    audit_log.log_action("issue_fetched", {"title": issue["title"]})
    plan = planner.plan_changes(issue)
    audit_log.log_action("plan_generated", {"plan_preview": plan[:100]})

    if git_ops.is_main_branch():
        branch_name = f"agent/fix-{req.issue_id}"
        git_ops.create_branch(branch_name)

    editor.apply_fix("demo_repo/calculator.py")
    audit_log.log_action("fix_applied", {"file": "demo_repo/calculator.py"})
    test_result = test_runner.run_tests()
    audit_log.log_action("tests_run", {"passed": test_result["passed"]})

    pr_url = ""
    if test_result["passed"]:
        pr_url = gh_client.create_pull_request(
            req.repo, f"fix: {issue['title']}", plan, draft=True
        )
        audit_log.log_action("pr_created", {"pr_url": pr_url})

    return {
        "issue": issue,
        "plan": plan,
        "tests_pass": test_result["passed"],
        "pr_url": pr_url,
    }


@app.post("/issues/{issue_id}/approve")
def approve_issue(issue_id: int):
    return {
        "status": "approved",
        "issue_id": issue_id,
        "message": "Human approval granted for agent action",
    }


@app.get("/audit")
def get_audit_logs(limit: int = 50):
    return {"logs": audit_log.get_logs(limit)}


@app.get("/health")
def health_check():
    return check_health(db_manager, redis_manager, config.APP_NAME)
