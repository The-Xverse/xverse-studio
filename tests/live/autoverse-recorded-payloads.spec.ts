import { test, expect, type Page, type Locator } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";

const recording = () => JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "playback-recording.private.json"), "utf8"));
async function activate(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let n = 0; n < 600; n++) {
    if (await target.evaluate(e => e === document.activeElement)) {
      await page.keyboard.press("Enter"); return;
    }
    await page.keyboard.press("Tab");
  }
  throw new Error("The original-record control is not reachable through native Tab order");
}
async function open(page: Page, info: any, width: number) {
  const source = recording();
  await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  await connectStudio(page, info);
  await page.evaluate(r => {
    localStorage.setItem("studio.lastRun", r.runId);
    localStorage.setItem("studio.lastRun." + r.projectId, r.runId);
  }, source);
  await page.getByRole("button", { name: "X-Verse Studio home", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
  const project = await page.request.get(`/api/v1/projects/${source.projectId}`);
  expect(project.status()).toBe(200);
  await page.locator(".project-list").getByRole("button").filter({ hasText: (await project.json()).name }).click();
  await page.getByRole("tab", { name: /^Results(?:\s+\d+)?$/ }).click();
  await page.getByLabel("Recorded run", { exact: true }).selectOption(source.runId);
  await expect(page.getByRole("heading", { name: "No plot samples available", exact: true })).toBeVisible();
  return source;
}
const region = (page: Page) => page.getByRole("region", { name: "Original observation records", exact: true });
const current = async (page: Page) => JSON.parse((await region(page).locator("pre[data-original-record]").textContent())!);
for (const width of [1024, 1440]) {
  test(`actual original records play and page through native keyboard at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [], replies: any[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    page.on("response", async r => { if (r.url().includes("/history?") && new URL(r.url()).searchParams.get("type") === "observation.available") replies.push(await r.json()); });
    await activate(page, page.getByRole("button", { name: "Load original observation records", exact: true }));
    const panel = region(page);
    await expect(panel).toContainText("20 of 21 matching records");
    expect(await current(page)).toEqual(source.records[0]);
    await expect(panel).toContainText("Source time unavailable");
    await expect(panel).toContainText("display interval");
    await activate(page, panel.getByRole("button", { name: "Next record", exact: true }));
    expect(await current(page)).toEqual(source.records[1]);
    await activate(page, panel.getByRole("button", { name: "Previous record", exact: true }));
    expect(await current(page)).toEqual(source.records[0]);
    await activate(page, panel.getByRole("button", { name: "Play recorded payloads", exact: true }));
    await expect.poll(async () => (await current(page)).eventId).not.toBe(source.records[0].eventId);
    await activate(page, panel.getByRole("button", { name: "Pause payload playback", exact: true }));
    const held = await current(page);
    await expect(panel.getByRole("button", { name: "Play recorded payloads", exact: true })).toBeFocused();
    expect(await panel.getByRole("button", { name: "Play recorded payloads", exact: true }).evaluate(e => { const s = getComputedStyle(e); return s.outlineStyle !== "none" && parseFloat(s.outlineWidth) >= 2; })).toBe(true);
    await activate(page, panel.getByRole("button", { name: "Next payload page", exact: true }));
    await expect(panel).toContainText("1 of 21 matching records");
    expect(await current(page)).toEqual(source.records[20]);
    await expect(panel.locator("pre[data-original-record]")).toBeFocused();
    await expect(panel.getByRole("button", { name: "Next payload page", exact: true })).toBeDisabled();
    await activate(page, panel.getByRole("button", { name: "Previous payload page", exact: true }));
    await expect(panel).toContainText("20 of 21 matching records");
    expect(await current(page)).toEqual(source.records[0]);
    await expect(panel.getByRole("button", { name: "Previous payload page", exact: true })).toBeDisabled();
    expect(replies.map(p => p.items)).toEqual([source.records.slice(0, 20), source.records.slice(20), source.records.slice(0, 20)]);
    expect(replies.every(p => p.integrity === "valid")).toBe(true);
    expect(writes).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    writeFileSync(info.outputPath(`playback-${width}.json`), JSON.stringify({ viewport: page.viewportSize(), browser: await page.context().browser()?.version(), sourceRunId: source.runId, snapshotId: source.snapshotId, originalRecords: 21, exactReturnedPages: replies.map(p => p.items.map((r: any) => r.eventId)), lastPausedRecordId: held.eventId, keyboard: true, writes, integrity: replies.map(p => p.integrity) }, null, 2));
    await page.screenshot({ path: info.outputPath(`playback-${width}.png`), fullPage: true });
    await activate(page, panel.getByRole("button", { name: "Play recorded payloads", exact: true }));
    await expect.poll(async () => (await current(page)).eventId).not.toBe(source.records[0].eventId);
    await activate(page, page.getByRole("tab", { name: "Compare", exact: true }));
    await expect(region(page)).toHaveCount(0);
    await activate(page, page.getByRole("tab", { name: "Observations", exact: true }));
    await expect(region(page).getByRole("button", { name: "Load original observation records", exact: true })).toBeVisible();
    await expect(region(page).locator("pre[data-original-record]")).toHaveCount(0);
  });
  test(`failed read retries against the actual journal at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    let failed = false;
    await page.route("**/history?*", async route => {
      if (new URL(route.request().url()).searchParams.get("type") === "observation.available" && !failed) {
        failed = true; await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ code: "READER_UNAVAILABLE", message: "Labelled reader-response fixture" }) });
      } else await route.continue();
    });
    await activate(page, page.getByRole("button", { name: "Load original observation records", exact: true }));
    await expect(region(page).getByRole("alert")).toContainText("Labelled reader-response fixture");
    await activate(page, region(page).getByRole("button", { name: "Refresh original records", exact: true }));
    await expect(region(page)).toContainText("20 of 21 matching records");
    expect(await current(page)).toEqual(recording().records[0]);
  });
  test(`late original response preserves Home at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    let release!: () => void, captured!: () => void;
    const held = new Promise<void>(resolve => release = resolve), ready = new Promise<void>(resolve => captured = resolve);
    await page.route("**/history?*", async route => {
      const response = await route.fetch(); captured(); await held;
      await route.fulfill({ response }).catch(() => {});
    });
    try {
      await activate(page, page.getByRole("button", { name: "Load original observation records", exact: true }));
      await ready;
      await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
      await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
    } finally { release(); }
    await page.unrouteAll({ behavior: "wait" });
    await expect(region(page)).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
  });
  test(`late original response preserves deliberate focus at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    let release!: () => void, captured!: () => void;
    const held = new Promise<void>(resolve => release = resolve), ready = new Promise<void>(resolve => captured = resolve);
    await page.route("**/history?*", async route => {
      const response = await route.fetch(); captured(); await held;
      await route.fulfill({ response }).catch(() => {});
    });
    try {
      await activate(page, page.getByRole("button", { name: "Load original observation records", exact: true }));
      await ready;
      await page.getByLabel("Recorded run", { exact: true }).focus();
    } finally { release(); }
    await page.unrouteAll({ behavior: "wait" });
    await expect(region(page)).toContainText("20 of 21 matching records");
    await expect(page.getByLabel("Recorded run", { exact: true })).toBeFocused();
  });
  test(`source-clock selection does not invent timestamps for receipt payloads at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    await page.getByLabel("Time basis", { exact: true }).selectOption("source");
    await page.getByLabel("Source clock", { exact: true }).selectOption("host-runtime");
    await activate(page, page.getByRole("button", { name: "Apply evidence filters", exact: true }));
    await expect(page.getByText("Loading observations for this exact run and filter…", { exact: true })).toHaveCount(0);
    await activate(page, page.getByRole("button", { name: "Load original observation records", exact: true }));
    await expect(region(page)).toContainText("0 of 0 matching records");
    await expect(region(page)).toContainText("No original observation records match");
    await expect(region(page).locator("pre[data-original-record]")).toHaveCount(0);
  });
  test(`labelled large payload has an explicit bounded display at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    await page.route("**/history?*", async route => {
      const response = await route.fetch(), body = await response.json();
      body.items[0].payload = { ...body.items[0].payload, labelledDisplayFixture: "x".repeat(70000) };
      await route.fulfill({ response, json: body });
    });
    await activate(page, page.getByRole("button", { name: "Load original observation records", exact: true }));
    await expect(region(page)).toContainText("Displaying the first 65536 characters");
    expect((await region(page).locator("pre[data-original-record]").textContent())!.length).toBe(65536);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  });
  for (const fault of ["invalid-integrity", "wrong-event", "wrong-snapshot", "oversized", "repeated-cursor"]) {
    test(`labelled ${fault} reply cannot enable misleading playback at ${width}`, async ({ page }, info) => {
      await open(page, info, width);
      await page.route("**/history?*", async route => {
        const response = await route.fetch(), body = await response.json();
        if (fault === "invalid-integrity") body.integrity = "invalid";
        if (fault === "wrong-event") body.items[0] = { ...body.items[0], type: "log.appended" };
        if (fault === "wrong-snapshot") body.items[0] = { ...body.items[0], snapshotId: "unrelated-snapshot" };
        if (fault === "oversized") body.items = Array(21).fill(body.items[0]);
        if (fault === "repeated-cursor") body.nextCursor = new URL(route.request().url()).searchParams.get("cursor") || "";
        await route.fulfill({ response, json: body });
      });
      await activate(page, page.getByRole("button", { name: "Load original observation records", exact: true }));
      if (fault === "invalid-integrity") {
        await expect(region(page)).toContainText("Integrity: invalid");
        await expect(region(page).getByRole("button", { name: "Play recorded payloads", exact: true })).toBeDisabled();
        expect(await current(page)).toEqual(recording().records[0]);
      } else {
        await expect(region(page).getByRole("alert")).toContainText("incompatible");
        await expect(region(page).locator("pre[data-original-record]")).toHaveCount(0);
      }
    });
  }
}
