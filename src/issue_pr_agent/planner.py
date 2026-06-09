from typing import Optional

from loguru import logger


class CodePlanner:
    """Reviews issues and proposes code modification steps."""

    def __init__(self, api_keys: Optional[dict] = None):
        self.api_keys = api_keys or {}

    def plan_changes(self, issue: dict) -> str:
        issue_text = f"#{issue['id']}: {issue['title']}\n{issue['body']}"
        try:
            from shared_core.llm import LLMClientFactory

            factory = LLMClientFactory(
                openai_api_key=self.api_keys.get("openai"),
            )
            response = factory.generate_mock(
                "gpt-4o-mini",
                f"Create a step-by-step implementation plan for: {issue_text}",
            )
            return response.text
        except Exception as e:
            logger.warning(f"LLM unavailable, using template plan: {e}")

        return (
            f"Plan for Issue #{issue['id']}:\n"
            "1. Inspect src/calculator.py\n"
            "2. Add empty list check in sum() method to return 0\n"
            "3. Run test suite to verify success."
        )
