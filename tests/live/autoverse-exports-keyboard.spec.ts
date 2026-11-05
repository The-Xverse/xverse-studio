import { test, expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";

type Kind = "project" | "evidence";
const recording = () => JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "playback-recording.private.json"), "utf8"));
const sources = (p: any) => Object.fromEntries(Object.values(p.documents).map((d: any) => [d.path, d.content]));
async function activate(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 600; i++) {
    if (await target.evaluate(n => n === document.activeElement)) {
      expect(await target.evaluate(n => {
        const r = n.getBoundingClientRect(), s = getComputedStyle(n);
        return r.left >= 0 && r.right <= innerWidth + 1 && r.top >= 0 && r.bottom <= innerHeight + 1 && s.outlineStyle !== "none" && parseFloat(s.outlineWidth) > 0;
      })).toBe(true);
      await page.keyboard.press("Enter"); return;
    }
    await page.keyboard.press("Tab");
  }
  throw Error("Required export/import control is unreachable through native Tab order");
}
async function get(page: Page, route: string) {
  const response = await page.request.get("/api/v1" + route); expect(response.status()).toBe(200); return response.json();
}
async function open(page: Page, info: TestInfo, width: number, kind: Kind) {
  await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  await connectStudio(page, info);
  const source = recording();
  // Fixture setup restores a known persisted project; the tested actions below use native keys.
  await page.evaluate(r => {
    localStorage.setItem("studio.projectId", r.projectId);
    localStorage.setItem("studio.lastRun", r.runId);
    localStorage.setItem("studio.lastRun." + r.projectId, r.runId);
  }, source);
  await page.reload();
  const project = await get(page, `/projects/${source.projectId}`);
  await expect(page.locator(".project-header h1")).toHaveText(project.name);
  if (kind === "evidence") {
    await activate(page, page.getByRole("tab", { name: /^Results(?:\s+\d+)?$/ }));
    await expect(page.getByLabel("Recorded run", { exact: true })).toHaveValue(source.runId);
    await activate(page, page.getByRole("tab", { name: "Evidence", exact: true }));
    await expect(page.getByRole("heading", { name: "Canonical evidence inventory", exact: true })).toBeVisible();
  }
  return { source, project };
}
const action = (page: Page, kind: Kind) => page.getByRole("button", { name: kind === "project" ? "Export" : "Export evidence bundle", exact: true });
async function download(page: Page, info: TestInfo, kind: Kind) {
  const source = recording(), route = kind === "project" ? `/api/v1/projects/${source.projectId}/exports` : `/api/v1/runs/${source.runId}/exports`;
  const reply = page.waitForResponse(r => new URL(r.url()).pathname === route && r.request().method() === "POST");
  const received = page.waitForEvent("download");
  await activate(page, action(page, kind));
  const response = await reply; expect(response.status()).toBe(202);
  const operation = await response.json(); expect(operation.status).toBe("completed");
  const file = await received, saved = info.outputPath(`${kind}.zip`);
  await file.saveAs(saved); expect(await file.failure()).toBeNull();
  expect(file.suggestedFilename()).toMatch(/\.zip$/);
  const raw = readFileSync(saved), digest = "sha256:" + createHash("sha256").update(raw).digest("hex");
  expect(digest).toBe(operation.result.digest); expect(raw.length).toBe(operation.result.size);
  await expect(action(page, kind)).toBeFocused();
  return { kind, path: saved, digest, bytes: raw.length, suggestedFilename: file.suggestedFilename(), operation };
}
async function choose(page: Page, name: string, file: string) {
  await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
  const picker = page.waitForEvent("filechooser");
  await activate(page, page.getByRole("button", { name, exact: true }));
  await (await picker).setFiles(file);
}
async function compile(page: Page, project: any) {
  const session = await get(page, "/session");
  const response = await page.request.post(`/api/v1/projects/${project.projectId}/compilations`, {
    headers: { Origin: process.env.STUDIO_BASE_URL!, "X-CSRF-Token": session.csrfToken }, data: { revision: project.revision },
  });
  const body = await response.json();
  return { status: response.status(), valid: body.valid, planDigest: body.planDigest, semanticDigest: body.semanticDigest, code: body.code };
}
async function report(page: Page, info: TestInfo, width: number, result: any, details: any) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await info.attach("actual-export-keyboard", { body: JSON.stringify({ width, ...result, ...details, browser: page.context().browser()?.version(),
    scope: "Actual portable project or frozen Autoverse evidence; native export/download and browser filechooser handoff; no OS-dialog/AT certification, workload or provider admission",
  }), contentType: "application/json" });
}

