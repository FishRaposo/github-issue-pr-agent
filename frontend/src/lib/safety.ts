// The agent's safety model, surfaced in the UI. Values mirror the backend
// defaults in config.py (ALLOWED_PATHS / BLOCKED_PATHS / PROTECTED_BRANCHES /
// AUTO_APPROVE) so the dashboard accurately reflects what the agent enforces.

export interface SafetyControl {
  title: string;
  description: string;
}

export const ALLOWED_GLOBS = [
  "*.py",
  "*.txt",
  "*.md",
  "*.yaml",
  "*.yml",
  "*.json",
  "*.toml",
  "*.cfg",
  "*.ini",
];

export const BLOCKED_GLOBS = [
  ".github/**",
  ".env",
  ".env.*",
  "Makefile",
  "pyproject.toml",
  "docker-compose.yml",
  "requirements.txt",
  "alembic.ini",
  "**/secrets/**",
];

export const PROTECTED_BRANCHES = ["main", "master"];

export const SAFETY_CONTROLS: SafetyControl[] = [
  {
    title: "Allowlisted paths only",
    description:
      "Edits are rejected before any write unless the path matches the allowlist and avoids the blocklist (CI config, secrets, build files).",
  },
  {
    title: "No-main guard",
    description:
      "The agent always branches off the protected default branch first. It never commits to or pushes main / master.",
  },
  {
    title: "Tests must pass",
    description:
      "A real pytest subprocess must go green in the sandbox before a run can reach the approval gate.",
  },
  {
    title: "Approval before PR",
    description:
      "No pull request is opened until a human explicitly approves. The PR is always opened as a draft.",
  },
];
