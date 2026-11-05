import { test, expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
import { renderedContrast } from "../e2e/contrast";

const recording = () => JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "campaign-recording.private.json"), "utf8"));
const history = (page: Page) => page.getByRole("region", { name: "Retained campaign history", exact: true });
const selected = (page: Page) => page.getByRole("region", { name: "Selected campaign", exact: true });
async function activate(page: Page, target: Locator, pressEnter = true) {
  await expect(target).toBeVisible();
  for (let count = 0; count < 600; count++) {
    if (await target.evaluate(n => n === document.activeElement)) {
      expect(await target.evaluate(n => {
        const r = n.getBoundingClientRect(), s = getComputedStyle(n);
        return r.left >= 0 && r.right <= innerWidth + 1 && r.top >= 0 && r.bottom <= innerHeight + 1 &&
          s.outlineStyle !== "none" && parseFloat(s.outlineWidth) >= 2;
      })).toBe(true);
      if (pressEnter) await page.keyboard.press("Enter");
      return;
    }
    await page.keyboard.press("Tab");
  }
  throw Error("Required campaign action is unreachable through native Tab order");
}
async function open(page: Page, info: TestInfo, width: number) {
  await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  await connectStudio(page, info);
  await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
  const response = await page.request.get(`/api/v1/projects/${recording().projectId}`);
  expect(response.status()).toBe(200);
  const project = await response.json();
  await activate(page, page.locator(".project-list").getByRole("button").filter({ hasText: project.name }));
  await activate(page, page.getByRole("tab", { name: "Experiments", exact: true }));
  await activate(page, page.getByRole("tab", { name: "Campaigns", exact: true }));
  await activate(page, history(page).getByRole("button", { name: "Refresh campaign history", exact: true }));
  await expect(history(page).getByRole("heading", { name: "Campaign history", exact: true })).toBeFocused();
  await activate(page, history(page).getByRole("button", { name: `Inspect campaign ${recording().campaignId}`, exact: true }));
  await expect(selected(page).getByRole("heading", { name: "Selected campaign", exact: true })).toBeFocused();
  return recording();
}
async function inspect(page: Page, child: any) {
  await activate(page, selected(page).getByRole("button", { name: `Inspect child inputs ${child.runId}`, exact: true }));
  const heading = selected(page).getByRole("heading", { name: "Verified child inputs", exact: true });
  await expect(heading).toBeVisible();
  await expect(heading.locator("..")).toContainText(child.runId);
  await expect(heading.locator("..")).toContainText(child.snapshotId);
  return heading;
}
async function report(page: Page, info: TestInfo, width: number, writes: string[], fixture: string | null) {
  expect(writes).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await info.attach("retained-campaign-keyboard.json", { body: JSON.stringify({
    width, writes, browser: await page.context().browser()?.version(), fixture,
    scope: "Actual completed Autoverse campaign and immutable children on a private copy; no fresh provider/preflight/execution or assistive-technology certification",
  }), contentType: "application/json" });
}

for (const width of [1024, 1440]) {
  test(`a delayed child read preserves moved keyboard focus at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), child = source.children[0], writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    let release!: () => void, observed!: () => void;
    const gate = new Promise<void>(r => { release = r; });
    const fetched = new Promise<void>(r => { observed = r; });
    await page.route(`**/api/v1/runs/${child.runId}/snapshot`, async route => {
      const response = await route.fetch();
      observed();
      await gate;
      await route.fulfill({ response });
    }, { times: 1 });
    try {
      await activate(page, selected(page).getByRole("button", { name: `Inspect child inputs ${child.runId}`, exact: true }));
      await fetched;
      const newer = history(page).getByRole("button", { name: "Refresh campaign history", exact: true });
      await activate(page, newer, false);
      release();
      await expect(selected(page).getByRole("heading", { name: "Verified child inputs", exact: true })).toBeVisible();
      await expect(newer).toBeFocused();
      await report(page, info, width, writes, "Actual child snapshot reply held until keyboard focus moves; response unchanged");
    } finally { release(); }
  });

  test(`native keyboard retained campaign and verified child inputs at ${width}`, async ({ page }, info) => {
    const writes: string[] = [];
    await connectStudio(page, info);
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    const source = await open(page, info, width);
    const planning = page.getByRole("region", { name: "Campaign planning", exact: true });
    await expect(planning).toContainText("A ready preflight");
    await expect(planning.getByRole("button", { name: "Preview campaign", exact: true })).toBeDisabled();
    await expect(planning.getByRole("button", { name: "Create campaign", exact: true })).toBeDisabled();
    await expect(selected(page)).toContainText(source.baseSnapshotId);
    await expect(selected(page)).toContainText("complete");
    for (const child of source.children) {
      const heading = await inspect(page, child);
      await expect(heading).toBeFocused();
      const contrast = await renderedContrast(heading, "Verified frozen child inputs heading");
      expect(contrast.supported).toBe(true);
      if (contrast.supported) expect(contrast.ratio).toBeGreaterThanOrEqual(4.5);
    }
    await report(page, info, width, writes, null);
  });

  test(`successful child inspection avoids an older history error at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    await page.route("**/api/v1/campaigns?**", route => route.fulfill({ status: 503, json: {
      code: "KEYBOARD_HISTORY_FIXTURE", message: "Labelled history transport failure", retryable: true,
    } }), { times: 1 });
    await activate(page, history(page).getByRole("button", { name: "Refresh campaign history", exact: true }));
    const error = page.getByRole("alert");
    await expect(error).toContainText("KEYBOARD_HISTORY_FIXTURE");
    await expect(error).toBeFocused();
    const heading = await inspect(page, source.children[0]);
    await expect(heading).toBeFocused();
    await expect(error).toContainText("Previous displayed observations have not been refreshed");
    await activate(page, history(page).getByRole("button", { name: "Refresh campaign history", exact: true }));
    await expect(history(page).getByRole("heading", { name: "Campaign history", exact: true })).toBeFocused();
    await expect(error).toHaveCount(0);
    await report(page, info, width, writes, "One labelled503 history response; all campaign/child data are actual retained reads");
  });

  test(`native keyboard child identity refusal and actual retry at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), child = source.children[0], writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    await page.route(`**/api/v1/runs/${child.runId}/snapshot`, async route => {
      const response = await route.fetch(), value = await response.json();
      value.snapshot.campaignChildKey = "labelled-mismatched-child";
      await route.fulfill({ response, json: value });
    }, { times: 1 });
    const button = selected(page).getByRole("button", { name: `Inspect child inputs ${child.runId}`, exact: true });
    await activate(page, button);
    await expect(page.getByRole("alert")).toContainText("immutable child input identities do not match");
    await expect(page.getByRole("alert")).toBeFocused();
    await expect(selected(page).getByRole("heading", { name: "Verified child inputs", exact: true })).toHaveCount(0);
    const heading = await inspect(page, child);
    await expect(heading).toBeFocused();
    await expect(page.getByRole("alert")).toHaveCount(0);
    await report(page, info, width, writes, "One labelled post-read campaignChildKey mismatch; actual unmodified retry");
  });
}
