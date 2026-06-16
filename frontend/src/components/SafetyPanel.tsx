import { GitBranch, Lock, ShieldCheck, TestTube2, UserCheck } from "lucide-react";
import {
  ALLOWED_GLOBS,
  BLOCKED_GLOBS,
  PROTECTED_BRANCHES,
  SAFETY_CONTROLS,
} from "@/lib/safety";

const CONTROL_ICONS = [Lock, GitBranch, TestTube2, UserCheck];

/** Visual summary of the agent's safety model. */
export default function SafetyPanel() {
  return (
    <section className="card border-emerald-200 bg-gradient-to-br from-emerald-50/60 to-white">
      <div className="mb-4 flex items-center gap-2">
        <ShieldCheck className="h-5 w-5 text-emerald-600" />
        <h2 className="text-lg font-semibold text-ink-900">Safety model</h2>
      </div>
      <p className="mb-5 max-w-3xl text-sm text-ink-600">
        Every run is constrained by hard guardrails. The agent edits only
        allowlisted paths, never touches the protected default branch, must pass
        tests, and cannot open a pull request without explicit human approval.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        {SAFETY_CONTROLS.map((control, i) => {
          const Icon = CONTROL_ICONS[i] || ShieldCheck;
          return (
            <div
              key={control.title}
              className="flex gap-3 rounded-lg border border-ink-200 bg-white p-4"
            >
              <Icon className="mt-0.5 h-5 w-5 flex-shrink-0 text-emerald-600" />
              <div>
                <h3 className="text-sm font-semibold text-ink-900">
                  {control.title}
                </h3>
                <p className="mt-1 text-xs leading-relaxed text-ink-600">
                  {control.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        <PolicyList
          label="Allowlisted paths"
          tone="ok"
          items={ALLOWED_GLOBS}
        />
        <PolicyList label="Blocked paths" tone="block" items={BLOCKED_GLOBS} />
        <PolicyList
          label="Protected branches"
          tone="block"
          items={PROTECTED_BRANCHES}
        />
      </div>
    </section>
  );
}

function PolicyList({
  label,
  items,
  tone,
}: {
  label: string;
  items: string[];
  tone: "ok" | "block";
}) {
  const chip =
    tone === "ok"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : "border-rose-200 bg-rose-50 text-rose-700";
  return (
    <div className="rounded-lg border border-ink-200 bg-white p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
        {label}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item) => (
          <code
            key={item}
            className={`rounded border px-1.5 py-0.5 font-mono text-[11px] ${chip}`}
          >
            {item}
          </code>
        ))}
      </div>
    </div>
  );
}
