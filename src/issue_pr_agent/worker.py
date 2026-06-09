from shared_core.tasks import create_celery_app

from .config import AppConfig

config = AppConfig()
celery_app = create_celery_app(
    config.APP_NAME,
    broker_url=config.CELERY_BROKER_URL,
    backend_url=config.CELERY_RESULT_BACKEND,
)


@celery_app.task
def process_issue_task(issue_id: int, repo: str) -> dict:
    """Async task: Fetch issue, plan, edit, test, and create PR."""
    from .editor import CodeEditor
    from .github import GitHubClient
    from .planner import CodePlanner
    from .test_runner import LocalTestRunner

    gh = GitHubClient()
    planner = CodePlanner()
    editor = CodeEditor()
    test_runner = LocalTestRunner()

    issue = gh.get_issue(issue_id, repo)
    plan = planner.plan_changes(issue)
    editor.apply_fix("src/calculator.py")
    tests_pass = test_runner.run_tests()
    pr_url = gh.create_pull_request(
        repo, f"fix: {issue['title']}", plan, draft=True
    )

    return {
        "issue_id": issue_id,
        "plan": plan,
        "tests_pass": tests_pass,
        "pr_url": pr_url,
    }
