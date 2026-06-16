"""Worker tests: the real domain task runs with no broker."""

from issue_pr_agent import worker
from issue_pr_agent.store import InMemoryStore


class TestWorker:
    def test_celery_app_importable_without_broker(self):
        assert worker.celery_app is not None
        assert "issue_pr_agent.process_issue" in worker.celery_app.tasks

    def test_run_issue_pipeline_sync(self):
        store = InMemoryStore()
        run = worker.run_issue_pipeline(101, "owner/repo", store=store)
        assert run["status"] == "awaiting_approval"
        assert run["tests_passed"] is True
        # The run is persisted in the provided store.
        assert store.get_run(run["id"]) is not None

    def test_task_run_directly(self):
        # Call the task body directly (no broker dispatch) — provisions its own
        # store via the availability probe (in-memory offline).
        result = worker.process_issue_task.run(101, "owner/repo")
        assert result["status"] in ("awaiting_approval", "completed")

    def test_build_agent_uses_mock_by_default(self):
        store = InMemoryStore()
        agent = worker.build_agent(store, ".")
        from issue_pr_agent.github import MockGitHubClient

        assert isinstance(agent.github, MockGitHubClient)
