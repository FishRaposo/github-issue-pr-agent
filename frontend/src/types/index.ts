// Types mirroring the FastAPI backend response shapes (issue_pr_agent).
// A "run" is the JSON dict snapshot returned by the store (store.py); an audit
// entry mirrors store.log_action / get_audit.

/** Lifecycle status of a run (agent.py). */
export type RunStatus =
  | "pending"
  | "planned"
  | "awaiting_approval"
  | "approved"
  | "completed"
  | "failed";

/** A single issue-to-PR processing run. Matches store snapshot keys exactly. */
export interface Run {
  id: string;
  issue_id: number;
  repo: string;
  status: RunStatus;
  plan: string | null;
  branch: string | null;
  files_changed: string[];
  tests_passed: boolean | null;
  test_output: string | null;
  approved: boolean;
  pr_url: string | null;
  error: string | null;
  created_at: number | null;
  updated_at: number | null;
}

/** GET /runs */
export interface RunListResponse {
  runs: Run[];
}

/** An append-only audit-trail record. Matches store.log_action output. */
export interface AuditEntry {
  id: string;
  run_id: string | null;
  action: string;
  actor: string;
  details: Record<string, unknown>;
  timestamp: number | null;
}

/** GET /audit */
export interface AuditResponse {
  audit: AuditEntry[];
}

/** POST /issues/process request body (IssueRequest). */
export interface IssueRequest {
  issue_id: number;
  repo?: string;
  mocked_plan?: string | null;
  sync?: boolean;
}

/**
 * POST /issues/process response. The endpoint returns one of:
 *  - { status: "completed", run } when run synchronously / no broker
 *  - { status: "queued", task_id } when dispatched to Celery
 */
export interface ProcessResponse {
  status: "completed" | "queued";
  run?: Run;
  task_id?: string;
}

/** POST /issues/{id}/approve response. */
export interface ApproveResponse {
  status: "approved";
  run: Run;
}

/** GET /health */
export interface HealthCheck {
  status: string;
  service: string;
  dependencies: Record<string, string>;
}
