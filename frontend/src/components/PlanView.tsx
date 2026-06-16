import ReactMarkdown from "react-markdown";
import { ClipboardList } from "lucide-react";

/**
 * Render the agent's generated plan. The backend stores it as plain text
 * (FixPlan.to_text); we present it as lightly-formatted markdown.
 */
export default function PlanView({ plan }: { plan: string | null }) {
  if (!plan) {
    return (
      <p className="text-sm text-ink-500" data-testid="plan-empty">
        No plan was generated for this run.
      </p>
    );
  }

  return (
    <div data-testid="plan-view">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink-700">
        <ClipboardList className="h-4 w-4 text-brand-600" />
        Generated plan
      </div>
      <div className="prose prose-sm max-w-none rounded-lg border border-ink-200 bg-ink-50/60 p-4 text-ink-700">
        <ReactMarkdown
          components={{
            p: ({ children }) => (
              <p className="my-1 whitespace-pre-wrap text-sm">{children}</p>
            ),
            ol: ({ children }) => (
              <ol className="my-1 list-decimal pl-5 text-sm">{children}</ol>
            ),
            li: ({ children }) => <li className="my-0.5">{children}</li>,
          }}
        >
          {plan}
        </ReactMarkdown>
      </div>
    </div>
  );
}
