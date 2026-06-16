import {
  Ban,
  Check,
  CircleDashed,
  Loader2,
  X,
} from "lucide-react";
import type { Run } from "@/types";
import { derivePipeline, type StageState } from "@/lib/pipeline";

const STATE_STYLES: Record<
  StageState,
  { dot: string; line: string; label: string }
> = {
  done: {
    dot: "bg-emerald-500 text-white border-emerald-500",
    line: "bg-emerald-300",
    label: "text-ink-900",
  },
  active: {
    dot: "bg-amber-500 text-white border-amber-500 ring-4 ring-amber-100",
    line: "bg-ink-200",
    label: "text-ink-900",
  },
  pending: {
    dot: "bg-white text-ink-400 border-ink-300",
    line: "bg-ink-200",
    label: "text-ink-400",
  },
  failed: {
    dot: "bg-rose-500 text-white border-rose-500",
    line: "bg-ink-200",
    label: "text-ink-900",
  },
  blocked: {
    dot: "bg-rose-100 text-rose-600 border-rose-300",
    line: "bg-ink-200",
    label: "text-rose-700",
  },
};

function StageIcon({ state }: { state: StageState }) {
  if (state === "done") return <Check className="h-4 w-4" />;
  if (state === "active") return <Loader2 className="h-4 w-4 animate-spin" />;
  if (state === "failed") return <X className="h-4 w-4" />;
  if (state === "blocked") return <Ban className="h-4 w-4" />;
  return <CircleDashed className="h-4 w-4" />;
}

/** Horizontal-on-desktop / vertical-on-mobile pipeline timeline for a run. */
export default function PipelineTimeline({ run }: { run: Run }) {
  const stages = derivePipeline(run);

  return (
    <div data-testid="pipeline-timeline">
      {/* Desktop: horizontal stepper */}
      <ol className="hidden items-start md:flex">
        {stages.map((stage, i) => {
          const style = STATE_STYLES[stage.state];
          const last = i === stages.length - 1;
          return (
            <li key={stage.key} className="relative flex-1">
              <div className="flex items-center">
                <span
                  className={`z-10 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 ${style.dot}`}
                >
                  <StageIcon state={stage.state} />
                </span>
                {!last && (
                  <span className={`h-0.5 w-full flex-1 ${style.line}`} />
                )}
              </div>
              <div className="mt-2 pr-3">
                <p className={`text-sm font-semibold ${style.label}`}>
                  {stage.label}
                </p>
                <p className="mt-0.5 text-xs leading-snug text-ink-500">
                  {stage.description}
                </p>
              </div>
            </li>
          );
        })}
      </ol>

      {/* Mobile: vertical stepper */}
      <ol className="space-y-1 md:hidden">
        {stages.map((stage, i) => {
          const style = STATE_STYLES[stage.state];
          const last = i === stages.length - 1;
          return (
            <li key={stage.key} className="flex gap-3">
              <div className="flex flex-col items-center">
                <span
                  className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 ${style.dot}`}
                >
                  <StageIcon state={stage.state} />
                </span>
                {!last && <span className={`my-1 w-0.5 flex-1 ${style.line}`} />}
              </div>
              <div className="pb-3">
                <p className={`text-sm font-semibold ${style.label}`}>
                  {stage.label}
                </p>
                <p className="text-xs text-ink-500">{stage.description}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
