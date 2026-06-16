"""DB availability probe + store selection tests (offline behaviour)."""

from issue_pr_agent import db as db_module
from issue_pr_agent import models  # noqa: F401  (register tables on Base.metadata)
from issue_pr_agent.store import DatabaseStore, InMemoryStore


class TestDbProbe:
    def test_unreachable_db_falls_back(self, monkeypatch):
        # Point at an unreachable Postgres; probe must fail fast and return False.
        monkeypatch.setattr(
            db_module.config,
            "DATABASE_URL",
            "postgresql+psycopg://x:y@127.0.0.1:1/none",
        )
        monkeypatch.setattr(db_module, "db_manager", None)
        monkeypatch.setattr(db_module, "db_available", False)
        assert db_module.check_db() is False
        assert db_module.db_available is False

    def test_build_store_in_memory_when_unavailable(self, monkeypatch):
        monkeypatch.setattr(db_module, "db_available", False)
        store = db_module.build_store()
        assert isinstance(store, InMemoryStore)

    def test_build_store_db_when_available(self, monkeypatch):
        from shared_core.testing import MockDatabase

        mock = MockDatabase()

        class _Manager:
            def get_session(self):
                return mock.get_session()

        monkeypatch.setattr(db_module, "db_available", True)
        monkeypatch.setattr(db_module, "db_manager", _Manager())
        store = db_module.build_store()
        assert isinstance(store, DatabaseStore)

    def test_sqlite_db_probe_succeeds(self, monkeypatch):
        # An in-memory SQLite URL is reachable and exercises the success path.
        monkeypatch.setattr(db_module.config, "DATABASE_URL", "sqlite:///:memory:")
        monkeypatch.setattr(db_module, "db_manager", None)
        monkeypatch.setattr(db_module, "db_available", False)
        assert db_module.check_db() is True
