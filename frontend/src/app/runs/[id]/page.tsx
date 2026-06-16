"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertOctagon,
  ArrowLeft,
  ExternalLink,
  GitBranch,
  Hash,
} from "lucide-react";
import type { AuditEntry, Run } from "@/types";
import { apiClient, ApiError } from "@/lib/api";
import { DEMO_DIFF_AFTER, DEMO_DIFF_BEFORE } from "@/lib/mockData";
import StatusBadge from "@/components/StatusBadge";
import DemoBadge from "@/components/DemoBadge";
import PipelineTimeline from "@/components/PipelineTimeline";
import PlanView from "@/components/PlanView";
import CodeDiff from "@/components/CodeDiff";
import TestResult from "@/components/TestResult";
import ApprovalGate from "@/components/ApprovalGate";
import AuditTimeline from "@/components/AuditTimeline";
import { DetailSkeleton } from "@/components/LoadingSkeleton";
import ErrorState from "@/components/ErrorState";
import { formatTime } from "@/lib/format";

export default function RunDetailPage({ params }: { params: { id: string } }) {
  const runId = params.id;
  const [run, setRun] = useState<Run | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [demo, setDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [runRes, auditRes] = await Promise.all([
        apiClient.getRun(runId),
        apiClient.getAudit(200, runId),
      ]);
      setRun(runRes.data);
      setAudit(auditRes.data);
      setDemo(runRes.demo || auditRes.demo);
    } catch (err) {
      setError(
        err instanceof ApiError ? `${err.message} (HTTP ${err.status})` : "Failed to load run"
      );
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleApproved = (updated: Run) => {
    setRun(updated);
    // Refresh the audit trail to reflect approval + PR creation.
    apiClient.getAudit(200, runId).then((res) => setAudit(res.data)).catch(() => {});
  };

  // Only the calculator.py demo has a known before/after we can render.
  const showDiff =
    !!run && run.files_changed.includes("calculator.py");

  return (
    <div className="space-y-6">
      <Link
        href="/runs"
        className="inline-flex items-center gap-1 text-sm font-medium text-ink-500 hover:text-ink-800"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to runs
      </Link>

      {error ? (
        <ErrorState
          title="Couldn't load this run"
          message={error}
          onRetry={load}
        />
      ) : loading ? (
        <DetailSkeleton />
      ) : run ? (
        <>
          {/* Header */}
          <div className="card">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold tracking-tight text-ink-900">
                    Issue #{run.issue_id}
                  </h1>
                  <StatusBadge status={run.status} />
                  {demo && <DemoBadge />}
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-ink-500">
                  <span className="inline-flex items-center gap-1 font-mono">
                    {run.repo}
                  </span>
                  {run.branch && (
                    <span className="inline-flex items-center gap-1 font-mono">
                      <GitBranch className="h-3.5 w-3.5" />
                      {run.branch}
                    </span>
                  )}
                  <span className="inline-flex items-center gap-1 font-mono">
                    <Hash className="h-3.5 w-3.5" />
                    {run.id.slice(0, 12)}
                  </span>
                  <span>created {formatTime(run.created_at)}</span>
                </div>
              </div>
              {run.pr_url && (
                <a
                  href={run.pr_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary"
                >
                  <ExternalLink className="h-4 w-4" />
                  Draft PR
                </a>
              )}
            </div>

            {run.error && (
              <div className="mt-4 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                <AlertOctagon className="mt-0.5 h-4 w-4 flex-shrink-0" />
                <span>{run.error}</span>
              </div>
            )}
          </div>

          {/* Pipeline */}
          <section className="card">
            <h2 className="mb-5 text-base font-semibold text-ink-900">
              Pipeline
            </h2>
            <PipelineTimeline run={run} />
          </section>

          {/* Approval gate (only meaningful at/after the gate) */}
          {(run.status === "awaiting_approval" || run.status === "completed" || run.status === "approved") && (
            <ApprovalGate run={run} onApproved={handleApproved} />
          )}

          {/* Plan + tests */}
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="card">
              <PlanView plan={run.plan} />
            </section>
            <section className="card">
              <h2 className="mb-3 text-sm font-semibold text-ink-700">
                Test results
              </h2>
              <TestResult run={run} />
            </section>
          </div>

          {/* Diff */}
          {showDiff && (
            <section className="card">
              <h2 className="mb-3 text-base font-semibold text-ink-900">
                Code change — before / after
              </h2>
              <CodeDiff
                filename="calculator.py"
                before={DEMO_DIFF_BEFORE}
                after={DEMO_DIFF_AFTER}
              />
            </section>
          )}

          {/* Audit */}
          <section className="card">
            <h2 className="mb-4 text-base font-semibold text-ink-900">
              Audit trail
            </h2>
            {audit.length === 0 ? (
              <p className="text-sm text-ink-500">
                No audit entries for this run.
              </p>
            ) : (
              <AuditTimeline entries={audit} />
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
