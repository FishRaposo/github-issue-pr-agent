"""API tests for every endpoint (success + error), all offline."""

import pytest
from fastapi.testclient import TestClient

from issue_pr_agent import main as main_module
from issue_pr_agent.store import InMemoryStore


@pytest.fixture
def client(monkeypatch):
    """TestClient with a fresh in-memory store and no DB/broker.

    The lifespan probe is neutralised so startup never touches a real database.
    """
    store = InMemoryStore()
    monkeypatch.setattr(main_module, "store", store)
    monkeypatch.setattr(main_module, "db_manager", None)

    # Neutralise the DB probe used in lifespan.
    from issue_pr_agent import db as db_module

    monkeypatch.setattr(db_module, "check_db", lambda: False)
    monkeypatch.setattr(db_module, "db_available", False)

    with TestClient(main_module.app) as c:
        yield c, store


class TestHealth:
    def test_health_degraded_offline(self, client):
        c, _ = client
        resp = c.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["service"] == "github-issue-pr-agent"
        assert body["dependencies"]["database"] == "offline"


class TestProcess:
    def test_process_sync_completes(self, client):
        c, _ = client
        resp = c.post(
            "/issues/process",
            json={"issue_id": 101, "repo": "owner/repo", "sync": True},
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "completed"
        assert body["run"]["status"] == "awaiting_approval"
        assert body["run"]["tests_passed"] is True

    def test_process_async_falls_back_without_broker(self, client):
        c, _ = client
        # No broker running -> .delay() fails -> synchronous fallback.
        resp = c.post("/issues/process", json={"issue_id": 101, "repo": "owner/repo"})
        assert resp.status_code == 202
        assert resp.json()["status"] in ("completed", "queued")

    def test_process_validation_error(self, client):
        c, _ = client
        resp = c.post("/issues/process", json={"repo": "owner/repo"})
        assert resp.status_code == 422  # missing issue_id


class TestRuns:
    def test_list_runs_empty(self, client):
        c, _ = client
        resp = c.get("/runs")
        assert resp.status_code == 200
        assert resp.json()["runs"] == []

    def test_list_and_get_run(self, client):
        c, _ = client
        c.post(
            "/issues/process",
            json={"issue_id": 101, "repo": "owner/repo", "sync": True},
        )
        runs = c.get("/runs").json()["runs"]
        assert len(runs) == 1
        run_id = runs[0]["id"]
        detail = c.get(f"/runs/{run_id}")
        assert detail.status_code == 200
        assert detail.json()["id"] == run_id

    def test_get_run_not_found(self, client):
        c, _ = client
        resp = c.get("/runs/does-not-exist")
        assert resp.status_code == 404
        assert resp.json()["error"] == "NOT_FOUND"


class TestApprove:
    def test_approve_opens_pr(self, client):
        c, _ = client
        c.post(
            "/issues/process",
            json={"issue_id": 101, "repo": "owner/repo", "sync": True},
        )
        resp = c.post("/issues/101/approve")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "approved"
        assert body["run"]["pr_url"]
        assert body["run"]["status"] == "completed"

    def test_approve_by_run_id(self, client):
        c, _ = client
        c.post(
            "/issues/process",
            json={"issue_id": 101, "repo": "owner/repo", "sync": True},
        )
        run_id = c.get("/runs").json()["runs"][0]["id"]
        resp = c.post(f"/issues/101/approve?run_id={run_id}")
        assert resp.status_code == 200

    def test_approve_unknown_issue_404(self, client):
        c, _ = client
        resp = c.post("/issues/9999/approve")
        assert resp.status_code == 404

    def test_approve_already_completed_409(self, client):
        c, _ = client
        c.post(
            "/issues/process",
            json={"issue_id": 101, "repo": "owner/repo", "sync": True},
        )
        c.post("/issues/101/approve")  # first approval -> completed
        resp = c.post("/issues/101/approve")  # second -> conflict
        assert resp.status_code == 409


class TestAudit:
    def test_audit_after_run(self, client):
        c, _ = client
        c.post(
            "/issues/process",
            json={"issue_id": 101, "repo": "owner/repo", "sync": True},
        )
        resp = c.get("/audit")
        assert resp.status_code == 200
        actions = [a["action"] for a in resp.json()["audit"]]
        assert "run_started" in actions
        assert "tests_run" in actions

    def test_audit_filtered_by_run(self, client):
        c, _ = client
        c.post(
            "/issues/process",
            json={"issue_id": 101, "repo": "owner/repo", "sync": True},
        )
        run_id = c.get("/runs").json()["runs"][0]["id"]
        resp = c.get(f"/audit?run_id={run_id}")
        assert resp.status_code == 200
        assert all(a["run_id"] == run_id for a in resp.json()["audit"])

    def test_audit_empty_initially(self, client):
        c, _ = client
        assert c.get("/audit").json()["audit"] == []
