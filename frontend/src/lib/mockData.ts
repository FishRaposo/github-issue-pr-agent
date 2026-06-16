// Bundled demo data so EVERY view is fully explorable with NO backend running.
// Shapes mirror the FastAPI backend exactly (see store.py / agent.py). These
// runs reproduce the canonical demo: the calculator.py division-by-zero fix
// (issue #101), plus a spread of states (completed, awaiting approval, tests
// failed, safety-refused) so the timeline, diff, and audit views all have
// meaningful content offline.

import type { AuditEntry, Run } from "@/types";

// A fixed reference instant so timestamps are deterministic across renders.
const NOW = 1_718_000_000; // ~2024-06-10 UTC; relative offsets below.

/** The buggy "before" content of the demo calculator.py divide function. */
export const DEMO_DIFF_BEFORE = `def divide(a, b):
    return a / b`;

/** The agent's "after" content once the safety guard is applied. */
export const DEMO_DIFF_AFTER = `def divide(a, b):
    if b == 0:
        return None
    return a / b`;

const PLAN_101 = [
  "Plan: Fix: divide() crashes on division by zero",
  "Target file: calculator.py",
  "",
  "1. Inspect calculator.py to locate the buggy function.",
  "2. Add the missing guard / fix so the failing test passes.",
  "3. Run the sandbox test suite to verify the fix.",
  "4. Open a draft pull request for human review.",
  "",
  "Rationale: Issue #101 reports: divide() crashes on division by zero. " +
    "The fix is scoped to a single allowlisted file.",
].join("\n");

const PLAN_102 = [
  "Plan: Fix: Add a safe percentage helper",
  "Target file: calculator.py",
  "",
  "1. Inspect calculator.py to locate the buggy function.",
  "2. Add the missing guard / fix so the failing test passes.",
  "3. Run the sandbox test suite to verify the fix.",
  "4. Open a draft pull request for human review.",
  "",
  "Rationale: Issue #102 reports: Add a safe percentage helper. " +
    "The fix is scoped to a single allowlisted file.",
].join("\n");

const PLAN_205 = [
  "Plan: Fix: Harden config loader against missing keys",
  "Target file: config.py",
  "",
  "1. Inspect config.py to locate the buggy function.",
  "2. Add the missing guard / fix so the failing test passes.",
  "3. Run the sandbox test suite to verify the fix.",
  "4. Open a draft pull request for human review.",
  "",
  "Rationale: Issue #205 reports: Harden config loader against missing keys. " +
    "The fix is scoped to a single allowlisted file.",
].join("\n");

const TEST_OUTPUT_PASS = "6 passed in 0.08s";
const TEST_OUTPUT_FAIL =
  "1 failed, 5 passed in 0.09s\n" +
  "FAILED test_calculator.py::test_divide_by_zero_returns_none - assert ... is None";

export const MOCK_RUNS: Run[] = [
  {
    id: "9f1c4a2b7e8d4f3a9b2c1d0e5f6a7b80",
    issue_id: 101,
    repo: "octocat/calculator",
    status: "completed",
    plan: PLAN_101,
    branch: "agent/fix-issue-101",
    files_changed: ["calculator.py"],
    tests_passed: true,
    test_output: TEST_OUTPUT_PASS,
    approved: true,
    pr_url: "https://github.com/octocat/calculator/pull/42",
    error: null,
    created_at: NOW - 60 * 42,
    updated_at: NOW - 60 * 39,
  },
  {
    id: "3a7b9c1d2e4f5061728394a5b6c7d8e9",
    issue_id: 102,
    repo: "octocat/calculator",
    status: "awaiting_approval",
    plan: PLAN_102,
    branch: "agent/fix-issue-102",
    files_changed: ["calculator.py"],
    tests_passed: true,
    test_output: TEST_OUTPUT_PASS,
    approved: false,
    pr_url: null,
    error: null,
    created_at: NOW - 60 * 18,
    updated_at: NOW - 60 * 16,
  },
  {
    id: "b2c3d4e5f60718293a4b5c6d7e8f9012",
    issue_id: 144,
    repo: "octocat/calculator",
    status: "failed",
    plan: PLAN_101,
    branch: "agent/fix-issue-144",
    files_changed: ["calculator.py"],
    tests_passed: false,
    test_output: TEST_OUTPUT_FAIL,
    approved: false,
    pr_url: null,
    error: "tests failed",
    created_at: NOW - 60 * 120,
    updated_at: NOW - 60 * 118,
  },
  {
    id: "c4d5e6f7081920304a5b6c7d8e9f0a1b",
    issue_id: 205,
    repo: "octocat/calculator",
    status: "failed",
    plan: PLAN_205,
    branch: "agent/fix-issue-205",
    files_changed: [],
    tests_passed: null,
    test_output: null,
    approved: false,
    pr_url: null,
    error:
      "fix refused by safety gate: path 'config.py' matches blocklist pattern",
    created_at: NOW - 60 * 200,
    updated_at: NOW - 60 * 199,
  },
];

