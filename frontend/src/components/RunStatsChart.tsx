"use client";

import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Run } from "@/types";
import { statusMeta } from "@/lib/format";

const ORDER = [
  "pending",
  "planned",
  "awaiting_approval",
  "approved",
  "completed",
  "failed",
];

const BAR_COLORS: Record<string, string> = {
  pending: "#94a3b8",
  planned: "#6366f1",
  awaiting_approval: "#f59e0b",
  approved: "#0ea5e9",
  completed: "#10b981",
  failed: "#f43f5e",
};

/** Small bar chart of runs grouped by status. */
export default function RunStatsChart({ runs }: { runs: Run[] }) {
  const counts = runs.reduce<Record<string, number>>((acc, r) => {
    acc[r.status] = (acc[r.status] || 0) + 1;
    return acc;
  }, {});

  const data = ORDER.filter((s) => counts[s]).map((s) => ({
    status: s,
    label: statusMeta(s).label,
    count: counts[s],
  }));

  if (data.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-ink-500">
        No runs to chart yet.
      </p>
    );
  }

  return (
    <div className="h-48 w-full" data-testid="run-stats-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -20 }}>
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "#64748b" }}
            interval={0}
            angle={-12}
            textAnchor="end"
            height={48}
          />
          <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#64748b" }} />
          <Tooltip
            cursor={{ fill: "rgba(99,102,241,0.06)" }}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #e2e8f0",
              fontSize: 12,
            }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.status} fill={BAR_COLORS[d.status] || "#6366f1"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
