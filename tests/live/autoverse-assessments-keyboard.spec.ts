import { test, expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
import { renderedContrast } from "../e2e/contrast";

const recording = () => JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "playback-recording.private.json"), "utf8"));
const panel = (page: Page) => page.getByRole("region", { name: "Frozen assertions and metrics", exact: true });
const inspect = (page: Page) => panel(page).getByRole("button", { name: "Inspect frozen assessments", exact: true });
const heading = (page: Page) => panel(page).getByRole("heading", { name: "Frozen assertions and metrics", exact: true });
async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 600; i++) {
    if (await target.evaluate(n => n === document.activeElement)) {
      expect(await target.evaluate(n => {
        const r = n.getBoundingClientRect(), s = getComputedStyle(n);
        return r.left >= 0 && r.right <= innerWidth + 1 && r.top >= 0 && r.bottom <= innerHeight + 1 &&
          s.outlineStyle !== "none" && parseFloat(s.outlineWidth) >= 2;
      })).toBe(true);
      return;
    }
    await page.keyboard.press("Tab");
  }
  throw Error("Required assessment control is unreachable through native Tab order");
}
async function activate(page: Page, target: Locator) {
  await tabTo(page, target);
  await page.keyboard.press("Enter");
}
function field(card: Locator, label: string) {
  return card.locator(".key-values > div").filter({ has: card.page().getByText(label, { exact: true }) }).locator("dd");
}
async function loaded(page: Page) {
  await expect(panel(page).locator("article.evaluation-card")).toHaveCount(6);
  await expect(panel(page)).toContainText("EVALUATION_EVIDENCE_UNSUPPORTED");
}
async function open(page: Page, info: TestInfo, width: number) {
  await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  await connectStudio(page, info);
  const source = recording();
  await page.evaluate(r => {
    localStorage.setItem("studio.lastRun", r.runId);
    localStorage.setItem("studio.lastRun." + r.projectId, r.runId);
  }, source);
  await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
  const response = await page.request.get(`/api/v1/projects/${source.projectId}`);
  expect(response.status()).toBe(200);
  await activate(page, page.locator(".project-list").getByRole("button").filter({ hasText: (await response.json()).name }));
  await activate(page, page.getByRole("tab", { name: "Experiments", exact: true }));
  const assertions = page.getByRole("tab", { name: "Assertions", exact: true });
  await activate(page, assertions);
  await loaded(page);
  await expect(assertions).toBeFocused();
  return source;
}
async function report(page: Page, info: TestInfo, width: number, writes: string[], fixture: string | null) {
  expect(writes).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await info.attach("actual-assessments-keyboard", { body: JSON.stringify({ width, writes, fixture,
    browser: page.context().browser()?.version(),
    scope: "Six actual historical Autoverse definitions/results; current provider mapping unregistered, new evaluation unavailable; no runtime or assistive-technology certification",
  }), contentType: "application/json" });
}
async function holdDefinitions(page: Page, runId: string) {
  let release!: () => void, seen!: () => void;
  const gate = new Promise<void>(r => { release = r; });
  const fetched = new Promise<void>(r => { seen = r; });
  await page.route(`**/api/v1/runs/${runId}/definitions`, async route => {
    const response = await route.fetch();
    seen();
    await gate;
    await route.fulfill({ response });
  }, { times: 1 });
  return { release, fetched };
}

