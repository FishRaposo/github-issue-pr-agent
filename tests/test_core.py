from unittest.mock import MagicMock, patch


def test_health_endpoint():
    mock_db = MagicMock()
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True

    with (
        patch("issue_pr_agent.main.db_manager", mock_db),
        patch("issue_pr_agent.main.redis_manager", mock_redis),
        patch("issue_pr_agent.main.editor", MagicMock()),
    ):
        from fastapi.testclient import TestClient

        from issue_pr_agent.main import app

        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["service"] == "github-issue-pr-agent"
            assert "dependencies" in response.json()
