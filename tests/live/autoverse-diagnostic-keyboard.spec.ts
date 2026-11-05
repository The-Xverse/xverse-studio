import { test, expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
import { renderedContrast } from "../e2e/contrast";

const recording = () => JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "playback-recording.private.json"), "utf8"));
const diagnosis = (page: Page) => page.getByRole("region", { name: "Run diagnosis", exact: true });

async function activate(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let step = 0; step < 600; step++) {
    if (await target.evaluate(node => node === document.activeElement)) {
      await page.keyboard.press("Enter");
      return;
    }
    await page.keyboard.press("Tab");
  }
  throw new Error("Required diagnostic action is unreachable through native Tab order");
}

async function open(page: Page, info: TestInfo, width: number) {
  const source = recording();
  await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  await connectStudio(page, info);
  await page.evaluate(r => {
    localStorage.setItem("studio.lastRun", r.runId);
    localStorage.setItem("studio.lastRun." + r.projectId, r.runId);
  }, source);
  await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
  const project = await page.request.get(`/api/v1/projects/${source.projectId}`);
  expect(project.status()).toBe(200);
  await activate(page, page.locator(".project-list").getByRole("button").filter({ hasText: (await project.json()).name }));
  await activate(page, page.getByRole("tab", { name: /^Results(?:\s+\d+)?$/ }));
  await expect(page.getByLabel("Recorded run", { exact: true })).toHaveValue(source.runId);
  return source;
}

async function loaded(page: Page) {
  const panel = diagnosis(page);
  await expect(panel).toHaveAttribute("data-explanation-state", "loaded");
  await expect(panel.locator('[data-diagnostic-class="incompatible_time_mapping"]')).toContainText("TIME_MAPPING_INCOMPATIBLE");
  return panel;
}

