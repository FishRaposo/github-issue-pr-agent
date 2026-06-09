from unittest.mock import MagicMock, patch

import pytest
from issue_pr_agent.github import GitHubClient


class TestGitHubClient:
    def test_get_issue_returns_data(self):
        client = GitHubClient(token="fake-token")
        result = client.get_issue(42, "owner/repo")
        assert isinstance(result, dict)
        assert "title" in result
        assert "id" in result

    def test_create_pull_request_returns_url(self):
        client = GitHubClient(token="fake-token")
        result = client.create_pull_request(
            "owner/repo",
            "Fix bug",
            "Changes description",
        )
        assert isinstance(result, str)
        assert "pull" in result.lower()

    def test_get_issue_mock_fallback(self):
        client = GitHubClient(token="fake-token", base_url="https://invalid.example")
        result = client.get_issue(1, "owner/repo")
        assert isinstance(result, dict)
        assert "title" in result

    def test_mock_issue_has_labels(self):
        client = GitHubClient()
        result = client._mock_issue(10)
        assert "labels" in result
        assert result["id"] == 10
