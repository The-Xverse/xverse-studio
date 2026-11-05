import { test, expect, type Locator, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";

async function focus(page: Page, control: Locator) {
  await expect(control).toBeVisible();
  for (let i = 0; i < 600; i++) {
    if (await control.evaluate(node => node === document.activeElement)) return;
    await page.keyboard.press("Tab");
  }
  throw Error("Retained run selection is unreachable through keyboard navigation");
}
async function activate(page: Page, control: Locator) {
  await focus(page, control);
  await page.keyboard.press("Enter");
}
for (const width of [1024, 1440]) {
  test(`fresh browser selects actual retained Autoverse results at ${width}`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    const source = JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "playback-recording.private.json"), "utf8"));
    await connectStudio(page, info);
    expect(await page.evaluate(() => Object.keys(localStorage).filter(k => k.startsWith("studio.lastRun")))).toEqual([]);
    const writes: string[] = [];
    page.on("request", request => { if (request.method() !== "GET") writes.push(new URL(request.url()).pathname); });
    await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
    await activate(page, page.locator(`.project-list-row[data-project-id="${source.projectId}"] .project-open`));
    await activate(page, page.getByRole("tab", { name: "Results", exact: true }));
    const select = page.getByLabel("Recorded run", { exact: true });
    await expect(select).toBeVisible();
    await expect(select.locator(`option[value="${source.runId}"]`)).toHaveCount(1);
    await expect(select).toHaveValue("");
    await focus(page, select);
    await page.keyboard.press("ArrowDown");
    await expect(select).toHaveValue(source.runId);
    await expect(page.locator(".run-identity")).toContainText(source.runId);
    await activate(page, page.getByRole("tab", { name: "Diagnosis", exact: true }));
    const diagnosis = page.getByRole("region", { name: "Run diagnosis", exact: true });
    await expect(diagnosis).toHaveAttribute("data-explanation-state", "loaded");
    await expect(diagnosis).toContainText("TIME_MAPPING_INCOMPATIBLE");
    expect(writes).toEqual([]);
    expect(await page.evaluate(() => localStorage.getItem("studio.lastRun"))).toBe(source.runId);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await info.attach("fresh-retained-selection", { body: JSON.stringify({ width, runId: source.runId, browser: page.context().browser()?.version(), writes,
      scope: "Actual retained Autoverse run selected with an initially empty browser preference; no provider/model/guest or evaluation operation" }), contentType: "application/json" });
  });
  for (const mode of ["reader failure", "wrong project", "incompatible shape", "cursor regression", "paged list", "late after Home", "stale selected metadata"] as const) {
    test(`retained run picker handles ${mode} at ${width}`, async ({ page }, info) => {
      await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
      const source = JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "playback-recording.private.json"), "utf8"));
      await connectStudio(page, info);
      const originalReply = await page.request.get(`/api/v1/runs/${source.runId}`);
      expect(originalReply.status()).toBe(200);
      const original = await originalReply.json();
      if (mode === "stale selected metadata") {
        await page.evaluate(s => localStorage.setItem("studio.lastRun." + s.projectId, s.runId), source);
      }
      let attempts = 0, release!: () => void, accepted!: () => void;
      const held = new Promise<void>(resolve => { release = resolve; });
      const received = new Promise<void>(resolve => { accepted = resolve; });
      const queries: string[] = [], writes: string[] = [];
      page.on("request", request => { if (request.method() !== "GET") writes.push(new URL(request.url()).pathname); });
      await page.route(url => url.pathname === "/api/v1/runs" && url.searchParams.has("projectId"), async route => {
        const url = new URL(route.request().url());
        expect(url.searchParams.get("projectId")).toBe(source.projectId);
        expect(url.searchParams.get("limit")).toBe("200");
        queries.push(url.search); attempts++;
        if (mode === "reader failure" && attempts === 1) {
          await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ code: "READER_UNAVAILABLE", message: "Labelled retained-run reader-response fixture" }) });
        } else if (mode === "wrong project" && attempts === 1) {
          await route.fulfill({ json: { items: [{ ...original, projectId: "labelled-other-project-fixture" }], nextCursor: null } });
        } else if (mode === "incompatible shape" && attempts === 1) {
          await route.fulfill({ status: 200, contentType: "application/json", body: "null" });
        } else if (mode === "cursor regression" && attempts === 1) {
          await route.fulfill({ json: { items: [original], nextCursor: "0" } });
        } else if (mode === "stale selected metadata") {
          await route.fulfill({ json: { items: [{ ...original, state: "running" }], nextCursor: null } });
        } else if (mode === "paged list" && !url.searchParams.has("cursor") && attempts === 1) {
          // Labelled metadata-page fixture; no synthetic run is stored or selected.
          await route.fulfill({ json: { items: Array.from({ length: 200 }, (_, i) => ({ ...original, runId: `labelled-page-fixture-${i}` })), nextCursor: "200" } });
        } else if (mode === "paged list" && url.searchParams.get("cursor") === "200") {
          await route.fulfill({ json: { items: [original], nextCursor: null } });
        } else if (mode === "late after Home") {
          const response = await route.fetch(); accepted(); await held;
          try { await route.fulfill({ response }); } catch { /* The departed component aborts its own read. */ }
        } else await route.continue();
      });
      await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
      await activate(page, page.locator(`.project-list-row[data-project-id="${source.projectId}"] .project-open`));
      await activate(page, page.getByRole("tab", { name: /^Results(?:\s+\d+)?$/ }));
      const picker = page.getByRole("group", { name: "Recorded runs", exact: true });
      if (mode === "stale selected metadata") {
        const select = picker.getByLabel("Recorded run", { exact: true });
        await expect(select).toHaveValue(source.runId);
        await expect(select.locator("option:checked")).toContainText(original.state);
        await expect(select.locator("option:checked")).not.toContainText("running");
      } else if (mode === "late after Home") {
        await received;
        const home = page.getByRole("button", { name: "X-Verse Studio home", exact: true });
        await activate(page, home); release();
        await expect(home).toBeFocused();
        await expect(picker).toHaveCount(0);
        await expect(page.locator(".project-list")).toBeVisible();
      } else {
        if (["reader failure", "wrong project", "incompatible shape", "cursor regression"].includes(mode)) {
          await expect(picker.getByRole("alert")).toContainText(mode === "reader failure" ? "Labelled retained-run reader-response fixture" : "incompatible with this project");
          expect(attempts).toBe(1);
          const refresh = picker.getByRole("button", { name: "Refresh recorded runs", exact: true });
          await activate(page, refresh);
          await expect(picker.getByRole("alert")).toHaveCount(0);
          await expect(refresh).toBeFocused();
        } else {
          await expect(picker.getByRole("status")).toContainText("200 recorded run(s)");
          const next = picker.getByRole("button", { name: "Next recorded run page", exact: true });
          await activate(page, next);
          await expect(next).toHaveAttribute("aria-disabled", "true");
          await expect(next).toBeFocused();
          expect(queries.some(q => new URLSearchParams(q).get("cursor") === "200")).toBe(true);
          const first = picker.getByRole("button", { name: "First recorded run page", exact: true });
          await activate(page, first);
          await expect(first).toHaveAttribute("aria-disabled", "true");
          await expect(first).toBeFocused();
        }
        const select = picker.getByLabel("Recorded run", { exact: true });
        await expect(select.locator(`option[value="${source.runId}"]`)).toHaveCount(1);
        await focus(page, select); await page.keyboard.press("ArrowDown");
        await expect(select).toHaveValue(source.runId);
        await expect(select).toBeFocused();
        await expect(page.locator(".run-identity")).toContainText(source.runId);
      }
      expect(writes).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      await info.attach("retained-run-picker-guard", { body: JSON.stringify({ mode, width, queries, attempts, writes,
        scope: "Actual retained Autoverse run; explicitly labelled HTTP/identity/page/delayed-response fixtures; no execution or derived evaluation" }), contentType: "application/json" });
    });
  }
}
