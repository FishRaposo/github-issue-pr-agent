import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient, ApiError } from "@/lib/api";
import { MOCK_RUNS } from "@/lib/mockData";

describe("apiClient demo-mode fallback", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("when the backend is unreachable", () => {
    beforeEach(() => {
      vi.stubGlobal(
        "fetch",
        vi.fn(() => Promise.reject(new Error("ECONNREFUSED")))
      );
    });

    it("falls back to bundled mock runs and flags demo mode", async () => {
      const res = await apiClient.listRuns();
      expect(res.demo).toBe(true);
      expect(res.data.length).toBe(MOCK_RUNS.length);
    });

    it("falls back to mock audit entries", async () => {
      const res = await apiClient.getAudit();
      expect(res.demo).toBe(true);
      expect(res.data.length).toBeGreaterThan(0);
    });

    it("returns a simulated run for processIssue", async () => {
      const res = await apiClient.processIssue({ issue_id: 101 });
      expect(res.demo).toBe(true);
      expect(res.data.run?.status).toBe("awaiting_approval");
      expect(res.data.run?.issue_id).toBe(101);
    });

    it("returns a simulated approval that opens a PR", async () => {
      const awaiting = MOCK_RUNS.find((r) => r.status === "awaiting_approval")!;
      const res = await apiClient.approveIssue(awaiting.issue_id, awaiting.id);
      expect(res.demo).toBe(true);
      expect(res.data.run.status).toBe("completed");
      expect(res.data.run.pr_url).toBeTruthy();
    });
  });

  describe("when the backend returns a real HTTP error", () => {
    beforeEach(() => {
      vi.stubGlobal(
        "fetch",
        vi.fn(() =>
          Promise.resolve(
            new Response(JSON.stringify({ detail: "Run xyz not found" }), {
              status: 404,
              headers: { "Content-Type": "application/json" },
            })
          )
        )
      );
    });

    it("surfaces a 4xx as an ApiError instead of masking with demo data", async () => {
      await expect(apiClient.getRun("xyz")).rejects.toBeInstanceOf(ApiError);
    });

    it("surfaces the error status code", async () => {
      try {
        await apiClient.getRun("xyz");
        throw new Error("expected ApiError");
      } catch (err) {
        expect(err).toBeInstanceOf(ApiError);
        expect((err as ApiError).status).toBe(404);
      }
    });
  });

  describe("error-message extraction across handler shapes", () => {
    afterEach(() => {
      vi.unstubAllGlobals();
    });

    function stubError(body: object, status = 422) {
      vi.stubGlobal(
        "fetch",
        vi.fn(() =>
          Promise.resolve(
            new Response(JSON.stringify(body), {
              status,
              headers: { "Content-Type": "application/json" },
            })
          )
        )
      );
    }

    it("uses shared_core's {error, message, status} message field", async () => {
      // shared_core's application_error_handler returns this shape; the
      // descriptive `message` must not be lost.
      stubError({ error: "validation_error", message: "issue_id is required", status: 422 });
      await expect(apiClient.getRun("xyz")).rejects.toMatchObject({
        message: "issue_id is required",
        status: 422,
      });
    });

    it("still falls back to FastAPI HTTPException {detail}", async () => {
      stubError({ detail: "Run xyz not found" }, 404);
      await expect(apiClient.getRun("xyz")).rejects.toMatchObject({
        message: "Run xyz not found",
        status: 404,
      });
    });

    it("falls back to a status code when neither field is present", async () => {
      stubError({}, 500);
      await expect(apiClient.getRun("xyz")).rejects.toMatchObject({
        message: "API error: 500",
        status: 500,
      });
    });
  });

  describe("when the backend is healthy", () => {
    beforeEach(() => {
      vi.stubGlobal(
        "fetch",
        vi.fn(() =>
          Promise.resolve(
            new Response(JSON.stringify({ runs: [] }), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            })
          )
        )
      );
    });

    it("returns live data with demo=false", async () => {
      const res = await apiClient.listRuns();
      expect(res.demo).toBe(false);
      expect(res.data).toEqual([]);
    });
  });
});