for (const width of [1024, 1440]) {
  test(`actual stored assessment outcomes and keyboard refresh remain inspectable at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    const results = await page.request.get(`/api/v1/runs/${source.runId}/evaluations`).then(r => r.json());
    expect(results.items).toHaveLength(6);
    expect(results.items.map((r: any) => r.verdict).filter(Boolean).sort()).toEqual(["fail", "indeterminate", "indeterminate", "pass"]);
    for (const row of results.items) {
      const card = panel(page).locator("article.evaluation-card").filter({ has: page.getByRole("heading", { name: row.definitionRef, exact: true }) });
      await expect(field(card, "Execution status")).toHaveText(row.status);
      await expect(field(card, "Assertion verdict")).toHaveText(row.verdict ?? "No verdict");
      await expect(field(card, "Definition digest")).toHaveText(row.definitionDigest);
      await expect(field(card, "Value")).toHaveText(row.value == null ? "Unavailable" : String(row.value));
    }
    const definition = panel(page).getByRole("combobox", { name: "Snapshot definition reference", exact: true });
    await tabTo(page, definition);
    await page.keyboard.press("Home"); await page.keyboard.press("ArrowDown"); await page.keyboard.press("Tab");
    await expect(definition).not.toHaveValue("");
    await expect(panel(page).getByRole("button", { name: "Evaluate assertion", exact: true })).toBeDisabled();
    const contrast = await renderedContrast(panel(page).getByText(/Not evaluated: no admitted measurement/), "Current unsupported evaluation explanation");
    expect(contrast.supported).toBe(true);
    if (contrast.supported) expect(contrast.ratio).toBeGreaterThanOrEqual(4.5);
    await activate(page, inspect(page));
    await loaded(page);
    await expect(heading(page)).toBeFocused();
    const exact = panel(page).getByText("Inspect exact data", { exact: true }).first();
    await activate(page, exact);
    await expect(exact.locator("..")).toHaveAttribute("open", "");
    await report(page, info, width, writes, null);
  });

  test(`assessment HTTP refusal has meaningful focus and native retry at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    await page.route(`**/api/v1/runs/${source.runId}/definitions`, route => route.fulfill({ status: 503, json: {
      code: "ASSESSMENT_KEYBOARD_FIXTURE", message: "Labelled definition read failure", retryable: true,
    } }), { times: 1 });
    await activate(page, inspect(page));
    await expect(panel(page).getByRole("alert")).toContainText("availability is unknown");
    await expect(panel(page).getByRole("alert")).toBeFocused();
    await activate(page, inspect(page));
    await loaded(page);
    await expect(heading(page)).toBeFocused();
    await report(page, info, width, writes, "One labelled503 definition response; actual retry and actual six stored results");
  });

  test(`foreign assessment identity is refused with a keyboard recovery at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    await page.route(`**/api/v1/runs/${source.runId}/evaluations?**`, async route => {
      const response = await route.fetch(), value = await response.json();
      value.items[0].snapshotId = "labelled-foreign-snapshot";
      await route.fulfill({ response, json: value });
    }, { times: 1 });
    await activate(page, inspect(page));
    await expect(panel(page).getByRole("alert")).toContainText("another run or snapshot");
    await expect(panel(page).getByRole("alert")).toBeFocused();
    await expect(panel(page).locator("article.evaluation-card")).toHaveCount(0);
    await activate(page, inspect(page)); await loaded(page);
    await expect(heading(page)).toBeFocused();
    await report(page, info, width, writes, "One labelled post-read foreign snapshot identity; canonical source unchanged");
  });

  test(`held actual assessment refresh preserves newer keyboard focus at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    const held = await holdDefinitions(page, source.runId);
    try {
      await activate(page, inspect(page)); await held.fetched;
      const home = page.getByRole("button", { name: "X-Verse Studio home", exact: true });
      await tabTo(page, home); held.release(); await loaded(page);
      await expect(home).toBeFocused();
      await report(page, info, width, writes, "Actual definition reply held until focus moves; unchanged response");
    } finally { held.release(); }
  });

  test(`held assessment refresh preserves a newer native source dialog at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    const held = await holdDefinitions(page, source.runId);
    try {
      await activate(page, inspect(page)); await held.fetched;
      const opener = page.getByRole("button", { name: "Edit scenario XDL", exact: true });
      await activate(page, opener);
      const dialog = page.getByRole("dialog", { name: "Authored XDL source", exact: true }), sourceEditor = dialog.getByRole("textbox", { name: "XDL source", exact: true });
      await expect(sourceEditor).toBeFocused(); held.release(); await loaded(page);
      await expect(sourceEditor).toBeFocused();
      await page.keyboard.press("Escape"); await expect(dialog).toHaveCount(0); await expect(opener).toBeFocused();
      await report(page, info, width, writes, "Actual definition reply held while a newer source dialog opens");
    } finally { held.release(); }
  });

  test(`departed assessment read cannot restore its view or focus at ${width}`, async ({ page }, info) => {
    const source = await open(page, info, width), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    const held = await holdDefinitions(page, source.runId);
    try {
      await activate(page, inspect(page)); await held.fetched;
      const scenario = page.getByRole("tab", { name: "Scenario", exact: true });
      await activate(page, scenario); held.release();
      await expect(scenario).toBeFocused(); await expect(panel(page)).toHaveCount(0);
      await page.unrouteAll({ behavior: "wait" });
      await expect(scenario).toBeFocused(); await expect(panel(page)).toHaveCount(0);
      await report(page, info, width, writes, "Actual late definition reply after component departure");
    } finally { held.release(); }
  });
}
