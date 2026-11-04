import { test, expect, type Locator, type Page } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
import { beginPresentationProbe, endPresentationProbe } from "../performance/presentation-probe";

const p95 = (samples: number[]) => [...samples].sort((a, b) => a - b)[Math.ceil(samples.length * .95) - 1];
const painted = (page: Page) => page.evaluate(() => new Promise<number>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve(performance.now())))));
async function activateByTab(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let index = 0; index < 600; index++) {
    if (await target.evaluate((e) => e === document.activeElement)) {
      await page.keyboard.press("Enter");
      return;
    }
    await page.keyboard.press("Tab");
  }
  throw new Error("Declared keyboard alternative is unreachable through Tab order");
}
async function noOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
}

test("Autoverse authoring and synthetic retained history meet the declared native budgets", async ({ page }, info) => {
  const context = JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "performance-context.private.json"), "utf8"));
  await connectStudio(page, info);
  const writes: string[] = [];
  page.on("request", (r) => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
  for (const width of [1024, 1440]) {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await page.evaluate((id) => { localStorage.setItem("studio.projectId", id); localStorage.removeItem("studio.lastRun"); }, context.model.projectId);
    await page.reload();
    await expect(page.locator(".tree-list button")).toHaveCount(200);
    await expect(page.locator(".react-flow__node-element")).toHaveCount(200);
    await expect(page.locator(".react-flow__edge")).toHaveCount(400);
    const opens: number[] = [], selections: number[] = [], diagnostics: any[] = [];
    let openWarmup = 0, selectionWarmup = 0;
    for (let repeat = -1; repeat < 30; repeat++) {
      await page.getByRole("button", { name: "X-Verse Studio home", exact: true }).click();
      await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
      const begin = await page.evaluate(() => performance.now());
      await beginPresentationProbe(page, context.model.projectId, begin);
      const loaded = page.waitForResponse((r) => new URL(r.url()).pathname === `/api/v1/projects/${context.model.projectId}` && r.request().method() === "GET");
      await page.locator(".project-list").getByRole("button").filter({ hasText: context.model.projectName }).click();
      expect((await loaded).status()).toBe(200);
      await expect(page.locator(".tree-list button")).toHaveCount(200);
      await expect(page.locator(".react-flow__node-element")).toHaveCount(200);
      await expect(page.locator(".react-flow__edge")).toHaveCount(400);
      const checked = page.waitForResponse((r) => new URL(r.url()).pathname === `/api/v1/projects/${context.model.projectId}/validations` && r.request().method() === "POST");
      await page.getByRole("button", { name: "Validate", exact: true }).click();
      const validation = await checked;
      expect(validation.status()).toBe(200);
      expect((await validation.json()).valid).toBe(true);
      await expect(page.locator(".alerts")).toContainText("Authoritative platform validation passed");
      const driverEnd = await painted(page);
      const openElapsed = driverEnd - begin;
      diagnostics.push(await endPresentationProbe(page, driverEnd));
      const id = context.model.selectionIds[repeat + 1];
      const elapsed = await page.evaluate((id) => {
        const button = [...document.querySelectorAll<HTMLButtonElement>(".tree-list button")].find((b) => b.querySelector("span")?.textContent === id);
        if (!button) throw new Error("Missing declared benchmark element");
        const start = performance.now();
        button.click();
        return new Promise<number>((resolve, reject) => {
          const committed = () => {
            if (document.querySelector(".inspector-summary h3")?.textContent === id) {
              requestAnimationFrame(() => requestAnimationFrame(() => resolve(performance.now() - start)));
            } else if (performance.now() - start > 3000) reject(new Error("Inspector did not commit the selected identity"));
            else requestAnimationFrame(committed);
          };
          committed();
        });
      }, id);
      await expect(page.locator(".inspector-summary h3")).toHaveText(id);
      if (repeat < 0) { openWarmup = openElapsed; selectionWarmup = elapsed; }
      else { opens.push(openElapsed); selections.push(elapsed); }
      writeFileSync(info.outputPath(`model-${width}.partial.json`), JSON.stringify({ viewport: page.viewportSize(), completedRepetitions: opens.length, warmups: 1, openWarmup, selectionWarmup, opens, selections, diagnostics, scope: "Actual prefix; final keyboard and threshold checks may still be pending" }, null, 2));
    }
    await activateByTab(page, page.getByRole("button", { name: "Table view", exact: true }));
    await expect(page.locator(".canvas-table tbody tr")).toHaveCount(200);
    const alternative = page.locator(".canvas-table").getByRole("button", { name: context.model.selectionIds[0], exact: true });
    await activateByTab(page, alternative);
    await expect(page.locator(".inspector-summary h3")).toHaveText(context.model.selectionIds[0]);
    expect(await alternative.evaluate((element) => { const s = getComputedStyle(element); return s.outlineStyle !== "none" && parseFloat(s.outlineWidth) >= 2; })).toBe(true);
    await activateByTab(page, page.getByRole("button", { name: "Graph view", exact: true }));
    await expect(page.locator(".react-flow__node-element")).toHaveCount(200);
    await expect(page.locator(".react-flow__edge")).toHaveCount(400);
    await noOverflow(page);
    const model = { scope: context.model.scope, platform: process.platform, browser: await page.context().browser()?.version(), viewport: page.viewportSize(),
      sourceProjectId: context.model.projectId, planDigest: context.model.planDigest, semanticDigest: context.model.semanticDigest,
      elements: 200, logicalAssets: context.model.logicalAssets, standalonePlacementNodes: context.model.standalonePlacementNodes, connections: 400, warmups: 1, repetitions: 30,
      openAndValidationPresentation: { milliseconds: opens, warmupMilliseconds: openWarmup, p95: p95(opens), threshold: 3000, passed: p95(opens) <= 3000 },
      selectionAndInspector: { milliseconds: selections, warmupMilliseconds: selectionWarmup, p95: p95(selections), threshold: 150, passed: p95(selections) <= 150 },
      passivePresentationDiagnostics: diagnostics, keyboardStructuredAlternative: true, visibleFocus: true, horizontalOverflow: false,
      measurement: "Open through matching real project and validation HTTP responses and presented graph/status; local selection through exact inspector identity commit plus two animation frames.",
      limitations: ["Synthetic expanded authoring topology; no simulator scalability/fidelity/admission claim.", "Native Windows and other browser engines NOT_RUN."] };
    writeFileSync(info.outputPath(`model-${width}.json`), JSON.stringify(model, null, 2));
    await page.screenshot({ path: info.outputPath(`model-${width}.png`), fullPage: true });

    await page.evaluate((fixture) => { localStorage.setItem("studio.projectId", fixture.projectId); localStorage.setItem("studio.lastRun", fixture.runId); localStorage.setItem("studio.lastRun." + fixture.projectId, fixture.runId); }, context.history);
    await page.reload();
    await page.getByRole("tab", { name: /^Results(?:\s+\d+)?$/ }).click();
    await expect(page.getByText("Recorded fixture scope", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Stop", exact: true })).toHaveCount(0);
    await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
    await page.getByLabel("Event kind", { exact: true }).selectOption("log.appended");
    await page.getByLabel("Severity", { exact: true }).selectOption("info");
    const panel = page.getByTestId("retained-history"), rows = panel.locator("[data-history-record=true]");
    await expect(panel).toHaveAttribute("aria-busy", "false");
    await expect(rows).toHaveCount(200);
    await expect(panel).toHaveAttribute("data-integrity", "valid");
    const samples: number[] = [], heapBytes: number[] = [];
    const cdp = await page.context().newCDPSession(page);
    await cdp.send("Performance.enable");
    let warmup = 0, omittedRecords = 0;
    for (let repeat = -1; repeat < 30; repeat++) {
      const epoch = Number(await panel.getAttribute("data-history-epoch"));
      const begin = await page.evaluate(() => performance.now());
      const response = page.waitForResponse((r) => { const url = new URL(r.url()); return url.pathname === `/api/v1/runs/${context.history.runId}/history` && url.searchParams.get("type") === "log.appended" && url.searchParams.get("severity") === "info"; });
      await page.getByRole("button", { name: "Reload retained first page", exact: true }).click();
      const reply = await response;
      expect(reply.status()).toBe(200);
      const result = await reply.json();
      expect(result.integrity).toBe("valid");
      expect(result.evidenceScope).toBe("recorded_fixture");
      expect(result.items.length).toBe(200);
      expect(result.counts.totalRecords).toBe(50000);
      expect(result.counts.omittedRecords).toBe(49800);
      omittedRecords = result.counts.omittedRecords;
      await expect.poll(async () => Number(await panel.getAttribute("data-history-epoch"))).toBeGreaterThan(epoch);
      await expect(panel).toHaveAttribute("aria-busy", "false");
      await expect(rows).toHaveCount(200);
      await expect(rows.first()).toHaveAttribute("data-event-id", context.history.runId + ":record-1");
      await expect(rows.last()).toHaveAttribute("data-sequence", "200");
      const elapsed = (await painted(page)) - begin;
      if (repeat < 0) warmup = elapsed;
      else samples.push(elapsed);
      const metrics = await cdp.send("Performance.getMetrics");
      heapBytes.push(metrics.metrics.find((m) => m.name === "JSHeapUsedSize")!.value);
      writeFileSync(info.outputPath(`history-${width}.partial.json`), JSON.stringify({ viewport: page.viewportSize(), completedRepetitions: samples.length, warmups: 1, warmupMilliseconds: warmup, milliseconds: samples, heapBytes, scope: "Actual prefix; final keyboard and threshold checks may still be pending" }, null, 2));
    }
    await cdp.detach();
    await activateByTab(page, page.getByRole("button", { name: "Next retained page", exact: true }));
    await expect(rows.first()).toHaveAttribute("data-sequence", "201");
    await expect(rows.last()).toHaveAttribute("data-sequence", "400");
    await activateByTab(page, page.getByRole("button", { name: "Previous retained page", exact: true }));
    await expect(rows.first()).toHaveAttribute("data-sequence", "1");
    await expect(rows).toHaveCount(200);
    await noOverflow(page);
    const evidence = await page.request.get(`/api/v1/runs/${context.history.runId}/evidence`).then((r) => r.json());
    expect(evidence.items[0].digest).toBe(context.history.journalDigest);
    expect(evidence.items[0].recordCount).toBe(50000);
    const history = { scope: "Synthetic inert 50,000-record load using the actual Autoverse frozen input identity; no recorded-simulator observation claim", platform: process.platform, browser: await page.context().browser()?.version(), viewport: page.viewportSize(),
      sourceRunId: context.history.sourceRunId, originalSourceRecordCount: context.history.sourceRecordCount,
      sourceRecords: 50000, pageSize: 200, omittedRecords, warmups: 1, repetitions: 30, warmupMilliseconds: warmup, milliseconds: samples,
      p95: p95(samples), threshold: 2000, passed: p95(samples) <= 2000,
      jsHeapUsedBytes: heapBytes, maximumJsHeapUsedBytes: Math.max(...heapBytes),
      journalDigest: context.history.journalDigest, journalBytes: context.history.journalBytes, integrity: "valid", keyboardPaging: true,
      limitations: ["Fixture creation, initial cold journal verification and filter setup excluded from warmed repetitions.", "Source-byte cache bound64MiB and two entries do not describe decoded object memory; actual backend RSS sampled separately.", "No live producer/control responsiveness, native Windows, other browser engines, runtime or physical observation claim."] };
    writeFileSync(info.outputPath(`history-${width}.json`), JSON.stringify(history, null, 2));
    await page.screenshot({ path: info.outputPath(`history-${width}.png`), fullPage: true });
  }
  expect(writes.every((url) => url === `/api/v1/projects/${context.model.projectId}/validations`)).toBe(true);
  writeFileSync(info.outputPath("requests.json"), JSON.stringify({ mutations: writes, preflightStartControlEvaluationAndCampaignRequests: 0 }, null, 2));
  // Retain every required viewport's actual samples before assessing all thresholds.
  for (const width of [1024, 1440]) {
    const model = JSON.parse(readFileSync(info.outputPath(`model-${width}.json`), "utf8"));
    const history = JSON.parse(readFileSync(info.outputPath(`history-${width}.json`), "utf8"));
    expect(model.openAndValidationPresentation.p95).toBeLessThanOrEqual(3000);
    expect(model.selectionAndInspector.p95).toBeLessThanOrEqual(150);
    expect(history.p95).toBeLessThanOrEqual(2000);
  }
});
