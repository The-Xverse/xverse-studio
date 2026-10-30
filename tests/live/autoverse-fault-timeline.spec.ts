import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
test("Actual Autoverse frozen fault timeline at both desktop sizes", async ({ page }, info) => {
  const data = JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "fault-authoring-project.private.json"), "utf8"));
  await connectStudio(page, info);
  await page.evaluate(p => { localStorage.setItem("studio.projectId", p.projectId); localStorage.setItem("studio.lastRun." + p.projectId, p._runId); }, data);
  await page.reload();
  await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  const draft = page.getByRole("table", { name: "Authored timeline entries", exact: true });
  await expect(draft.getByRole("row").filter({ hasText: "fault · first-loss" })).toContainText("5000 ms");
  await expect(draft.getByRole("row").filter({ hasText: "fault · first-loss" })).toContainText("Duration 3 s");
  await page.getByRole("tab", { name: "Timeline", exact: true }).click();
  const panel = page.getByRole("region", { name: "Selected run timeline", exact: true });
  for (const width of [1024, 1440]) {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await panel.getByRole("button", { name: "Inspect selected run timeline", exact: true }).click();
    await expect(panel.getByText("actual-running-transition", { exact: true })).toBeVisible();
    await expect(panel.getByText("autoverse.host-elapsed-microseconds.v1", { exact: true })).toBeVisible();
    await expect(panel.getByRole("img")).toBeVisible();
    await expect(panel).toContainText("fault.activation_observed");
    await expect(panel).toContainText("fault.recovery_observed");
    await expect(panel).toContainText("fault.interrupted");
    await expect(panel).toContainText("5000000");
    await page.screenshot({ path: info.outputPath(`fault-timeline-${width}.png`), fullPage: true });
  }
  const report = await page.request.get(`/api/v1/runs/${data._runId}/timeline?formatVersion=1.1&snapshotId=${data._snapshotId}&limit=200`).then(r => r.json());
  expect(report.counts.unplacedRows).toBeGreaterThan(0);
  expect(report.recorded.coverage).toBe("not_attested_by_timeline");
  await info.attach("actual-fault-timeline", { body: JSON.stringify({ runId: data._runId, snapshotId: data._snapshotId, viewports: [1024, 1440], canonicalIntegrity: report.recorded.integrity, unknownTelemetryRemainsUnplaced: true }), contentType: "application/json" });
});
