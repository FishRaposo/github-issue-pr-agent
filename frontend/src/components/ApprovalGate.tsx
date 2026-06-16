"use client";

import { useState } from "react";
import {
  CheckCircle2,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import type { Run } from "@/types";
import { apiClient } from "@/lib/api";
import { ApiError } from "@/lib/api";
import { DemoWriteNotice } from "@/components/DemoBadge";

interface Props {
  run: Run;
  /** Called with the updated run after a successful approval. */
  onApproved?: (run: Run) => void;
}

/**
 * The human approval gate. A draft PR is only opened after the operator
 * explicitly approves a run that is awaiting approval (POST
 * /issues/{id}/approve). Visually emphasizes that this is the safety boundary.
 */
export default function ApprovalGate({ run, onApproved }: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [demo, setDemo] = useState(false);
  const [result, setResult] = useState<Run | null>(null);

  const current = result || run;
  const isAwaiting = current.status === "awaiting_approval";
  const isCompleted = current.status === "completed";

  const handleApprove = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await apiClient.approveIssue(current.issue_id, current.id);
      setResult(res.data.run);
      setDemo(res.demo);
      onApproved?.(res.data.run);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`${err.message} (HTTP ${err.status})`);
      } else {
        setError(err instanceof Error ? err.message : "Approval failed");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="rounded-xl border-2 border-dashed border-amber-300 bg-amber-50/60 p-5"
      data-testid="approval-gate"
    >
      <div className="mb-3 flex items-center gap-2">
        <ShieldAlert className="h-5 w-5 text-amber-600" />
        <h3 className="text-base font-semibold text-ink-900">Approval gate</h3>
      </div>

      {isCompleted ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium text-emerald-700">
            <CheckCircle2 className="h-5 w-5" />
            Approved — draft pull request opened.
          </div>
          {current.pr_url && (
            <a
              href={current.pr_url}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary w-fit"
            >
              <ExternalLink className="h-4 w-4" />
              View draft PR
            </a>
          )}
          {demo && (
            <DemoWriteNotice message="Demo mode — approval was simulated locally; no real PR was opened or persisted." />
          )}
        </div>
      ) : isAwaiting ? (
        <div className="space-y-3">
          <p className="max-w-2xl text-sm text-ink-700">
            This run passed its tests and is paused at the safety boundary. No
            pull request exists yet. Approving will open a{" "}
            <span className="font-semibold">draft</span> PR for human review —
            the only action that creates a PR.
          </p>
          <button
            onClick={handleApprove}
            disabled={submitting}
            className="btn-primary bg-emerald-600 hover:bg-emerald-700"
          >
            <ShieldCheck className="h-4 w-4" />
            {submitting ? "Approving…" : "Approve & open draft PR"}
          </button>
          {error && (
            <p className="text-sm text-rose-600" role="alert">
              {error}
            </p>
          )}
        </div>
      ) : (
        <p className="text-sm text-ink-600">
          This run is <span className="font-semibold">{current.status}</span> and
          is not awaiting approval. Approval is only available once a run reaches
          the gate with passing tests.
        </p>
      )}
    </div>
  );
}
