"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight, GitBranch, RefreshCw } from "lucide-react";
import type { Run, RunStatus } from "@/types";
import { apiClient, ApiError } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import DemoBadge from "@/components/DemoBadge";
import { RunListSkeleton } from "@/components/LoadingSkeleton";
import ErrorState from "@/components/ErrorState";
import EmptyState from "@/components/EmptyState";
import { formatRelative } from "@/lib/format";

const FILTERS: { value: string; label: string }[] = [
  { value: "all", label: "All" },
  { value: "awaiting_approval", label: "Awaiting approval" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
];

function RunsPageInner() {
  const searchParams = useSearchParams();
  const initialStatus = searchParams.get("status") || "all";

  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [demo, setDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>(initialStatus);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.listRuns(200);
      setRuns(res.data);
      setDemo(res.demo);
    } catch (err) {
      setError(
        err instanceof ApiError ? `${err.message} (HTTP ${err.status})` : "Failed to load runs"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(
    () => (filter === "all" ? runs : runs.filter((r) => r.status === filter)),
    [runs, filter]
  );

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-ink-900">
            Runs
            {demo && <DemoBadge />}
          </h1>
          <p className="mt-1 text-sm text-ink-600">
            Every issue-to-PR run, most recent first.
          </p>
        </div>
        <button onClick={load} className="btn-secondary" disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </header>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              filter === f.value
                ? "bg-brand-600 text-white"
                : "border border-ink-200 bg-white text-ink-600 hover:bg-ink-50"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : loading ? (
        <RunListSkeleton />
      ) : filtered.length === 0 ? (
        <EmptyState
          title={filter === "all" ? "No runs yet" : "No runs match this filter"}
          message={
            filter === "all"
              ? "Process an issue to create your first run."
              : "Try a different status filter."
          }
          action={
            filter === "all" ? (
              <Link href="/process" className="btn-primary">
                Process an issue
              </Link>
            ) : undefined
          }
        />
      ) : (
        <ul className="space-y-3" data-testid="run-list">
          {filtered.map((run) => (
            <li key={run.id}>
              <Link
                href={`/runs/${run.id}`}
                className="card flex items-center justify-between gap-4 transition-shadow hover:shadow-md"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-semibold text-brand-600">
                      #{run.issue_id}
                    </span>
                    <span className="truncate text-sm font-medium text-ink-900">
                      {run.repo}
                    </span>
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-ink-500">
                    {run.branch && (
                      <span className="inline-flex items-center gap-1 font-mono">
                        <GitBranch className="h-3 w-3" />
                        {run.branch}
                      </span>
                    )}
                    <span>{run.files_changed.length} file(s) changed</span>
                    <span>{formatRelative(run.created_at)}</span>
                  </div>
                </div>
                <div className="flex flex-shrink-0 items-center gap-3">
                  <StatusBadge status={run.status} />
                  <ArrowRight className="h-4 w-4 text-ink-400" />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function RunsPage() {
  return (
    <Suspense fallback={<RunListSkeleton />}>
      <RunsPageInner />
    </Suspense>
  );
}
