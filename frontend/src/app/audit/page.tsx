"use client";

import { useEffect, useMemo, useState } from "react";
import { RefreshCw, ScrollText } from "lucide-react";
import type { AuditEntry } from "@/types";
import { apiClient, ApiError } from "@/lib/api";
import DemoBadge from "@/components/DemoBadge";
import AuditTimeline from "@/components/AuditTimeline";
import { TimelineSkeleton } from "@/components/LoadingSkeleton";
import ErrorState from "@/components/ErrorState";
import EmptyState from "@/components/EmptyState";
import { actionMeta } from "@/lib/format";

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [demo, setDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionFilter, setActionFilter] = useState<string>("all");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getAudit(500);
      setEntries(res.data);
      setDemo(res.demo);
    } catch (err) {
      setError(
        err instanceof ApiError ? `${err.message} (HTTP ${err.status})` : "Failed to load audit log"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const actionTypes = useMemo(() => {
    const set = new Set(entries.map((e) => e.action));
    return Array.from(set).sort();
  }, [entries]);

  const filtered = useMemo(
    () =>
      actionFilter === "all"
        ? entries
        : entries.filter((e) => e.action === actionFilter),
    [entries, actionFilter]
  );

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-ink-900">
            <ScrollText className="h-6 w-6 text-brand-600" />
            Audit log
            {demo && <DemoBadge />}
          </h1>
          <p className="mt-1 text-sm text-ink-600">
            Append-only record of every action the agent and operators take.
          </p>
        </div>
        <button onClick={load} className="btn-secondary" disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </header>

      {!loading && !error && entries.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActionFilter("all")}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              actionFilter === "all"
                ? "bg-brand-600 text-white"
                : "border border-ink-200 bg-white text-ink-600 hover:bg-ink-50"
            }`}
          >
            All actions
          </button>
          {actionTypes.map((a) => (
            <button
              key={a}
              onClick={() => setActionFilter(a)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                actionFilter === a
                  ? "bg-brand-600 text-white"
                  : "border border-ink-200 bg-white text-ink-600 hover:bg-ink-50"
              }`}
            >
              {actionMeta(a).label}
            </button>
          ))}
        </div>
      )}

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : loading ? (
        <div className="card">
          <TimelineSkeleton />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No audit entries"
          message="Actions will appear here as the agent processes issues."
        />
      ) : (
        <div className="card">
          <AuditTimeline entries={filtered} linkRuns />
        </div>
      )}
    </div>
  );
}
