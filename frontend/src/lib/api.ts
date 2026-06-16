import type {
  ApproveResponse,
  AuditResponse,
  HealthCheck,
  IssueRequest,
  ProcessResponse,
  Run,
  RunListResponse,
} from "@/types";
import {
  makeDemoAudit,
  makeDemoRun,
  MOCK_AUDIT,
  MOCK_RUNS,
} from "@/lib/mockData";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Raised when the backend returns a real HTTP 4xx/5xx. These are surfaced as
 * error states (never masked by demo data) so genuine API failures stay visible.
 */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Thrown internally when the backend is simply unreachable (offline/network). */
class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}

/**
 * A result that carries whether the data came from the live backend or from the
 * bundled demo fallback, so the UI can show a "Demo mode" indicator.
 */
export interface ResultMeta<T> {
  data: T;
  demo: boolean;
}

// Kept short so that, when the backend is down, views fall back to demo data
// quickly rather than hanging. Real responses return well within this window.
const REQUEST_TIMEOUT_MS = 2500;

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Low-level request. Distinguishes two failure modes:
   *  - HTTP 4xx/5xx -> throws ApiError (surfaced to the user)
   *  - network/timeout -> throws NetworkError (callers fall back to demo data)
   */
  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    let response: Response;
    try {
      response = await fetch(url, {
        signal: controller.signal,
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
      });
    } catch (err) {
      throw new NetworkError(
        err instanceof Error ? err.message : "Network request failed"
      );
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok) {
      const body = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      // shared_core's error handler returns {error, message, status}; FastAPI's
      // HTTPException returns {detail}. Prefer message, then detail, then a code.
      const msg = body.message || body.detail || `API error: ${response.status}`;
      throw new ApiError(msg, response.status);
    }

    return response.json();
  }

  // ---- reads (live-first with demo fallback) -------------------------------

  async listRuns(limit = 50): Promise<ResultMeta<Run[]>> {
    try {
      const res = await this.request<RunListResponse>(`/runs?limit=${limit}`);
      return { data: res.runs, demo: false };
    } catch (err) {
      if (err instanceof ApiError) throw err;
      return { data: MOCK_RUNS, demo: true };
    }
  }

  async getRun(runId: string): Promise<ResultMeta<Run>> {
    try {
      const res = await this.request<Run>(`/runs/${runId}`);
      return { data: res, demo: false };
    } catch (err) {
      if (err instanceof ApiError) throw err;
      const found = MOCK_RUNS.find((r) => r.id === runId);
      if (!found) {
        throw new ApiError(`Run ${runId} not found`, 404);
      }
      return { data: found, demo: true };
    }
  }

  async getAudit(limit = 200, runId?: string): Promise<ResultMeta<AuditResponse["audit"]>> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (runId) params.set("run_id", runId);
    try {
      const res = await this.request<AuditResponse>(`/audit?${params}`);
      return { data: res.audit, demo: false };
    } catch (err) {
      if (err instanceof ApiError) throw err;
      const filtered = runId
        ? MOCK_AUDIT.filter((e) => e.run_id === runId)
        : MOCK_AUDIT;
      return { data: filtered, demo: true };
    }
  }

  // ---- writes (live-first; demo writes are not persisted) ------------------

  async processIssue(req: IssueRequest): Promise<ResultMeta<ProcessResponse>> {
    try {
      const res = await this.request<ProcessResponse>("/issues/process", {
        method: "POST",
        body: JSON.stringify({ sync: true, repo: "owner/repo", ...req }),
      });
      return { data: res, demo: false };
    } catch (err) {
      if (err instanceof ApiError) throw err;
      const run = makeDemoRun(req.issue_id, req.repo || "owner/repo");
      return { data: { status: "completed", run }, demo: true };
    }
  }

  async approveIssue(
    issueId: number,
    runId?: string
  ): Promise<ResultMeta<ApproveResponse>> {
    const query = runId ? `?run_id=${encodeURIComponent(runId)}` : "";
    try {
      const res = await this.request<ApproveResponse>(
        `/issues/${issueId}/approve${query}`,
        { method: "POST" }
      );
      return { data: res, demo: false };
    } catch (err) {
      if (err instanceof ApiError) throw err;
      const base = MOCK_RUNS.find((r) => r.id === runId) ||
        MOCK_RUNS.find((r) => r.issue_id === issueId);
      const approved: Run = base
        ? {
            ...base,
            status: "completed",
            approved: true,
            pr_url: `https://github.com/${base.repo}/pull/42`,
          }
        : makeDemoRun(issueId, "owner/repo");
      return { data: { status: "approved", run: approved }, demo: true };
    }
  }

  async healthCheck(): Promise<ResultMeta<HealthCheck>> {
    try {
      const res = await this.request<HealthCheck>("/health");
      return { data: res, demo: false };
    } catch (err) {
      if (err instanceof ApiError) throw err;
      return {
        data: {
          status: "offline",
          service: "github-issue-pr-agent",
          dependencies: { database: "offline", redis: "offline" },
        },
        demo: true,
      };
    }
  }
}

export { makeDemoAudit, makeDemoRun };
export const apiClient = new ApiClient(API_BASE);
export const API_URL = API_BASE;
