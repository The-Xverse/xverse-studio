import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";

test("Actual Autoverse frozen rerun comparison exposes configuration and blocks unsupported numeric playback", async ({ page }, info) => {
  const recording = JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "comparison-recording.private.json"), "utf8"));
  await connectStudio(page, info);
  await page.evaluate((r) => {
    localStorage.setItem("studio.projectId", r.projectId);
    localStorage.setItem("studio.lastRun", r.runId);
    localStorage.setItem("studio.lastRun." + r.projectId, r.runId);
  }, recording);
  await page.reload();
  await page.getByRole("tab", { name: "Results", exact: true }).click();
  await expect(page.getByLabel("Recorded run", { exact: true })).toHaveValue(recording.runId);
  await expect(page.getByRole("heading", { name: new RegExp("Run results " + recording.selectedState) })).toBeVisible();
  for (const width of [1024, 1440]) {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await page.getByRole("tab", { name: "Compare", exact: true }).click();
    for (const [baseline, parameterStatus] of [[recording.sourceRunId, "same"], [recording.siblingRunId, "different"]]) {
      await page.getByLabel("Baseline run", { exact: true }).selectOption(baseline);
      await expect(page.getByRole("region", { name: "Recorded comparison report", exact: true })).toHaveCount(0);
      const inspect = page.getByRole("button", { name: "Inspect compatibility", exact: true });
      await inspect.focus(); await page.keyboard.press("Enter");
      const report = page.getByRole("region", { name: "Recorded comparison report", exact: true });
      await expect(report).toBeVisible();
      await expect(report).toContainText("Pairing blocked");
      await expect(report).toContainText(baseline);
      await expect(report).toContainText(recording.runId);
      await expect(report).toContainText(recording.snapshotId);
      await expect(report.getByRole("row").filter({ has: page.getByRole("rowheader", { name: new RegExp("^Parameters") }) })).toContainText(parameterStatus);
      await expect(report).toContainText("OBSERVATION_PAYLOAD_UNAVAILABLE");
      await expect(report).not.toContainText("Compatible recorded windows");
      await expect(report.getByRole("heading", { name: "Comparison report", exact: true })).toBeFocused();
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath(`actual-comparison-${width}.png`), fullPage: true });
    await page.getByRole("button", { name: "Open recorded playback", exact: true }).click();
    await expect(page.getByRole("tab", { name: "Observations", exact: true })).toHaveAttribute("aria-selected", "true");
    await expect(page.getByRole("button", { name: "Replay observations", exact: true })).toBeDisabled();
    await expect(page.getByRole("heading", { name: "No plot samples available", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Rerun frozen inputs", exact: true })).toBeEnabled();
  }
  // Labelled transport fixtures over the retained real operation and child.
  // The POST never reaches admission. Real operation reads and the final child
  // read retain their actual provider/scope and failed execution state.
  await page.getByLabel("Recorded run", { exact: true }).selectOption(recording.sourceRunId);
  const rerunUrl = `**/api/v1/runs/${recording.sourceRunId}/reruns`;
  const childUrl = `**/api/v1/runs/${recording.runId}`;
  const keys: string[] = [];
  await page.route(rerunUrl, async (route) => {
    keys.push(route.request().headers()["idempotency-key"]);
    await route.fulfill({ status: 202, contentType: "application/json", body: JSON.stringify({ operationId: recording.rerunOperationId }) });
  });
  await page.route(childUrl, async (route) => {
    const response = await route.fetch();
    await route.fulfill({ response, json: { ...(await response.json()), providerId: "unadmitted-other-provider" } });
  });
  await page.getByRole("button", { name: "Rerun frozen inputs", exact: true }).click();
  await expect(page.getByText("The acknowledged child does not match this rerun. Retry retains the same request key.", { exact: false })).toBeVisible();
  await expect(page.getByLabel("Recorded run", { exact: true })).toHaveValue(recording.sourceRunId);
  expect(await page.evaluate((id) => localStorage.getItem("studio.pendingRerun." + id), recording.sourceRunId)).toBe(keys[0]);
  await page.unroute(childUrl);
  await page.getByRole("button", { name: "Rerun frozen inputs", exact: true }).click();
  await expect(page.getByLabel("Recorded run", { exact: true })).toHaveValue(recording.runId);
  expect(keys).toHaveLength(2); expect(keys[0]).toBeTruthy(); expect(keys[1]).toBe(keys[0]);
  expect(await page.evaluate((id) => localStorage.getItem("studio.pendingRerun." + id), recording.sourceRunId)).toBeNull();
  await page.unroute(rerunUrl);
});
