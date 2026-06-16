import { CheckCircle2, MinusCircle, XCircle } from "lucide-react";
import type { Run } from "@/types";

/** Test outcome panel for a run (pass / fail / not yet run). */
export default function TestResult({ run }: { run: Run }) {
  const passed = run.tests_passed;

  if (passed === null || passed === undefined) {
    return (
      <div
        className="flex items-center gap-2 rounded-lg border border-ink-200 bg-ink-50 px-4 py-3 text-sm text-ink-500"
        data-testid="test-result"
      >
        <MinusCircle className="h-5 w-5 text-ink-400" />
        Tests were not run for this run.
      </div>
    );
  }

  const tone = passed
    ? {
        wrap: "border-emerald-200 bg-emerald-50",
        text: "text-emerald-800",
        icon: <CheckCircle2 className="h-5 w-5 text-emerald-600" />,
        label: "Tests passed",
      }
    : {
        wrap: "border-rose-200 bg-rose-50",
        text: "text-rose-800",
        icon: <XCircle className="h-5 w-5 text-rose-600" />,
        label: "Tests failed",
      };

  return (
    <div
      className={`rounded-lg border ${tone.wrap} p-4`}
      data-testid="test-result"
    >
      <div className="flex items-center gap-2">
        {tone.icon}
        <span className={`text-sm font-semibold ${tone.text}`}>{tone.label}</span>
      </div>
      {run.test_output && (
        <pre className="mt-3 overflow-x-auto rounded bg-white/70 p-3 font-mono text-xs text-ink-700">
          {run.test_output}
        </pre>
      )}
    </div>
  );
}
