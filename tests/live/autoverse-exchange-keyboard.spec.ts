import { test, expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
import { renderedContrast } from "../e2e/contrast";

const data = () => process.env.STUDIO_BROWSER_DATA!;
const context = () => JSON.parse(readFileSync(path.join(data(), "exchange-recording.private.json"), "utf8"));
const dialog = (page: Page) => page.getByRole("dialog", { name: "Imported evidence inspection", exact: true });

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let step = 0; step < 600; step++) {
    if (await target.evaluate(node => node === document.activeElement)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error("Required evidence-import control is unreachable through native Tab order");
}
async function activate(page: Page, target: Locator) {
  await tabTo(page, target);
  await page.keyboard.press("Enter");
}
async function open(page: Page, info: TestInfo, width: number) {
  await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  await connectStudio(page, info);
  await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
  await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
}
async function choose(page: Page, file: string) {
  const picker = page.waitForEvent("filechooser");
  await activate(page, page.getByRole("button", { name: "Import evidence", exact: true }));
  await (await picker).setFiles(path.join(data(), file));
}
const imported = (page: Page) => page.waitForResponse(r => new URL(r.url()).pathname === "/api/v1/evidence/imports" && r.request().method() === "POST");
async function read(page: Page) {
  const r = await page.request.get("/api/v1/evidence/imports?limit=100");
  expect(r.status()).toBe(200);
  return (await r.json()).items;
}
async function leave(page: Page, destination: string) {
  const button = destination === "Home"
    ? page.getByRole("button", { name: "X-Verse Studio home", exact: true })
    : page.getByRole("navigation", { name: "Main navigation", exact: true }).getByRole("button", { name: destination, exact: true });
  await activate(page, button);
  if (destination === "Home") await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
  else await expect(button).toHaveAttribute("aria-current", "page");
  return button;
}

for (const width of [1024, 1440]) {
  for (const [file, integrity] of [["evidence-valid.zip", "unavailable"], ["evidence-damaged.zip", "invalid"]]) {
    test(`native keyboard imports and inspects ${integrity} Autoverse evidence at ${width}`, async ({ page }, info) => {
      await open(page, info, width);
      const before = await read(page), writes: string[] = [];
      page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
      const reply = imported(page);
      await choose(page, file);
      expect((await reply).status()).toBe(201);
      const panel = dialog(page), source = context();
      await expect(panel).toBeVisible();
      await expect(panel.getByRole("button", { name: "Close dialog", exact: true })).toBeFocused();
      const current = panel.getByRole("region", { name: "Current imported evidence inspection", exact: true });
      const original = panel.getByRole("region", { name: "Original imported evidence report", exact: true });
      await expect(current).toContainText(source.sourceRunId);
      await expect(current).toContainText(source.sourceSnapshotId);
      await expect(current.locator(".key-values > div").filter({ has: page.locator("dt", { hasText: /^Current integrity$/ }) })).toContainText(integrity);
      await expect(original.locator(".key-values > div").filter({ has: page.locator("dt", { hasText: /^Reported integrity$/ }) })).toContainText("valid");
      await expect(panel).toContainText("Import creates no run and grants no execution authority");
      await expect(panel).toContainText("6 recorded evaluations and 2 annotations");
      const dependencies = panel.getByRole("region", { name: "Referenced dependencies", exact: true });
      const provider = dependencies.getByText("Inspect provider identity", { exact: true });
      await activate(page, provider);
      await expect(provider).toBeFocused();
      await expect(dependencies).toContainText(source.installationDigest);
      await activate(page, dependencies.getByText("Inspect profile identity", { exact: true }).first());
      await expect(dependencies).toContainText(source.compiledProfileDigest);
      await activate(page, panel.getByText("Inspect recorded evaluations and annotations", { exact: true }));
      await expect(panel.locator("details[open]").filter({ has: page.getByText("Inspect recorded evaluations and annotations", { exact: true }) })).toBeVisible();
      const measurements = [await renderedContrast(current.getByRole("heading"), "Current inspection heading"), await renderedContrast(original.locator("p"), "Original claims explanation"), await renderedContrast(provider, "Provider identity keyboard control")];
      for (const pair of measurements) { expect(pair.supported).toBe(true); if (pair.supported) expect(pair.ratio).toBeGreaterThanOrEqual(4.5); }
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      await page.keyboard.press("Escape");
      await expect(panel).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Import evidence", exact: true })).toBeFocused();
      expect((await read(page)).length).toBe(before.length + 1);
      expect(writes).toEqual(["/api/v1/evidence/imports"]);
      await info.attach("evidence-keyboard.json", { body: JSON.stringify({ width, file, integrity, measurements, writes, restoredImportFocus: true, browser: await page.context().browser()?.version(), scope: "Actual Autoverse evidence archive; native keyboard browser activation and filechooser handoff, no OS file-dialog or assistive-technology certification" }), contentType: "application/json" });
    });
  }
  test(`native keyboard evidence rejection remains actionable at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    const before = await read(page), reply = imported(page);
    await choose(page, "evidence-invalid.zip");
    expect((await reply).status()).toBe(422);
    const error = page.getByRole("alert", { name: "Operation error", exact: true });
    await expect(error).toContainText("EVIDENCE_BUNDLE_INVALID");
    await expect(dialog(page)).toHaveCount(0);
    expect((await read(page)).length).toBe(before.length);
    await tabTo(page, page.getByRole("button", { name: "Import evidence", exact: true }));
    await expect(page.getByRole("button", { name: "Import evidence", exact: true })).toBeFocused();
    await info.attach("evidence-rejection.json", { body: JSON.stringify({ width, status: 422, code: "EVIDENCE_BUNDLE_INVALID", importsUnchanged: true, scope: "Owned truncated ZIP fixture; actual backend refusal" }), contentType: "application/json" });
  });
  for (const destination of ["Home", "Catalog"]) {
    test(`accepted evidence import cannot reopen a departed ${destination} at ${width}`, async ({ page }, info) => {
      await open(page, info, width);
      const before = await read(page);
      let release!: () => void, captured!: () => void;
      const held = new Promise<void>(r => release = r), ready = new Promise<void>(r => captured = r);
      await page.route("**/api/v1/evidence/imports", async route => {
        if (route.request().method() !== "POST") return route.continue();
        const response = await route.fetch(); expect(response.status()).toBe(201); captured(); await held; await route.fulfill({ response });
      });
      try {
        await choose(page, "evidence-valid.zip");
        await ready;
        const target = await leave(page, destination), reply = imported(page);
        release(); expect((await reply).status()).toBe(201);
        await expect(page.locator(".notice.busy")).toHaveCount(0);
        await expect(dialog(page)).toHaveCount(0);
        await expect(target).toBeFocused();
        expect((await read(page)).length).toBe(before.length + 1);
        await info.attach("late-import.json", { body: JSON.stringify({ width, destination, acceptedAndRetained: true, lateModalSuppressed: true, focusPreserved: true, scope: "Delayed actual HTTP201; import persists without execution" }), contentType: "application/json" });
      } finally { release(); await page.unrouteAll({ behavior: "wait" }); }
    });
  }
  test(`late evidence rejection cannot replace newer navigation at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    const before = await read(page);
    let release!: () => void, captured!: () => void;
    const held = new Promise<void>(r => release = r), ready = new Promise<void>(r => captured = r);
    await page.route("**/api/v1/evidence/imports", async route => {
      if (route.request().method() !== "POST") return route.continue();
      const response = await route.fetch(); expect(response.status()).toBe(422); captured(); await held; await route.fulfill({ response });
    });
    try {
      await choose(page, "evidence-invalid.zip"); await ready;
      const target = await leave(page, "Catalog"), reply = imported(page);
      release(); expect((await reply).status()).toBe(422);
      await expect(page.locator(".notice.busy")).toHaveCount(0);
      await expect(page.getByRole("alert", { name: "Operation error", exact: true })).toHaveCount(0);
      await expect(dialog(page)).toHaveCount(0); await expect(target).toBeFocused();
      expect((await read(page)).length).toBe(before.length);
    } finally { release(); await page.unrouteAll({ behavior: "wait" }); }
  });
  test(`newer evidence selection wins even when the older reply arrives first at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    const before = await read(page), releases: Array<() => void> = [], ready: Array<Promise<void>> = [], bodies: any[] = [];
    const captures: Array<() => void> = [];
    for (let i = 0; i < 2; i++) ready.push(new Promise<void>(r => captures.push(r)));
    let count = 0;
    await page.route("**/api/v1/evidence/imports", async route => {
      if (route.request().method() !== "POST") return route.continue();
      const index = count++, response = await route.fetch(); expect(response.status()).toBe(201); bodies[index] = await response.json();
      const held = new Promise<void>(r => releases[index] = r); captures[index](); await held; await route.fulfill({ response });
    });
    try {
      await choose(page, "evidence-valid.zip"); await ready[0];
      await choose(page, "evidence-damaged.zip"); await ready[1];
      const first = imported(page); releases[0]();
      const firstReply = await first;
      expect(firstReply.status()).toBe(201);
      await firstReply.finished();
      await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => resolve())));
      await expect(page.locator(".notice.busy")).toHaveCount(1);
      await expect(dialog(page)).toHaveCount(0);
      const second = imported(page); releases[1](); expect((await second).status()).toBe(201);
      await expect(dialog(page)).toContainText(bodies[1].bundleId);
      await expect(dialog(page)).not.toContainText(bodies[0].bundleId);
      expect((await read(page)).length).toBe(before.length + 2);
      await page.keyboard.press("Escape");
    } finally { for (const release of releases) release?.(); await page.unrouteAll({ behavior: "wait" }); }
  });
}
