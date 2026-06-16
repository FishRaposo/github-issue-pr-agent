import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import DemoBadge, { DemoWriteNotice } from "@/components/DemoBadge";

describe("DemoBadge", () => {
  it("renders the demo-mode indicator", () => {
    render(<DemoBadge />);
    expect(screen.getByTestId("demo-badge")).toHaveTextContent("Demo mode");
  });

  it("renders the default write notice text", () => {
    render(<DemoWriteNotice />);
    expect(screen.getByTestId("demo-write-notice")).toHaveTextContent(
      /not persisted/i
    );
  });

  it("renders a custom write notice message", () => {
    render(<DemoWriteNotice message="simulated only" />);
    expect(screen.getByTestId("demo-write-notice")).toHaveTextContent(
      "simulated only"
    );
  });
});