for (const width of [1024, 1440]) {
  test(`actual Autoverse diagnosis preserves facts and keyboard evidence navigation at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [];
    page.on("request", request => { if (request.method() !== "GET") writes.push(new URL(request.url()).pathname); });
    const reply = page.waitForResponse(response => new URL(response.url()).pathname === `/api/v1/runs/${source.runId}/diagnostics`);
    await activate(page, page.getByRole("tab", { name: "Diagnosis", exact: true }));
    const response = await reply;
    expect(response.status()).toBe(200);
    const original = await response.json(), panel = await loaded(page);
    expect(original.findings.length).toBeGreaterThan(0);
    await expect(panel.locator("article.diagnostic-finding")).toHaveCount(original.findings.length);
    for (let i = 0; i < original.findings.length; i++) {
      const finding = original.findings[i], row = panel.locator("article.diagnostic-finding").nth(i);
      await expect(row.getByRole("heading", { name: finding.title, exact: true })).toBeVisible();
      await expect(row.locator("header code")).toHaveText(finding.code);
      await expect(row.locator(".badge")).toHaveText(finding.severity);
      for (const fact of finding.facts) await expect(row.locator(".diagnostic-facts")).toContainText(fact.statement);
      for (const unknown of finding.unknowns) await expect(row).toContainText(unknown);
    }
    const clock = panel.locator('[data-diagnostic-class="incompatible_time_mapping"]');
    await expect(clock).toContainText("21 observation(s) carry no source time.");
    const contrast = [
      await renderedContrast(clock.getByRole("heading", { level: 4 }), "Actual clock diagnostic title"),
      await renderedContrast(clock.locator(".badge"), "Actual clock diagnostic severity"),
      await renderedContrast(clock.locator(".diagnostic-evidence li").first(), "Original event reference"),
    ];
    for (const pair of contrast) {
      expect(pair.supported).toBe(true);
      if (pair.supported) expect(pair.ratio).toBeGreaterThanOrEqual(4.5);
    }
    await activate(page, clock.getByRole("button", { name: "Inspect the referenced retained events and logs.", exact: true }));
    const events = page.getByRole("tab", { name: /^Events & logs/ });
    await expect(events).toHaveAttribute("aria-selected", "true");
    await expect(events).toBeFocused();
    expect(await events.evaluate(node => { const s = getComputedStyle(node); return s.outlineStyle !== "none" && parseFloat(s.outlineWidth) >= 2; })).toBe(true);
    await activate(page, page.getByRole("tab", { name: "Diagnosis", exact: true }));
    await loaded(page);
    expect(writes).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await info.attach("actual-diagnosis-keyboard.json", { body: JSON.stringify({ width, runId: source.runId, findings: original.findings.map((f: any) => ({ class: f.class, code: f.code })), contrast, writes, browser: await page.context().browser()?.version(), scope: "Original Autoverse recording; keyboard and selected text contrast, no assistive-technology certification" }), contentType: "application/json" });
  });

  test(`diagnostic read failure has a keyboard retry with stable focus at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [];
    page.on("request", request => { if (request.method() !== "GET") writes.push(new URL(request.url()).pathname); });
    let attempts = 0;
    await page.route(`**/api/v1/runs/${source.runId}/diagnostics`, async route => {
      attempts++;
      if (attempts === 1) await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ code: "READER_UNAVAILABLE", message: "Labelled diagnostic reader-response fixture" }) });
      else await route.continue();
    });
    await activate(page, page.getByRole("tab", { name: "Diagnosis", exact: true }));
    const panel = diagnosis(page);
    await expect(panel).toHaveAttribute("data-explanation-state", "unavailable");
    await expect(panel.getByRole("alert")).toContainText("Labelled diagnostic reader-response fixture");
    expect(attempts).toBe(1);
    const retryReply = page.waitForResponse(response => new URL(response.url()).pathname === `/api/v1/runs/${source.runId}/diagnostics`);
    await activate(page, panel.getByRole("button", { name: "Retry explanation", exact: true }));
    expect((await retryReply).status()).toBe(200);
    await loaded(page);
    const refresh = panel.getByRole("button", { name: "Refresh explanation", exact: true });
    await expect(refresh).toBeFocused();
    await expect(panel.getByRole("alert")).toHaveCount(0);
    expect(attempts).toBe(2);
    const refreshReply = page.waitForResponse(response => new URL(response.url()).pathname === `/api/v1/runs/${source.runId}/diagnostics`);
    await page.keyboard.press("Enter");
    expect((await refreshReply).status()).toBe(200);
    await expect.poll(() => attempts).toBe(3);
    await loaded(page);
    await expect(refresh).toBeFocused();
    expect(writes).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await info.attach("diagnostic-retry.json", { body: JSON.stringify({ width, attempts, writes, stableFocus: true, scope: "One labelled HTTP503 then actual original Autoverse diagnosis; no provider/device failure claim" }), contentType: "application/json" });
  });

  test(`a delayed diagnostic refresh preserves newer keyboard focus at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width);
    await activate(page, page.getByRole("tab", { name: "Diagnosis", exact: true }));
    const panel = await loaded(page), writes: string[] = [];
    page.on("request", request => { if (request.method() !== "GET") writes.push(new URL(request.url()).pathname); });
    let release!: () => void, captured!: () => void;
    const held = new Promise<void>(resolve => release = resolve), ready = new Promise<void>(resolve => captured = resolve);
    await page.route(`**/api/v1/runs/${source.runId}/diagnostics`, async route => {
      const response = await route.fetch();
      captured();
      await held;
      await route.fulfill({ response });
    });
    try {
      await activate(page, panel.getByRole("button", { name: "Refresh explanation", exact: true }));
      await ready;
      await page.keyboard.press("Tab");
      const newer = await page.evaluateHandle(() => document.activeElement);
      expect(await newer.evaluate(node => node?.tagName)).toBe("BUTTON");
      expect(await newer.evaluate(node => node?.textContent)).toBe("Inspect the referenced retained events and logs.");
      const reply = page.waitForResponse(response => new URL(response.url()).pathname === `/api/v1/runs/${source.runId}/diagnostics`);
      release();
      expect((await reply).status()).toBe(200);
      await loaded(page);
      expect(await newer.evaluate(node => node === document.activeElement)).toBe(true);
      expect(writes).toEqual([]);
      await info.attach("newer-diagnostic-focus.json", { body: JSON.stringify({ width, newerFocusPreserved: true, writes, scope: "Delayed actual HTTP200 response; no provider/device failure claim" }), contentType: "application/json" });
    } finally {
      release();
      await page.unrouteAll({ behavior: "wait" });
    }
  });
}