for (const width of [1024, 1440]) {
  test(`native project export download and inert portable import at ${width}`, async ({ page }, info) => {
    const { source, project } = await open(page, info, width, "project");
    const originalCompile = await compile(page, project), result = await download(page, info, "project");
    const response = page.waitForResponse(r => new URL(r.url()).pathname === "/api/v1/projects/imports" && r.request().method() === "POST");
    await choose(page, "Import project", result.path);
    const imported = await response; expect(imported.status()).toBe(201); const current = await imported.json();
    expect(current.projectId).not.toBe(source.projectId);
    await expect.poll(() => page.evaluate(() => localStorage.getItem("studio.projectId"))).toBe(current.projectId);
    await expect(page.getByText("Archive imported without executing referenced code.", { exact: false })).toBeVisible();
    expect(sources(current)).toEqual(sources(project)); expect(current.layout).toEqual(project.layout);
    expect(await compile(page, current)).toEqual(originalCompile);
    expect((await get(page, `/projects/${current.projectId}/local-bindings`)).state).toBe("empty");
    const preserved = await get(page, `/projects/${source.projectId}`);
    expect(sources(preserved)).toEqual(sources(project)); expect(preserved.revision).toBe(project.revision);
    await report(page, info, width, result, { importedProjectId: current.projectId, authoredBytesPreserved: true, compilation: originalCompile, importedBindings: "empty" });
  });

  test(`native evidence export download and inert historical import at ${width}`, async ({ page }, info) => {
    const { source } = await open(page, info, width, "evidence"), result = await download(page, info, "evidence");
    const response = page.waitForResponse(r => new URL(r.url()).pathname === "/api/v1/evidence/imports" && r.request().method() === "POST");
    await choose(page, "Import evidence", result.path);
    const imported = await response; expect(imported.status()).toBe(201); const value = await imported.json();
    const dialog = page.getByRole("dialog", { name: "Imported evidence inspection", exact: true });
    await expect(dialog).toBeVisible(); await expect(dialog).toContainText(source.runId); await expect(dialog).toContainText(source.snapshotId);
    await expect(dialog).toContainText("Import creates no run and grants no execution authority");
    const original = dialog.getByRole("region", { name: "Original imported evidence report", exact: true });
    await expect(original).toContainText("valid");
    await expect(dialog).toContainText("6 recorded evaluations");
    await page.keyboard.press("Escape"); await expect(dialog).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Import evidence", exact: true })).toBeFocused();
    await report(page, info, width, result, { importedBundleId: value.bundleId, runId: source.runId, snapshotId: source.snapshotId, inertImport: true });
  });

  for (const kind of ["project", "evidence"] as const) {
    test(`native ${kind} export refusal retains focus and actual retry at ${width}`, async ({ page }, info) => {
      const { source } = await open(page, info, width, kind), route = kind === "project" ? `/api/v1/projects/${source.projectId}/exports` : `/api/v1/runs/${source.runId}/exports`;
      await page.route("**" + route, handler => handler.fulfill({ status: 503, json: { code: "EXPORT_KEYBOARD_FIXTURE", message: "Labelled export refusal; retry explicitly.", retryable: true } }), { times: 1 });
      let downloads = 0; page.on("download", () => downloads++);
      await activate(page, action(page, kind));
      await expect(page.getByRole("alert")).toContainText("EXPORT_KEYBOARD_FIXTURE");
      await expect(action(page, kind)).toBeFocused(); expect(downloads).toBe(0);
      const result = await download(page, info, kind); expect(downloads).toBe(1);
      await report(page, info, width, result, { fixture: "One labelled503 before backend acceptance; actual retry and ZIP", refusedAttemptDownloads: 0 });
    });
  }
}
