import Link from "next/link";
import { Bot, User } from "lucide-react";
import type { AuditEntry } from "@/types";
import { ACTION_TONE_CLASSES, actionMeta, formatTime } from "@/lib/format";

interface Props {
  entries: AuditEntry[];
  /** When true, link each entry to its run-detail page. */
  linkRuns?: boolean;
}

/** Append-only audit-trail timeline with action types + timestamps. */
export default function AuditTimeline({ entries, linkRuns = false }: Props) {
  // Newest first for display.
  const ordered = [...entries].sort(
    (a, b) => (b.timestamp ?? 0) - (a.timestamp ?? 0)
  );

  return (
    <ol className="relative space-y-0" data-testid="audit-timeline">
      {ordered.map((entry, i) => {
        const meta = actionMeta(entry.action);
        const last = i === ordered.length - 1;
        const detailStr = formatDetails(entry.details);
        return (
          <li key={entry.id} className="relative flex gap-4 pb-5">
            {/* connector + dot */}
            <div className="flex flex-col items-center">
              <span
                className={`mt-1 h-3 w-3 flex-shrink-0 rounded-full ring-4 ${ACTION_TONE_CLASSES[meta.tone]}`}
              />
              {!last && <span className="my-1 w-px flex-1 bg-ink-200" />}
            </div>

            <div className="flex-1 pb-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold text-ink-900">
                  {meta.label}
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2 py-0.5 text-[11px] font-medium text-ink-600">
                  {entry.actor === "human" ? (
                    <User className="h-3 w-3" />
                  ) : (
                    <Bot className="h-3 w-3" />
                  )}
                  {entry.actor}
                </span>
                <time className="text-xs text-ink-400">
                  {formatTime(entry.timestamp)}
                </time>
              </div>

              {detailStr && (
                <p className="mt-0.5 font-mono text-xs text-ink-500">
                  {detailStr}
                </p>
              )}

              {linkRuns && entry.run_id && (
                <Link
                  href={`/runs/${entry.run_id}`}
                  className="mt-1 inline-block text-xs font-medium text-brand-600 hover:underline"
                >
                  run {entry.run_id.slice(0, 8)} →
                </Link>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

function formatDetails(details: Record<string, unknown>): string {
  const keys = Object.keys(details);
  if (keys.length === 0) return "";
  return keys
    .map((k) => {
      const v = details[k];
      const text = Array.isArray(v) ? v.join(", ") : String(v);
      return `${k}: ${text}`;
    })
    .join("  ·  ");
}
