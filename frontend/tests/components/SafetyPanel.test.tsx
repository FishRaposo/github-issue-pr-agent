import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import SafetyPanel from "@/components/SafetyPanel";

describe("SafetyPanel", () => {
  it("renders the safety model heading", () => {
    render(<SafetyPanel />);
    expect(screen.getByText("Safety model")).toBeInTheDocument();
  });

  it("surfaces the four core controls", () => {
    render(<SafetyPanel />);
    expect(screen.getByText("Allowlisted paths only")).toBeInTheDocument();
    expect(screen.getByText("No-main guard")).toBeInTheDocument();
    expect(screen.getByText("Approval before PR")).toBeInTheDocument();
  });

  it("lists protected branches", () => {
    render(<SafetyPanel />);
    expect(screen.getByText("main")).toBeInTheDocument();
    expect(screen.getByText("master")).toBeInTheDocument();
  });
});
