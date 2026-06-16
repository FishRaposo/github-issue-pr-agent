import { statusMeta } from "@/lib/format";

export default function StatusBadge({ status }: { status: string }) {
  const meta = statusMeta(status);
  return (
    <span className={`badge ${meta.badge}`} data-testid="status-badge">
      {meta.label}
    </span>
  );
}