function audit(
  id: string,
  runId: string | null,
  action: string,
  actor: string,
  details: Record<string, unknown>,
  ts: number
): AuditEntry {
  return { id, run_id: runId, action, actor, details, timestamp: ts };
}

const R0 = MOCK_RUNS[0].id;
const R1 = MOCK_RUNS[1].id;
const R2 = MOCK_RUNS[2].id;
const R3 = MOCK_RUNS[3].id;

// Append-only audit trail (oldest first), mirroring the actions logged by the
// agent pipeline in agent.py.
export const MOCK_AUDIT: AuditEntry[] = [
  // --- run #101 (completed end-to-end) ---
  audit("a01", R0, "run_started", "agent", { issue_id: 101, repo: "octocat/calculator" }, NOW - 60 * 42),
  audit("a02", R0, "issue_fetched", "agent", { title: "divide() crashes on division by zero" }, NOW - 60 * 42 + 2),
  audit("a03", R0, "plan_generated", "agent", { target: "calculator.py", steps: 4 }, NOW - 60 * 42 + 5),
  audit("a04", R0, "branch_created", "agent", { branch: "agent/fix-issue-101" }, NOW - 60 * 42 + 7),
  audit("a05", R0, "fix_applied", "agent", { files: ["calculator.py"] }, NOW - 60 * 42 + 9),
  audit("a06", R0, "changes_committed", "agent", { branch: "agent/fix-issue-101" }, NOW - 60 * 42 + 11),
  audit("a07", R0, "tests_run", "agent", { passed: true, summary: TEST_OUTPUT_PASS }, NOW - 60 * 42 + 18),
  audit("a08", R0, "awaiting_approval", "agent", {}, NOW - 60 * 42 + 19),
  audit("a09", R0, "approved", "human", { actor: "human" }, NOW - 60 * 40),
  audit("a10", R0, "pr_created", "human", { pr_url: "https://github.com/octocat/calculator/pull/42", draft: true }, NOW - 60 * 39),

  // --- run #102 (waiting at the approval gate) ---
  audit("b01", R1, "run_started", "agent", { issue_id: 102, repo: "octocat/calculator" }, NOW - 60 * 18),
  audit("b02", R1, "issue_fetched", "agent", { title: "Add a safe percentage helper" }, NOW - 60 * 18 + 2),
  audit("b03", R1, "plan_generated", "agent", { target: "calculator.py", steps: 4 }, NOW - 60 * 18 + 4),
  audit("b04", R1, "branch_created", "agent", { branch: "agent/fix-issue-102" }, NOW - 60 * 18 + 6),
  audit("b05", R1, "fix_applied", "agent", { files: ["calculator.py"] }, NOW - 60 * 18 + 8),
  audit("b06", R1, "changes_committed", "agent", { branch: "agent/fix-issue-102" }, NOW - 60 * 18 + 10),
  audit("b07", R1, "tests_run", "agent", { passed: true, summary: TEST_OUTPUT_PASS }, NOW - 60 * 16 - 5),
  audit("b08", R1, "awaiting_approval", "agent", {}, NOW - 60 * 16),

  // --- run #144 (tests failed, no PR) ---
  audit("c01", R2, "run_started", "agent", { issue_id: 144, repo: "octocat/calculator" }, NOW - 60 * 120),
  audit("c02", R2, "issue_fetched", "agent", { title: "divide() still throws on zero" }, NOW - 60 * 120 + 2),
  audit("c03", R2, "plan_generated", "agent", { target: "calculator.py", steps: 4 }, NOW - 60 * 120 + 4),
  audit("c04", R2, "branch_created", "agent", { branch: "agent/fix-issue-144" }, NOW - 60 * 120 + 6),
  audit("c05", R2, "fix_applied", "agent", { files: ["calculator.py"] }, NOW - 60 * 120 + 8),
  audit("c06", R2, "tests_run", "agent", { passed: false, summary: TEST_OUTPUT_FAIL }, NOW - 60 * 119),
  audit("c07", R2, "run_failed", "agent", { reason: "tests" }, NOW - 60 * 118),

  // --- run #205 (refused by the safety gate) ---
  audit("d01", R3, "run_started", "agent", { issue_id: 205, repo: "octocat/calculator" }, NOW - 60 * 200),
  audit("d02", R3, "issue_fetched", "agent", { title: "Harden config loader against missing keys" }, NOW - 60 * 200 + 2),
  audit("d03", R3, "plan_generated", "agent", { target: "config.py", steps: 4 }, NOW - 60 * 200 + 4),
  audit("d04", R3, "branch_created", "agent", { branch: "agent/fix-issue-205" }, NOW - 60 * 200 + 6),
  audit("d05", R3, "fix_refused", "agent", { path: "config.py", reason: "path matches blocklist pattern" }, NOW - 60 * 199 - 2),
  audit("d06", R3, "run_failed", "agent", { reason: "fix refused by safety gate" }, NOW - 60 * 199),
];

