import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import TestResult from "@/components/TestResult";
import { MOCK_RUNS } from "@/lib/mockData";

describe("TestResult", () => {
  it("renders a passing result with the summary line", () => {
    const passing = MOCK_RUNS.find((r) => r.tests_passed === true)!;
    render(<TestResult run={passing} />);
    expect(screen.getByText("Tests passed")).toBeInTheDocument();
    expect(screen.getByText(/passed in/)).toBeInTheDocument();
  });

  it("renders a failing result", () => {
    const failing = MOCK_RUNS.find((r) => r.tests_passed === false)!;
    render(<TestResult run={failing} />);
    expect(screen.getByText("Tests failed")).toBeInTheDocument();
  });

  it("handles runs where tests were not run", () => {
    const notRun = MOCK_RUNS.find((r) => r.tests_passed === null)!;
    render(<TestResult run={notRun} />);
    expect(screen.getByText(/not run/i)).toBeInTheDocument();
  });
});
