"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  GitPullRequestArrow,
  ListChecks,
  ScrollText,
  Send,
} from "lucide-react";
import type { Run } from "@/types";
import { apiClient, ApiError } from "@/lib/api";
import SafetyPanel from "@/components/SafetyPanel";
import RunStatsChart from "@/components/RunStatsChart";
import DemoBadge from "@/components/DemoBadge";
import { CardSkeleton } from "@/components/LoadingSkeleton";
import ErrorState from "@/components/ErrorState";
import { statusMeta } from "@/lib/format";

export default function OverviewPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [demo, setDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.listRuns(200);
      setRuns(res.data);
      setDemo(res.demo);
    } catch (err) {
      setError(err instanceof ApiError ? `${err.message} (HTTP ${err.status})` : "Failed to load runs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const awaiting = runs.filter((r) => r.status === "awaiting_approval").length;
  const completed = runs.filter((r) => r.status === "completed").length;
  const failed = runs.filter((r) => r.status === "failed").length;

  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="overflow-hidden rounded-2xl border border-ink-200 bg-gradient-to-br from-brand-600 to-brand-800 p-8 text-white">
        <div className="flex items-center gap-2 text-brand-100">
          <GitPullRequestArrow className="h-5 w-5" />
          <span className="text-sm font-medium">Issue-to-PR automation console</span>
          {demo && <DemoBadge className="border-white/30 bg-white/10 text-white" />}
        </div>
        <h1 className="mt-3 max-w-3xl text-3xl font-bold tracking-tight sm:text-4xl">
          Turn GitHub issues into reviewed draft PRs — safely.
        </h1>
        <p className="mt-3 max-w-2xl text-sm text-brand-100">
          The agent reads an issue, plans a fix, edits only allowlisted code in a
          sandbox, proves it with real tests, and stops at a human approval gate
          before opening a draft pull request. Every step is audited.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/process" className="btn-primary bg-white text-brand-700 hover:bg-brand-50">
            <Send className="h-4 w-4" />
            Process an issue
          </Link>
          <Link
            href="/runs"
            className="btn-secondary border-white/30 bg-white/10 text-white hover:bg-white/20"
          >
            <ListChecks className="h-4 w-4" />
            View runs
          </Link>
        </div>
      </section>

      {/* Stats + chart */}
      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total runs" value={runs.length} tone="text-ink-900" />
            <StatCard
              label="Awaiting approval"
              value={awaiting}
              tone={statusMeta("awaiting_approval").accent}
              href="/runs?status=awaiting_approval"
            />
            <StatCard
              label="Completed"
              value={completed}
              tone={statusMeta("completed").accent}
            />
            <StatCard label="Failed" value={failed} tone={statusMeta("failed").accent} />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <div className="card">
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-base font-semibold text-ink-900">Runs by status</h2>
                {demo && <DemoBadge />}
              </div>
              <RunStatsChart runs={runs} />
            </div>
            <div className="card flex flex-col">
              <h2 className="mb-3 text-base font-semibold text-ink-900">How it works</h2>
              <ol className="flex-1 space-y-2 text-sm text-ink-600">
                <li>1. Submit an issue on the Process page.</li>
                <li>2. The agent plans, branches, edits, and runs tests in a sandbox.</li>
                <li>3. A passing run waits at the approval gate — no PR yet.</li>
                <li>4. You approve; a draft PR is opened and the trail is sealed.</li>
              </ol>
              <Link
                href="/audit"
                className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:underline"
              >
                <ScrollText className="h-4 w-4" />
                See the full audit log
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </section>
        </>
      )}

      {/* Safety model */}
      <SafetyPanel />
    </div>
  );
}

function StatCard({
  label,
  value,
  tone,
  href,
}: {
  label: string;
  value: number;
  tone: string;
  href?: string;
}) {
  const inner = (
    <div className="card transition-shadow hover:shadow-md">
      <p className="text-xs font-medium uppercase tracking-wide text-ink-500">
        {label}
      </p>
      <p className={`mt-1 text-3xl font-bold ${tone}`}>{value}</p>
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}
