from issue_pr_agent.planner import CodePlanner


class TestCodePlanner:
    def test_plan_changes_returns_string(self):
        planner = CodePlanner()
        issue = {"id": 42, "title": "Fix division by zero", "body": "Calculator crashes."}
        plan = planner.plan_changes(issue)
        assert isinstance(plan, str)
        assert len(plan) > 0

    def test_plan_changes_with_empty_body(self):
        planner = CodePlanner()
        issue = {"id": 1, "title": "Simple issue", "body": ""}
        plan = planner.plan_changes(issue)
        assert isinstance(plan, str)
        assert "1" in plan or "Simple" in plan

    def test_plan_changes_contains_steps(self):
        planner = CodePlanner()
        issue = {"id": 99, "title": "Bug: edge case", "body": "Description here"}
        plan = planner.plan_changes(issue)
        assert any(
            kw in plan.lower()
            for kw in ["step", "plan", "inspect", "fix", "implement", "issue"]
        )
