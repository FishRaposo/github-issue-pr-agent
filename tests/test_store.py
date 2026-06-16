"""Store tests: in-memory and DB-backed (SQLite) parity."""

import pytest
from shared_core.testing import MockDatabase

# Import models before MockDatabase so their tables are registered on
# Base.metadata and created by MockDatabase's create_all().
from issue_pr_agent import models  # noqa: F401
from issue_pr_agent.store import DatabaseStore, InMemoryStore


@pytest.fixture
def db_store():
    mock = MockDatabase()
    return DatabaseStore(mock.get_session)


def _exercise(store):
    run = store.create_run(issue_id=101, repo="owner/repo")
    assert run["status"] == "pending"
    rid = run["id"]

    updated = store.update_run(rid, status="planned", plan="do x")
    assert updated["status"] == "planned"
    assert updated["plan"] == "do x"

    store.update_run(rid, files_changed=["calculator.py"])
    fetched = store.get_run(rid)
    assert fetched["files_changed"] == ["calculator.py"]

    store.log_action("plan_generated", {"target": "calculator.py"}, run_id=rid)
    store.log_action("tests_run", {"passed": True}, run_id=rid)
    audit = store.get_audit(run_id=rid)
    assert [a["action"] for a in audit] == ["plan_generated", "tests_run"]
    assert audit[0]["details"]["target"] == "calculator.py"

    runs = store.list_runs()
    assert any(r["id"] == rid for r in runs)
    assert store.get_run("missing") is None
    assert store.update_run("missing", status="x") is None


class TestInMemoryStore:
    def test_full_lifecycle(self):
        _exercise(InMemoryStore())

    def test_audit_filter_by_run(self):
        store = InMemoryStore()
        r1 = store.create_run(1, "r")["id"]
        r2 = store.create_run(2, "r")["id"]
        store.log_action("a", run_id=r1)
        store.log_action("b", run_id=r2)
        assert len(store.get_audit(run_id=r1)) == 1
        assert len(store.get_audit()) == 2


class TestDatabaseStore:
    def test_full_lifecycle(self, db_store):
        _exercise(db_store)

    def test_persisted_run_roundtrip(self, db_store):
        run = db_store.create_run(7, "owner/x")
        loaded = db_store.get_run(run["id"])
        assert loaded["issue_id"] == 7
        assert loaded["repo"] == "owner/x"
