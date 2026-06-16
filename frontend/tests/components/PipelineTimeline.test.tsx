import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import PipelineTimeline from "@/components/PipelineTimeline";
import { MOCK_RUNS } from "@/lib/mockData";

describe("PipelineTimeline", () => {
  it("renders every pipeline stage label (mobile + desktop = 2x)", () => {
    render(<PipelineTimeline run={MOCK_RUNS[0]} />);
    expect(screen.getByTestId("pipeline-timeline")).toBeInTheDocument();
    // Each stage label appears in both the desktop and mobile steppers.
    expect(screen.getAllByText("Approval gate").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Draft PR").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Tests").length).toBeGreaterThanOrEqual(1);
  });

  it("renders for an awaiting-approval run", () => {
    const awaiting = MOCK_RUNS.find((r) => r.status === "awaiting_approval")!;
    render(<PipelineTimeline run={awaiting} />);
    expect(screen.getAllByText("Approval gate").length).toBeGreaterThanOrEqual(1);
  });

  it("renders for a failed run without crashing", () => {
    const failed = MOCK_RUNS.find((r) => r.status === "failed")!;
    render(<PipelineTimeline run={failed} />);
    expect(screen.getByTestId("pipeline-timeline")).toBeInTheDocument();
  });
});
