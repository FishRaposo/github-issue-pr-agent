"""GitHub access layer: a deterministic mock and a real REST client.

Config-selected via ``AppConfig.GITHUB_MODE``:

* ``mock`` (default, offline) — :class:`MockGitHubClient` returns deterministic
  issue data and a synthetic draft-PR URL. No network, no token.
* ``real`` — :class:`RealGitHubClient` reads issues, creates branches, and opens
  **draft** PRs against the GitHub REST API via
  ``shared_core.clients.BaseHTTPClient``. Used only when a token is configured.

Both clients implement the same surface (``get_issue``, ``create_branch``,
``create_pull_request``) so the rest of the agent is provider-agnostic.
"""

import asyncio
from typing import Optional, Protocol

from loguru import logger

# Deterministic issues used by the mock client and the demo. The agent is built
# and tested against these without any network.
_MOCK_ISSUES: dict[int, dict] = {
    101: {
        "id": 101,
        "title": "divide() crashes on division by zero",
        "body": (
            "Calling calculate('divide', 1, 0) raises ZeroDivisionError. "
            "Please make calculator.py return None (or raise a clean ValueError) "
            "instead of crashing."
        ),
        "labels": ["bug", "agent-ready"],
    },
    102: {
        "id": 102,
        "title": "Add a safe percentage helper",
        "body": "We need a percentage() function in calculator.py.",
        "labels": ["enhancement"],
    },
}


class GitHubClient(Protocol):
    """Shared surface implemented by both the mock and real clients."""

    def get_issue(self, issue_id: int, repo: str = "") -> dict: ...

    def create_branch(self, repo: str, branch: str, base: str = "main") -> bool: ...

    def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        branch: str = "",
        base: str = "main",
        draft: bool = True,
    ) -> str: ...


class MockGitHubClient:
    """Deterministic, offline GitHub client (the default)."""

    def __init__(self, token: Optional[str] = None, base_url: str = ""):
        self.token = token
        self.base_url = base_url

    def get_issue(self, issue_id: int, repo: str = "") -> dict:
        issue = _MOCK_ISSUES.get(issue_id)
        if issue is None:
            issue = {
                "id": issue_id,
                "title": "Fix bug in calculations",
                "body": "The divide operation crashes when dividing by zero.",
                "labels": ["bug"],
            }
        return dict(issue)

    def create_branch(self, repo: str, branch: str, base: str = "main") -> bool:
        logger.info(f"[mock] create branch {branch} from {base} on {repo}")
        return True

    def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        branch: str = "",
        base: str = "main",
        draft: bool = True,
    ) -> str:
        branch = branch or f"agent/fix-{title.lower().replace(' ', '-')[:40]}"
        kind = "draft" if draft else "ready"
        url = f"https://github.com/{repo or 'owner/repo'}/pull/42"
        logger.info(f"[mock] opened {kind} PR {url} (head={branch}, base={base})")
        return url


class RealGitHubClient:
    """Real GitHub REST client built on ``shared_core.clients.BaseHTTPClient``."""

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
    ):
        self.token = token
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _client(self):
        from shared_core.clients import BaseHTTPClient

        return BaseHTTPClient(base_url=self.base_url)

    def get_issue(self, issue_id: int, repo: str = "") -> dict:
        async def _run() -> dict:
            client = await self._client()
            try:
                resp = await client.get(
                    f"/repos/{repo}/issues/{issue_id}", headers=self._headers()
                )
                data = resp.json()
                return {
                    "id": data["number"],
                    "title": data["title"],
                    "body": data.get("body") or "",
                    "labels": [label["name"] for label in data.get("labels", [])],
                }
            finally:
                await client.close()

        try:
            return asyncio.run(_run())
        except Exception as exc:
            logger.error(f"GitHub get_issue failed: {exc}")
            raise

    def create_branch(self, repo: str, branch: str, base: str = "main") -> bool:
        async def _run() -> bool:
            client = await self._client()
            try:
                ref = await client.get(
                    f"/repos/{repo}/git/ref/heads/{base}", headers=self._headers()
                )
                sha = ref.json()["object"]["sha"]
                await client.post(
                    f"/repos/{repo}/git/refs",
                    headers=self._headers(),
                    json={"ref": f"refs/heads/{branch}", "sha": sha},
                )
                return True
            finally:
                await client.close()

        try:
            return asyncio.run(_run())
        except Exception as exc:
            logger.error(f"GitHub create_branch failed: {exc}")
            return False

    def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        branch: str = "",
        base: str = "main",
        draft: bool = True,
    ) -> str:
        async def _run() -> str:
            client = await self._client()
            try:
                resp = await client.post(
                    f"/repos/{repo}/pulls",
                    headers=self._headers(),
                    json={
                        "title": title,
                        "body": body,
                        "head": branch,
                        "base": base,
                        "draft": draft,
                    },
                )
                return resp.json().get("html_url", "")
            finally:
                await client.close()

        try:
            return asyncio.run(_run())
        except Exception as exc:
            logger.error(f"GitHub create_pull_request failed: {exc}")
            raise


def build_github_client(
    mode: str = "mock",
    token: Optional[str] = None,
    base_url: str = "https://api.github.com",
) -> GitHubClient:
    """Return the configured client. Falls back to mock without a token."""
    if mode == "real" and token:
        logger.info("Using real GitHub REST client")
        return RealGitHubClient(token=token, base_url=base_url)
    if mode == "real" and not token:
        logger.warning("GITHUB_MODE=real but no token set — using mock client")
    return MockGitHubClient(token=token, base_url=base_url)
