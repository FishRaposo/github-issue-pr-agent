import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from issue_pr_agent.editor import CodeEditor
from issue_pr_agent.github import MockGitHubClient
from issue_pr_agent.planner import CodePlanner
from issue_pr_agent.test_runner import LocalTestRunner


def main():
    dummy_file = "calculator.py"
    with open(dummy_file, "w") as f:
        f.write("def sum_numbers(val):\n    return val\n")

    print("--- Running GitHub Issue-to-PR Agent Sim ---")
    gh = MockGitHubClient()
    planner = CodePlanner()
    editor = CodeEditor()
    runner = LocalTestRunner()

    issue = gh.get_issue(101)
    plan = planner.plan_changes(issue)
    print("Agent Plan:\n", plan)

    print(f"Applying fix to {dummy_file}...")
    editor.apply_fix(dummy_file)

    success = runner.run_tests()
    print("Tests passed:", success)

    pr_url = gh.create_pull_request(
        "fix-calculator-bug", "Fix calculator issue", "Automated patch."
    )
    print("PR Created:", pr_url)

    os.remove(dummy_file)

if __name__ == "__main__":
    main()
