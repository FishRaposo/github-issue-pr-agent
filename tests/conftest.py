"""Shared pytest fixtures.

Everything here runs with NO database, NO broker, and NO API keys. Fixtures
provision disposable sandboxes from the bundled demo repo and an in-memory store.
"""

import pytest

from issue_pr_agent.sandbox import cleanup_sandbox, provision_sandbox
from issue_pr_agent.store import InMemoryStore


@pytest.fixture
def memory_store():
    return InMemoryStore()


@pytest.fixture
def sandbox():
    """A disposable copy of demo_repo with git initialised."""
    path = provision_sandbox(init_git=True)
    yield path
    cleanup_sandbox(path)


@pytest.fixture
def sandbox_no_git():
    path = provision_sandbox(init_git=False)
    yield path
    cleanup_sandbox(path)


@pytest.fixture
def sample_issue():
    return {
        "id": 101,
        "title": "divide() crashes on division by zero",
        "body": "calculate('divide', 1, 0) raises ZeroDivisionError in calculator.py",
        "labels": ["bug"],
    }
