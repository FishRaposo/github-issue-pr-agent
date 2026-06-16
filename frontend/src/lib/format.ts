import type { RunStatus } from "@/types";

/** Format a unix-seconds timestamp as a short absolute string. */
export function formatTime(ts: number | null | undefined): string {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/** Format a unix-seconds timestamp as a relative "x ago" string. */
export function formatRelative(ts: number | null | undefined): string {
  if (!ts) return "—";
  const seconds = Math.floor(Date.now() / 1000 - ts);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export interface StatusMeta {
  label: string;
  /** Tailwind classes for a badge (bg + text + border). */
  badge: string;
  /** Tailwind text color for icons / accents. */
  accent: string;
}

const STATUS_META: Record<RunStatus, StatusMeta> = {
  pending: {
    label: "Pending",
    badge: "bg-ink-100 text-ink-700 border-ink-200",
    accent: "text-ink-500",
  },
  planned: {
    label: "Planned",
    badge: "bg-indigo-50 text-indigo-700 border-indigo-200",
    accent: "text-indigo-500",
  },
  awaiting_approval: {
    label: "Awaiting approval",
    badge: "bg-amber-50 text-amber-700 border-amber-200",
    accent: "text-amber-500",
  },
  approved: {
    label: "Approved",
    badge: "bg-sky-50 text-sky-700 border-sky-200",
    accent: "text-sky-500",
  },
  completed: {
    label: "Completed",
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
    accent: "text-emerald-500",
  },
  failed: {
    label: "Failed",
    badge: "bg-rose-50 text-rose-700 border-rose-200",
    accent: "text-rose-500",
  },
};

export function statusMeta(status: string): StatusMeta {
  return (
    STATUS_META[status as RunStatus] || {
      label: status,
      badge: "bg-ink-100 text-ink-700 border-ink-200",
      accent: "text-ink-500",
    }
  );
}

/** Human-friendly label + accent color for an audit action type. */
export interface ActionMeta {
  label: string;
  /** Tailwind text/border color for the timeline dot. */
  tone: "agent" | "human" | "safety" | "success" | "danger";
}

const ACTION_META: Record<string, ActionMeta> = {
  run_started: { label: "Run started", tone: "agent" },
  issue_fetched: { label: "Issue fetched", tone: "agent" },
  plan_generated: { label: "Plan generated", tone: "agent" },
  branch_created: { label: "Branch created", tone: "safety" },
  fix_applied: { label: "Fix applied", tone: "agent" },
  fix_refused: { label: "Fix refused (safety gate)", tone: "danger" },
  changes_committed: { label: "Changes committed", tone: "agent" },
  tests_run: { label: "Tests run", tone: "agent" },
  awaiting_approval: { label: "Awaiting approval", tone: "safety" },
  approved: { label: "Approved", tone: "human" },
  approval_rejected: { label: "Approval rejected", tone: "danger" },
  pr_created: { label: "Draft PR created", tone: "success" },
  run_failed: { label: "Run failed", tone: "danger" },
};

export function actionMeta(action: string): ActionMeta {
  return ACTION_META[action] || { label: action, tone: "agent" };
}

export const ACTION_TONE_CLASSES: Record<ActionMeta["tone"], string> = {
  agent: "bg-brand-500 ring-brand-100",
  human: "bg-sky-500 ring-sky-100",
  safety: "bg-amber-500 ring-amber-100",
  success: "bg-emerald-500 ring-emerald-100",
  danger: "bg-rose-500 ring-rose-100",
};
