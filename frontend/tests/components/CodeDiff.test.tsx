import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import CodeDiff from "@/components/CodeDiff";
import { DEMO_DIFF_AFTER, DEMO_DIFF_BEFORE } from "@/lib/mockData";

describe("CodeDiff", () => {
  it("renders the filename and the added guard lines", () => {
    render(
      <CodeDiff
        filename="calculator.py"
        before={DEMO_DIFF_BEFORE}
        after={DEMO_DIFF_AFTER}
      />
    );
    expect(screen.getByTestId("code-diff")).toBeInTheDocument();
    expect(screen.getByText("calculator.py")).toBeInTheDocument();
    // The fix adds a zero guard — these lines should appear as additions.
    expect(screen.getByText(/if b == 0:/)).toBeInTheDocument();
    expect(screen.getByText(/return None/)).toBeInTheDocument();
  });

  it("shows non-zero add/remove counts", () => {
    render(
      <CodeDiff
        filename="calculator.py"
        before={DEMO_DIFF_BEFORE}
        after={DEMO_DIFF_AFTER}
      />
    );
    expect(screen.getByText(/^\+\d+$/)).toBeInTheDocument();
  });
});
