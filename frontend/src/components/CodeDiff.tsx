import { FileCode2 } from "lucide-react";
import { computeDiff } from "@/lib/pipeline";

interface Props {
  filename: string;
  before: string;
  after: string;
}

/** Unified before/after diff for the agent's change to a single file. */
export default function CodeDiff({ filename, before, after }: Props) {
  const lines = computeDiff(before, after);
  const added = lines.filter((l) => l.type === "add").length;
  const removed = lines.filter((l) => l.type === "del").length;

  return (
    <div
      className="overflow-hidden rounded-lg border border-ink-200"
      data-testid="code-diff"
    >
      <div className="flex items-center justify-between border-b border-ink-200 bg-ink-50 px-3 py-2">
        <div className="flex items-center gap-2 text-sm font-medium text-ink-700">
          <FileCode2 className="h-4 w-4 text-ink-400" />
          <span className="font-mono">{filename}</span>
        </div>
        <div className="flex items-center gap-3 font-mono text-xs">
          <span className="text-emerald-600">+{added}</span>
          <span className="text-rose-600">−{removed}</span>
        </div>
      </div>
      <pre className="overflow-x-auto bg-ink-950 py-2 text-[13px] leading-relaxed">
        <code className="block font-mono">
          {lines.map((line, i) => {
            const base = "block px-3 whitespace-pre";
            if (line.type === "add") {
              return (
                <span key={i} className={`${base} bg-emerald-500/15 text-emerald-300`}>
                  <span className="select-none text-emerald-500/70">+ </span>
                  {line.text || " "}
                </span>
              );
            }
            if (line.type === "del") {
              return (
                <span key={i} className={`${base} bg-rose-500/15 text-rose-300`}>
                  <span className="select-none text-rose-500/70">- </span>
                  {line.text || " "}
                </span>
              );
            }
            return (
              <span key={i} className={`${base} text-ink-400`}>
                <span className="select-none text-ink-600">{"  "}</span>
                {line.text || " "}
              </span>
            );
          })}
        </code>
      </pre>
    </div>
  );
}
