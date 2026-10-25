import { test, expect } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "./connect-studio";

test("draft and run snapshot: divergence is shown, navigable and never changes the run", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  const project = await page.evaluate(async () => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const headers = {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    };
    let r = await fetch("/api/v1/projects", {
      method: "POST",
      headers,
      body: JSON.stringify({ name: "Draft and run overlay" }),
    });
    let project = await r.json();
    r = await fetch(`/api/v1/projects/${project.projectId}/edits`, {
      method: "POST",
      headers: { ...headers, "If-Match": String(project.revision) },
      body: JSON.stringify({
        baseRevision: project.revision,
        edits: [{ kind: "set_parameter", parameterId: "duration", value: 20 }],
      }),
    });
    project = await r.json();
    localStorage.setItem("studio.projectId", project.projectId);
    return project;
  });
  await page.reload();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start frozen snapshot", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /Run results/ }),
  ).toContainText("running", { timeout: 15000 });
  const runId = (await page.evaluate(() =>
    localStorage.getItem("studio.lastRun"),
  ))!;
  const run = await page.request
    .get(`/api/v1/runs/${runId}`)
    .then((r) => r.json());
  const snapshotFile = path.join(
      process.env.STUDIO_BROWSER_DATA!,
      "snapshots",
      run.snapshotId,
      "snapshot.json",
    ),
    sha = () =>
      createHash("sha256").update(readFileSync(snapshotFile)).digest("hex"),
    snapshotBefore = sha();
  const badge = page.locator(".divergence-badge");
  await expect(badge).toHaveText("Draft matches run inputs");
  // A parameter edit diverges the draft from the run's frozen inputs.
  await page.getByRole("tab", { name: /Model/ }).click();
  await page.getByRole("button", { name: "plant plant" }).click();
  await page.getByRole("button", { name: "Parameters", exact: true }).click();
  await page.getByLabel("Duration").fill("12");
  await page
    .getByLabel("Duration")
    .locator("xpath=ancestor::form")
    .getByRole("button", { name: "Apply", exact: true })
    .click();
  await expect(badge).toHaveText(
    "Draft differs from run inputs (1 document, 0 elements, 1 parameter)",
  );
  // Adding an instance marks it on the canvas and in the comparison.
  await page.getByRole("button", { name: "Add element", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog
    .getByRole("radiogroup", { name: "Definitions" })
    .getByRole("radio", {
      name: /reference-plant org\.xverse\.studio\.process-control/,
    })
    .check();
  await dialog.getByLabel("Instance identifier").fill("second-plant");
  await dialog.getByLabel("Placement node").selectOption("plant-node");
  await dialog.getByRole("button", { name: "Add instance" }).click();
  await expect(dialog).toHaveCount(0);
  await expect(badge).toHaveText(
    "Draft differs from run inputs (2 documents, 1 element, 1 parameter)",
  );
  await expect(
    page.locator(".element-node").filter({ hasText: "second-plant" }),
  ).toContainText("new in draft");
  await badge.click();
  await expect(badge).toHaveAttribute("aria-expanded", "true");
  const panel = page.getByRole("region", { name: "Draft and run snapshot" });
  await expect(panel).toContainText(run.snapshotId);
  await expect(panel).toContainText("duration: run 20 → draft 12");
  await expect(panel).toContainText("Run scenario parameters");
  await panel.getByRole("button", { name: "second-plant" }).click();
  await expect(
    page.locator(".inspector").getByRole("heading", { name: "second-plant" }),
  ).toBeVisible();
  await panel
    .getByRole("button", { name: "xdl/scenario.xdl.yaml (draft)" })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  // Undo both graph edits: same bytes as the snapshot, at a newer revision.
  const undo = page.getByRole("button", { name: "Undo", exact: true });
  await undo.click();
  await expect(badge).toHaveText(
    "Draft differs from run inputs (1 document, 0 elements, 1 parameter)",
  );
  await expect(undo).toBeEnabled();
  await undo.click();
  await expect(badge).toHaveText("Draft matches run inputs");
  await expect(panel).toContainText(
    "The revision numbers differ, but every run input matches the snapshot byte for byte.",
  );
  await expect(panel).toContainText(run.snapshotId);
  await panel
    .getByRole("button", { name: "Inspect frozen run inputs" })
    .click();
  const frozen = page.getByRole("dialog", {
    name: "Frozen run inputs · read-only",
  });
  await expect(frozen).toContainText("Project revision");
  await page.keyboard.press("Escape");
  await expect(frozen).toHaveCount(0);
  expect(sha()).toBe(snapshotBefore);
  const current = await page.request
    .get(`/api/v1/projects/${project.projectId}`)
    .then((r) => r.json());
  expect(current.revision).toBeGreaterThan(run.revision ?? project.revision);
  await page.screenshot({ path: testInfo.outputPath("run-overlay.png") });
  // Free the owned run slot for other checks.
  await page.getByRole("tab", { name: /Results/ }).click();
  await page.getByRole("button", { name: "Stop", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /Run results/ }),
  ).toContainText("stopped", { timeout: 15000 });
});
