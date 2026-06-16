import type { ReactNode } from "react";
import { Inbox } from "lucide-react";

interface Props {
  title: string;
  message?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

/** A standard empty-state panel for data views with no results. */
export default function EmptyState({ title, message, icon, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-ink-300 bg-ink-50/50 p-12 text-center">
      <div className="mb-3 text-ink-400">{icon || <Inbox className="h-9 w-9" />}</div>
      <h3 className="mb-1 text-base font-semibold text-ink-700">{title}</h3>
      {message && <p className="mb-4 max-w-md text-sm text-ink-500">{message}</p>}
      {action}
    </div>
  );
}
