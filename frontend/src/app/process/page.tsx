"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Send, Sparkles } from "lucide-react";
import type { Run } from "@/types";
import { apiClient, ApiError } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import PipelineTimeline from "@/components/PipelineTimeline";
import PlanView from "@/components/PlanView";
import { DemoWriteNotice } from "@/components/DemoBadge";

const SAMPLE_ISSUES = [
  { id: 101, title: "divide() crashes on division by zero" },
  { id: 102, title: "Add a safe percentage helper" },
];

export default function ProcessPage() {
  const [issueId, setIssueId] = useState("101");
  const [repo, setRepo] = useState("octocat/calculator");
  const [planHint, setPlanHint] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [demo, setDemo] = useState(false);
  const [queuedTaskId, setQueuedTaskId] = useState<string | null>(null);
  const [run, setRun] = useState<Run | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(issueId, 10);
    if (Number.isNaN(parsed)) {
      setError("Issue number must be an integer.");
      return;
    }
    setSubmitting(true);
    setError(null);
    setRun(null);
    setQueuedTaskId(null);
    try {
      const res = await apiClient.processIssue({
        issue_id: parsed,
        repo: repo.trim() || "owner/repo",
        mocked_plan: planHint.trim() || null,
        sync: true,
      });
      setDemo(res.demo);
      if (res.data.run) {
        setRun(res.data.run);
      } else if (res.data.task_id) {
        setQueuedTaskId(res.data.task_id);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`${err.message} (HTTP ${err.status})`);
      } else {
        setError(err instanceof Error ? err.message : "Failed to process issue");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">
          Process an issue
        </h1>
        <p className="mt-1 text-sm text-ink-600">
          Submit a GitHub issue to the agent. It plans a fix, edits allowlisted
          code in a sandbox, and runs tests — stopping at the approval gate.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Form */}
        <form onSubmit={handleSubmit} className="card space-y-4 lg:col-span-2">
          <div>
            <label htmlFor="issueId" className="mb-1 block text-sm font-medium text-ink-700">
              Issue number
            </label>
            <input
              id="issueId"
              type="number"
              value={issueId}
              onChange={(e) => setIssueId(e.target.value)}
              className="w-full rounded-lg border border-ink-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="101"
              required
            />
          </div>

          <div>
            <label htmlFor="repo" className="mb-1 block text-sm font-medium text-ink-700">
              Repository
            </label>
            <input
              id="repo"
              type="text"
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              className="w-full rounded-lg border border-ink-300 px-3 py-2 font-mono text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="owner/repo"
            />
          </div>

          <div>
            <label htmlFor="planHint" className="mb-1 block text-sm font-medium text-ink-700">
              Plan hint <span className="text-ink-400">(optional, offline)</span>
            </label>
            <textarea
              id="planHint"
              value={planHint}
              onChange={(e) => setPlanHint(e.target.value)}
              rows={2}
              className="w-full rounded-lg border border-ink-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="Force a deterministic offline plan hint"
            />
          </div>

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            <Send className="h-4 w-4" />
            {submitting ? "Processing…" : "Run agent pipeline"}
          </button>

          {error && (
            <p className="text-sm text-rose-600" role="alert">
              {error}
            </p>
          )}

          <div className="border-t border-ink-100 pt-3">
            <p className="mb-2 flex items-center gap-1 text-xs font-medium text-ink-500">
              <Sparkles className="h-3.5 w-3.5" />
              Sample issues
            </p>
            <div className="space-y-1">
              {SAMPLE_ISSUES.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setIssueId(String(s.id))}
                  className="block w-full rounded-md px-2 py-1 text-left text-xs text-ink-600 hover:bg-ink-50"
                >
                  <span className="font-mono font-semibold text-brand-600">#{s.id}</span>{" "}
                  {s.title}
                </button>
              ))}
            </div>
          </div>
        </form>

        {/* Result */}
        <div className="lg:col-span-3">
          {!run && !queuedTaskId ? (
            <div className="flex h-full min-h-[18rem] flex-col items-center justify-center rounded-xl border border-dashed border-ink-300 bg-ink-50/50 p-8 text-center">
              <Send className="mb-3 h-9 w-9 text-ink-400" />
              <p className="text-sm text-ink-500">
                Submit an issue to see the pipeline run and its generated plan
                here.
              </p>
            </div>
          ) : queuedTaskId ? (
            <div className="card">
              <h2 className="text-base font-semibold text-ink-900">Run queued</h2>
              <p className="mt-1 text-sm text-ink-600">
                Dispatched to the worker. Task id:
              </p>
              <code className="mt-2 block rounded bg-ink-100 px-2 py-1 font-mono text-xs">
                {queuedTaskId}
              </code>
            </div>
          ) : run ? (
            <div className="space-y-5 animate-fade-in">
              <div className="card">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="text-base font-semibold text-ink-900">
                      Issue #{run.issue_id}
                    </h2>
                    <p className="font-mono text-xs text-ink-500">{run.repo}</p>
                  </div>
                  <StatusBadge status={run.status} />
                </div>
                <PipelineTimeline run={run} />
              </div>

              {demo && (
                <DemoWriteNotice message="Demo mode — this run was simulated locally and not persisted to a backend." />
              )}

              <div className="card">
                <PlanView plan={run.plan} />
              </div>

              <Link
                href={`/runs/${run.id}`}
                className="btn-secondary w-fit"
              >
                Open full run detail
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
