"""GitHub Issue-to-PR automation agent.

An offline-first agent that reads an issue, plans a fix, edits code in a sandbox
under strict safety guards, runs tests, and — after human approval — opens a draft
pull request. See ``issue_pr_agent.agent.IssuePRAgent`` for the orchestrator.
"""

__version__ = "1.0.0"
