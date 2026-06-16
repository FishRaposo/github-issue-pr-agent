import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import ApprovalGate from "@/components/ApprovalGate";
import { MOCK_RUNS } from "@/lib/mockData";

describe("ApprovalGate", () => {
  beforeEach(() => {
    // Force the network to fail so the client falls back to demo mode.
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new Error("offline")))
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows the approve action for an awaiting-approval run", () => {
    const awaiting = MOCK_RUNS.find((r) => r.status === "awaiting_approval")!;
    render(<ApprovalGate run={awaiting} />);
    expect(screen.getByTestId("approval-gate")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /approve & open draft pr/i })
    ).toBeInTheDocument();
  });

  it("approves in demo mode and shows the not-persisted notice", async () => {
    const awaiting = MOCK_RUNS.find((r) => r.status === "awaiting_approval")!;
    render(<ApprovalGate run={awaiting} />);

    const button = screen.getByRole("button", {
      name: /approve & open draft pr/i,
    });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByTestId("demo-write-notice")).toBeInTheDocument();
    });
    expect(screen.getByText(/draft pull request opened/i)).toBeInTheDocument();
  });

  it("shows a completed state with a PR link for a completed run", () => {
    const completed = MOCK_RUNS.find((r) => r.status === "completed")!;
    render(<ApprovalGate run={completed} />);
    expect(screen.getByText(/draft pull request opened/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view draft pr/i })).toHaveAttribute(
      "href",
      completed.pr_url!
    );
  });
});
