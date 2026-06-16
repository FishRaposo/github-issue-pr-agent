import type { Run } from "@/types";

/**
 * The fixed pipeline a run progresses through:
 *   issue -> plan -> branch -> edit -> tests -> approval -> draft PR
 * (mirrors agent.process_issue + approve_and_open_pr in agent.py).
 */
export type StageState = "done" | "active" | "pending" | "failed" | "blocked";

export interface PipelineStage {
  key: string;
  label: string;
  description: string;
  state: StageState;
}

/**
 * Derive the per-stage state of a run from its status + recorded outcomes.
 * Used to render the run-detail pipeline timeline.
 */
export function derivePipeline(run: Run): PipelineStage[] {
  const s = run.status;
  const failed = s === "failed";
  const refused = failed && (run.error?.includes("safety") ?? false);
  const testsFailed = run.tests_passed === false;

  // Helper: is a stage complete given how far the run got?
  const reached = (...statuses: string[]) => statuses.includes(s);

  const issueDone = true; // a run always starts from a fetched issue
  const planDone =
    reached("planned", "awaiting_approval", "approved", "completed") ||
    (failed && !!run.plan);
  const branchDone =
    reached("planned", "awaiting_approval", "approved", "completed") ||
    (failed && !!run.branch);
  const editDone =
    reached("awaiting_approval", "approved", "completed") ||
    (failed && run.files_changed.length > 0 && !refused);
  const testsDone = run.tests_passed === true;
  const approvalDone = reached("approved", "completed");
  const prDone = s === "completed" && !!run.pr_url;

  const stages: PipelineStage[] = [
    {
      key: "issue",
      label: "Issue",
      description: "Fetch the GitHub issue",
      state: issueDone ? "done" : "pending",
    },
    {
      key: "plan",
      label: "Plan",
      description: "Generate a structured fix plan",
      state: planDone ? "done" : refused ? "failed" : "pending",
    },
    {
      key: "branch",
      label: "Branch",
      description: "Leave protected branch (no-main guard)",
      state: branchDone ? "done" : "pending",
    },
    {
      key: "edit",
      label: "Edit",
      description: "Apply fix to allowlisted paths",
      state: refused
        ? "blocked"
        : editDone
        ? "done"
        : "pending",
    },
    {
      key: "tests",
      label: "Tests",
      description: "Run the sandbox test suite",
      state: testsDone
        ? "done"
        : testsFailed
        ? "failed"
        : refused
        ? "pending"
        : "pending",
    },
    {
      key: "approval",
      label: "Approval gate",
      description: "Human approves before any PR",
      state: approvalDone
        ? "done"
        : s === "awaiting_approval"
        ? "active"
        : "pending",
    },
    {
      key: "pr",
      label: "Draft PR",
      description: "Open a draft pull request",
      state: prDone ? "done" : "pending",
    },
  ];

  return stages;
}

/** A unified-style diff hunk line, classified for rendering. */
export interface DiffLine {
  type: "add" | "del" | "context";
  text: string;
}

/** Produce a simple line-by-line diff between two code blocks. */
export function computeDiff(before: string, after: string): DiffLine[] {
  const beforeLines = before.split("\n");
  const afterLines = after.split("\n");
  const lines: DiffLine[] = [];
  const beforeSet = new Set(beforeLines);
  const afterSet = new Set(afterLines);

  // Leading common lines.
  let i = 0;
  while (
    i < beforeLines.length &&
    i < afterLines.length &&
    beforeLines[i] === afterLines[i]
  ) {
    lines.push({ type: "context", text: beforeLines[i] });
    i++;
  }
  // Removed lines (present before, not after).
  for (let b = i; b < beforeLines.length; b++) {
    if (!afterSet.has(beforeLines[b])) {
      lines.push({ type: "del", text: beforeLines[b] });
    }
  }
  // Added lines (present after, not before).
  for (let a = i; a < afterLines.length; a++) {
    if (!beforeSet.has(afterLines[a])) {
      lines.push({ type: "add", text: afterLines[a] });
    }
  }
  // Trailing common lines after the change.
  for (let a = i; a < afterLines.length; a++) {
    if (beforeSet.has(afterLines[a]) && a > i) {
      lines.push({ type: "context", text: afterLines[a] });
    }
  }
  return lines;
}