/** Build a fresh, realistic run snapshot for a newly "processed" issue in demo
 *  mode. Mirrors what the pipeline returns when it stops at awaiting_approval. */
export function makeDemoRun(issueId: number, repo: string): Run {
  const id = `demo${Date.now().toString(16)}${Math.floor(Math.random() * 1e6).toString(16)}`;
  const ts = Math.floor(Date.now() / 1000);
  const plan = [
    `Plan: Fix: issue #${issueId}`,
    "Target file: calculator.py",
    "",
    "1. Inspect calculator.py to locate the buggy function.",
    "2. Add the missing guard / fix so the failing test passes.",
    "3. Run the sandbox test suite to verify the fix.",
    "4. Open a draft pull request for human review.",
    "",
    `Rationale: Issue #${issueId} processed in demo mode. ` +
      "The fix is scoped to a single allowlisted file.",
  ].join("\n");
  return {
    id,
    issue_id: issueId,
    repo,
    status: "awaiting_approval",
    plan,
    branch: `agent/fix-issue-${issueId}`,
    files_changed: ["calculator.py"],
    tests_passed: true,
    test_output: TEST_OUTPUT_PASS,
    approved: false,
    pr_url: null,
    error: null,
    created_at: ts,
    updated_at: ts,
  };
}

/** Audit entries for a freshly created demo run (issue -> plan -> ... -> gate). */
export function makeDemoAudit(run: Run): AuditEntry[] {
  const base = run.created_at ?? Math.floor(Date.now() / 1000);
  const rid = run.id;
  return [
    audit(`${rid}-1`, rid, "run_started", "agent", { issue_id: run.issue_id, repo: run.repo }, base),
    audit(`${rid}-2`, rid, "issue_fetched", "agent", { title: `issue #${run.issue_id}` }, base + 1),
    audit(`${rid}-3`, rid, "plan_generated", "agent", { target: "calculator.py", steps: 4 }, base + 2),
    audit(`${rid}-4`, rid, "branch_created", "agent", { branch: run.branch }, base + 3),
    audit(`${rid}-5`, rid, "fix_applied", "agent", { files: run.files_changed }, base + 4),
    audit(`${rid}-6`, rid, "tests_run", "agent", { passed: true, summary: run.test_output }, base + 5),
    audit(`${rid}-7`, rid, "awaiting_approval", "agent", {}, base + 6),
  ];
}
