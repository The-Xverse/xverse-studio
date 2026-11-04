import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";

test("Actual Autoverse campaign history and admitted duration preview preserve frozen children", async ({ page }, info) => {
  const recording = JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "campaign-recording.private.json"), "utf8"));
  await connectStudio(page, info);
  await page.evaluate((r) => {
    localStorage.setItem("studio.projectId", r.projectId);
    localStorage.setItem("studio.lastRun." + r.projectId, r.children[1].runId);
  }, recording);
  await page.reload();
  await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  await page.getByRole("tab", { name: "Campaigns", exact: true }).click();
  await page.getByRole("button", { name: "Preflight & run", exact: true }).click();
  await expect(page.getByRole("button", { name: "Start frozen snapshot", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Back to draft", exact: true }).click();
  const planning = page.getByRole("region", { name: "Campaign planning", exact: true });
  await expect(planning).toContainText("durationSeconds: 30–1800 s");
  await expect(planning).toContainText("Applied seeds are unavailable");
  for (const width of [1024, 1440]) {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await planning.getByRole("button", { name: "Use admitted parameter example", exact: true }).click();
    expect(JSON.parse(await planning.getByLabel("Parameter matrix (JSON)").inputValue())).toEqual({ durationSeconds: [30] });
    await planning.getByLabel("Parameter matrix (JSON)").fill('{"durationSeconds":[30,31]}');
    await planning.getByLabel("Maximum runs", { exact: true }).fill("2");
    await planning.getByLabel("Maximum total declared seconds", { exact: true }).fill("62");
    await planning.getByRole("button", { name: "Preview campaign", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Authoritative campaign preview", exact: true })).toBeVisible();
    await expect(planning).toContainText("Estimated total declared seconds");
    await expect(planning).not.toContainText("simulated seconds");
    const history = page.getByRole("region", { name: "Retained campaign history", exact: true });
    await history.getByRole("button", { name: "Refresh campaign history", exact: true }).click();
    const row = history.getByRole("listitem").filter({ hasText: recording.campaignId });
    await expect(row).toBeVisible();
    await row.getByRole("button").click();
    const selected = page.getByRole("region", { name: "Selected campaign", exact: true });
    await expect(selected).toContainText(recording.baseSnapshotId);
    await expect(selected).toContainText("different frozen project or revision");
    for (const child of recording.children) {
      await expect(selected).toContainText(child.childKey);
      const inspect = selected.getByRole("button", { name: `Inspect child inputs ${child.runId}`, exact: true });
      await inspect.focus(); await page.keyboard.press("Enter");
      const inputs = selected.getByRole("heading", { name: "Verified child inputs", exact: true }).locator("..");
      await expect(inputs).toContainText(child.runId);
      await expect(inputs).toContainText(child.snapshotId);
      await expect(inputs).toContainText("durationSeconds");
      await expect(selected.getByText("Reading immutable child inputs…", { exact: true })).toHaveCount(0);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath(`actual-campaign-${width}.png`), fullPage: true });
  }
});
