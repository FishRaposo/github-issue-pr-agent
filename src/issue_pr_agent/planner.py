"""Issue -> implementation plan generation (sim/real).

Mirrors the offline-first / real-when-keyed pattern: a ``mocked_response``
short-circuits to a deterministic simulated plan (the default for tests and the
demo — no network, no keys), otherwise the real provider path runs via
``shared_core.llm.LLMClientFactory`` with a graceful fallback to simulation when
the SDK is missing or no API key is configured.

The plan is a structured :class:`FixPlan` so downstream components (editor,
test_runner) act on a stable, machine-checkable contract rather than free text.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger


@dataclass
class FixPlan:
    """A structured, machine-actionable implementation plan."""

    summary: str
    target_file: str
    steps: list[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "target_file": self.target_file,
            "steps": self.steps,
            "rationale": self.rationale,
        }

    def to_text(self) -> str:
        lines = [f"Plan: {self.summary}", f"Target file: {self.target_file}", ""]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"{i}. {step}")
        if self.rationale:
            lines.extend(["", f"Rationale: {self.rationale}"])
        return "\n".join(lines)


# Deterministic keyword -> target-file routing for the simulated planner. Keeps
# the offline plan grounded in the demo repository without any model call.
_DEFAULT_TARGET = "calculator.py"


class CodePlanner:
    """Reviews issues and proposes a structured code-modification plan."""

    def __init__(
        self,
        api_keys: Optional[dict] = None,
        model: str = "gpt-4o-mini",
    ):
        self.api_keys = api_keys or {}
        self.model = model

    def plan_changes(
        self,
        issue: dict,
        mocked_response: Optional[str] = None,
    ) -> FixPlan:
        """Generate a :class:`FixPlan` for the given issue.

        Args:
            issue: ``{"id", "title", "body", "labels"}`` issue payload.
            mocked_response: when provided, the real LLM path is skipped and a
                plan is built deterministically from the issue + this hint.
        """
        target = self._infer_target_file(issue)

        if mocked_response is not None:
            return self._simulated_plan(issue, target, hint=mocked_response)

        # Real path: only attempt when a key is actually configured.
        if self.api_keys.get("openai") or self.api_keys.get("anthropic"):
            try:
                text = self._call_llm(issue)
                return self._plan_from_llm_text(issue, target, text)
            except ImportError as exc:
                logger.warning("LLM SDK unavailable, using simulated plan: {}", exc)
            except Exception as exc:  # noqa: BLE001 - never crash the pipeline
                logger.warning("LLM call failed, using simulated plan: {}", exc)

        return self._simulated_plan(issue, target)

    # ---- simulated (deterministic) path ------------------------------------
    def _simulated_plan(
        self, issue: dict, target: str, hint: Optional[str] = None
    ) -> FixPlan:
        title = issue.get("title", "issue")
        steps = [
            f"Inspect {target} to locate the buggy function.",
            "Add the missing guard / fix so the failing test passes.",
            "Run the sandbox test suite to verify the fix.",
            "Open a draft pull request for human review.",
        ]
        rationale = (
            f"Issue #{issue.get('id', '?')} reports: {title}. "
            "The fix is scoped to a single allowlisted file."
        )
        if hint:
            rationale += f" (hint: {hint[:120]})"
        return FixPlan(
            summary=f"Fix: {title}",
            target_file=target,
            steps=steps,
            rationale=rationale,
        )

    def _plan_from_llm_text(self, issue: dict, target: str, text: str) -> FixPlan:
        """Wrap free-form model text into the structured plan contract."""
        steps = [
            line.strip(" -*0123456789.") for line in text.splitlines() if line.strip()
        ] or ["Apply the fix described by the model.", "Run tests."]
        return FixPlan(
            summary=f"Fix: {issue.get('title', 'issue')}",
            target_file=target,
            steps=steps[:8],
            rationale=text[:400],
        )

    def _infer_target_file(self, issue: dict) -> str:
        """Deterministically choose the target file from issue text."""
        text = f"{issue.get('title', '')} {issue.get('body', '')}".lower()
        # Look for an explicit ``file.py`` mention (first wins).
        for raw in text.replace(",", " ").split():
            token = raw.strip("`'\"()")
            if token.endswith(".py") and not token.startswith("/"):
                return token
        return _DEFAULT_TARGET

    # ---- real provider path -------------------------------------------------
    def _call_llm(self, issue: dict) -> str:
        from shared_core.llm import LLMClientFactory

        issue_text = (
            f"#{issue.get('id')}: {issue.get('title')}\n{issue.get('body', '')}"
        )
        prompt = (
            "You are a senior engineer. Produce a concise numbered implementation "
            "plan to fix this GitHub issue. One step per line.\n\n" + issue_text
        )
        factory = LLMClientFactory(
            openai_api_key=self.api_keys.get("openai"),
            anthropic_api_key=self.api_keys.get("anthropic"),
        )
        is_anthropic = "claude" in self.model.lower()
        if is_anthropic:
            if not self.api_keys.get("anthropic"):
                raise ImportError("No Anthropic API key configured")
            response = asyncio.run(factory.generate_anthropic(self.model, prompt))
        else:
            if not self.api_keys.get("openai"):
                raise ImportError("No OpenAI API key configured")
            response = asyncio.run(factory.generate_openai(self.model, prompt))
        return response.text
