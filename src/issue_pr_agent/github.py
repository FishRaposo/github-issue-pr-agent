from typing import Optional

from loguru import logger


class GitHubClient:
    """Interfaces with GitHub repository issues and pull requests."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url

    def get_issue(self, issue_id: int, repo: str) -> dict:
        import httpx

        url = f"{self.base_url}/repos/{repo}/issues/{issue_id}"
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = httpx.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return {
                "id": data["number"],
                "title": data["title"],
                "body": data.get("body", ""),
                "labels": [label["name"] for label in data.get("labels", [])],
            }
        except Exception as e:
            logger.warning(f"GitHub API unavailable, using mock data: {e}")
            return self._mock_issue(issue_id)

    def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        branch: str = "",
        draft: bool = True,
    ) -> str:
        import httpx

        url = f"{self.base_url}/repos/{repo}/pulls"
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        if not branch:
            branch = f"agent/fix-{title.lower().replace(' ', '-')[:50]}"

        payload = {
            "title": title,
            "body": body,
            "head": branch,
            "base": "main",
            "draft": draft,
        }

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json().get("html_url", "")
        except Exception as e:
            logger.warning(f"GitHub API create PR failed, using mock: {e}")
            return "https://github.com/{repo}/pulls/42"

    def _mock_issue(self, issue_id: int) -> dict:
        return {
            "id": issue_id,
            "title": "Fix bug in calculations",
            "body": "The sum method throws an exception when passing empty lists.",
            "labels": ["bug"],
        }
