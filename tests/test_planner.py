"""Unit + golden tests for the simulated planner."""

from issue_pr_agent.planner import CodePlanner, FixPlan


class TestCodePlanner:
    def test_returns_fixplan(self, sample_issue):
        plan = CodePlanner().plan_changes(sample_issue)
        assert isinstance(plan, FixPlan)
        assert plan.summary
        assert plan.target_file
        assert len(plan.steps) >= 1

    def test_target_file_inferred_from_body(self, sample_issue):
        plan = CodePlanner().plan_changes(sample_issue)
        assert plan.target_file == "calculator.py"

    def test_target_file_default_when_absent(self):
        plan = CodePlanner().plan_changes(
            {"id": 1, "title": "vague", "body": "something is broken"}
        )
        assert plan.target_file == "calculator.py"

    def test_mocked_response_is_deterministic(self, sample_issue):
        a = CodePlanner().plan_changes(sample_issue, mocked_response="hint")
        b = CodePlanner().plan_changes(sample_issue, mocked_response="hint")
        assert a.to_dict() == b.to_dict()

    def test_mocked_response_included_in_rationale(self, sample_issue):
        plan = CodePlanner().plan_changes(sample_issue, mocked_response="USE GUARD")
        assert "USE GUARD" in plan.rationale

    def test_no_llm_call_without_keys(self, monkeypatch, sample_issue):
        # If no keys configured, the real LLM path must never be invoked.
        def _boom(*_a, **_k):
            raise AssertionError("LLM should not be called without keys")

        monkeypatch.setattr(CodePlanner, "_call_llm", _boom)
        plan = CodePlanner(api_keys={}).plan_changes(sample_issue)
        assert isinstance(plan, FixPlan)

    def test_llm_failure_falls_back_to_simulation(self, monkeypatch, sample_issue):
        def _boom(*_a, **_k):
            raise RuntimeError("network down")

        planner = CodePlanner(api_keys={"openai": "sk-test"})
        monkeypatch.setattr(planner, "_call_llm", _boom)
        plan = planner.plan_changes(sample_issue)
        assert isinstance(plan, FixPlan)
        assert plan.target_file == "calculator.py"

    def test_real_path_used_when_key_present(self, monkeypatch, sample_issue):
        planner = CodePlanner(api_keys={"openai": "sk-test"})
        monkeypatch.setattr(planner, "_call_llm", lambda issue: "1. do x\n2. do y")
        plan = planner.plan_changes(sample_issue)
        assert "do x" in plan.steps or any("do x" in s for s in plan.steps)

    def test_plan_to_text_and_dict(self, sample_issue):
        plan = CodePlanner().plan_changes(sample_issue)
        text = plan.to_text()
        assert "Plan:" in text and "Target file:" in text
        d = plan.to_dict()
        assert set(d) == {"summary", "target_file", "steps", "rationale"}


class TestPlannerGolden:
    """Golden output so the deterministic plan never silently drifts."""

    def test_golden_steps(self, sample_issue):
        plan = CodePlanner().plan_changes(sample_issue)
        assert plan.steps == [
            "Inspect calculator.py to locate the buggy function.",
            "Add the missing guard / fix so the failing test passes.",
            "Run the sandbox test suite to verify the fix.",
            "Open a draft pull request for human review.",
        ]
