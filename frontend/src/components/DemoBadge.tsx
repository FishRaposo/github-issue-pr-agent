import { FlaskConical } from "lucide-react";

/**
 * Visible "Demo mode" indicator shown whenever a view is rendering bundled mock
 * data because the backend was unreachable. Live HTTP errors are NOT shown as
 * demo mode — they surface as real error states elsewhere.
 */
export default function DemoBadge({ className = "" }: { className?: string }) {
  return (
    <span
      className={`badge border-amber-200 bg-amber-50 text-amber-700 ${className}`}
      title="The backend was unreachable — showing bundled demo data."
      data-testid="demo-badge"
    >
      <FlaskConical className="h-3.5 w-3.5" />
      Demo mode
    </span>
  );
}

/** Inline notice for write actions in demo mode (not persisted to a backend). */
export function DemoWriteNotice({ message }: { message?: string }) {
  return (
    <div
      className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700"
      data-testid="demo-write-notice"
    >
      <FlaskConical className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
      <span>
        {message ||
          "Demo mode — this action was simulated locally and not persisted to a backend."}
      </span>
    </div>
  );
}
