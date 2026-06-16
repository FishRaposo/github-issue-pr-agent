from shared_core.config import BaseAppConfig


class AppConfig(BaseAppConfig):
    """Project-specific configuration extending the shared core settings.

    Offline-first defaults: ``GITHUB_MODE`` is ``mock`` so the agent runs with no
    network and no token. Set ``GITHUB_MODE=real`` (and a ``GITHUB_TOKEN``) to hit
    the real GitHub REST API. The planner mirrors the same pattern via the
    presence of ``OPENAI_API_KEY`` / ``ANTHROPIC_API_KEY``.
    """

    APP_NAME: str = "github-issue-pr-agent"

    # GitHub client selection: "mock" (deterministic, offline) or "real" (REST API).
    GITHUB_MODE: str = "mock"
    GITHUB_API_URL: str = "https://api.github.com"

    # Planner model used when an API key is configured (else simulated).
    PLANNER_MODEL: str = "gpt-4o-mini"

    # Sandbox repository the agent is allowed to operate on. Defaults to the
    # bundled ``demo_repo`` so the demo and tests run with no external repo.
    SANDBOX_REPO_PATH: str = "demo_repo"

    # Comma-separated glob allowlist / blocklist for editable paths within the
    # sandbox. Anything not matching the allowlist (or matching the blocklist) is
    # rejected before any write occurs.
    ALLOWED_PATHS: str = "*.py,*.txt,*.md,*.yaml,*.yml,*.json,*.toml,*.cfg,*.ini"
    BLOCKED_PATHS: str = (
        ".github/**,.env,.env.*,Makefile,pyproject.toml,"
        "docker-compose.yml,requirements.txt,alembic.ini,**/secrets/**"
    )

    # Branches the agent must never commit to or push.
    PROTECTED_BRANCHES: str = "main,master"

    # When False, a PR can only be opened after an explicit approval call.
    AUTO_APPROVE: bool = False

    # Seconds to wait when probing the database before falling back to in-memory.
    DB_CONNECT_TIMEOUT: int = 2

    def allowed_globs(self) -> list[str]:
        """Return the allowlist as a list of glob patterns."""
        return [p.strip() for p in self.ALLOWED_PATHS.split(",") if p.strip()]

    def blocked_globs(self) -> list[str]:
        """Return the blocklist as a list of glob patterns."""
        return [p.strip() for p in self.BLOCKED_PATHS.split(",") if p.strip()]

    def protected_branches(self) -> set[str]:
        """Return the set of branches the agent may never write to."""
        return {b.strip() for b in self.PROTECTED_BRANCHES.split(",") if b.strip()}
