import { test, expect } from "@playwright/test";

// Smoke test over the demo-mode UI. The dashboard is live-first but falls back
// to bundled mock data when no backend is running, so these assertions hold even
// with the FastAPI service down.

test("overview page loads with the safety model", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Issue → PR Console/i);
  await expect(
    page.getByRole("heading", { name: /turn github issues into reviewed draft prs/i })
  ).toBeVisible();
  await expect(page.getByText("Safety model")).toBeVisible();
});

test("runs list renders and links to a run detail", async ({ page }) => {
  await page.goto("/runs");
  await expect(page.getByRole("heading", { name: "Runs" })).toBeVisible();

  const firstRun = page.getByTestId("run-list").locator("a").first();
  await expect(firstRun).toBeVisible();
  await firstRun.click();

  // Run detail shows the pipeline timeline and an audit trail. Allow extra time
  // for the live-first fetch to fall back to demo data when no backend is up.
  await expect(page.getByTestId("pipeline-timeline")).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByText("Audit trail")).toBeVisible();
});

test("audit log page renders the timeline", async ({ page }) => {
  await page.goto("/audit");
  await expect(page.getByRole("heading", { name: /audit log/i })).toBeVisible();
  await expect(page.getByTestId("audit-timeline")).toBeVisible();
});

test("process page can run a pipeline in demo mode", async ({ page }) => {
  await page.goto("/process");
  await page.getByLabel("Issue number").fill("101");
  await page.getByRole("button", { name: /run agent pipeline/i }).click();
  await expect(page.getByTestId("pipeline-timeline")).toBeVisible();
});
