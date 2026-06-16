import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import PlanView from "@/components/PlanView";
import { MOCK_RUNS } from "@/lib/mockData";

describe("PlanView", () => {
  it("renders the generated plan text", () => {
    render(<PlanView plan={MOCK_RUNS[0].plan} />);
    expect(screen.getByTestId("plan-view")).toBeInTheDocument();
    expect(screen.getByText(/Target file:/)).toBeInTheDocument();
  });

  it("renders an empty state when there is no plan", () => {
    render(<PlanView plan={null} />);
    expect(screen.getByTestId("plan-empty")).toBeInTheDocument();
  });
});
