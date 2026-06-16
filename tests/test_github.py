"""GitHub client tests: mock determinism + real-client selection."""

from issue_pr_agent.github import (
    MockGitHubClient,
    RealGitHubClient,
    build_github_client,
)


class TestMockGitHubClient:
    def test_get_known_issue(self):
        issue = MockGitHubClient().get_issue(101, "owner/repo")
        assert issue["id"] == 101
        assert "divide" in issue["title"].lower()
        assert "labels" in issue

    def test_get_unknown_issue_default(self):
        issue = MockGitHubClient().get_issue(9999, "owner/repo")
        assert issue["id"] == 9999
        assert "title" in issue

    def test_deterministic(self):
        a = MockGitHubClient().get_issue(101, "r")
        b = MockGitHubClient().get_issue(101, "r")
        assert a == b

    def test_create_branch(self):
        assert MockGitHubClient().create_branch("owner/repo", "agent/fix-1") is True

    def test_create_draft_pr_url(self):
        url = MockGitHubClient().create_pull_request(
            "owner/repo", "fix", "body", branch="agent/fix-1", draft=True
        )
        assert "pull" in url and "owner/repo" in url


class TestBuildClient:
    def test_default_is_mock(self):
        assert isinstance(build_github_client(), MockGitHubClient)

    def test_real_without_token_falls_back_to_mock(self):
        client = build_github_client(mode="real", token=None)
        assert isinstance(client, MockGitHubClient)

    def test_real_with_token(self):
        client = build_github_client(mode="real", token="ghp_test")
        assert isinstance(client, RealGitHubClient)


class TestRealGitHubClient:
    def test_headers_include_auth(self):
        client = RealGitHubClient(token="ghp_test")
        headers = client._headers()
        assert headers["Authorization"] == "Bearer ghp_test"
        assert "X-GitHub-Api-Version" in headers

    def test_headers_without_token(self):
        headers = (
            RealGitHubClient().headers
            if hasattr(RealGitHubClient(), "headers")
            else RealGitHubClient()._headers()
        )
        assert "Authorization" not in headers
