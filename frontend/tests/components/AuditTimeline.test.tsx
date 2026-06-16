import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import AuditTimeline from "@/components/AuditTimeline";
import { MOCK_AUDIT } from "@/lib/mockData";

describe("AuditTimeline", () => {
  it("renders audit entries with action labels", () => {
    render(<AuditTimeline entries={MOCK_AUDIT.slice(0, 5)} />);
    expect(screen.getByTestId("audit-timeline")).toBeInTheDocument();
    expect(screen.getAllByText("Run started").length).toBeGreaterThanOrEqual(1);
  });

  it("labels human vs agent actors", () => {
    const withHuman = MOCK_AUDIT.filter((e) => e.actor === "human");
    render(<AuditTimeline entries={withHuman} />);
    expect(screen.getAllByText("human").length).toBeGreaterThanOrEqual(1);
  });

  it("renders an empty list without crashing", () => {
    render(<AuditTimeline entries={[]} />);
    expect(screen.getByTestId("audit-timeline")).toBeInTheDocument();
  });
});
