import { test, expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { parse } from "yaml";
import { connectStudio } from "../e2e/connect-studio";
import { renderedContrast } from "../e2e/contrast";

const context = () => JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "playback-recording.private.json"), "utf8"));
const button = (page: Page, name: string) => page.getByRole("button", { name, exact: true });
async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let step = 0; step < 600; step++) {
    if (await target.evaluate(node => node === document.activeElement)) {
      expect(await target.evaluate(node => {
        const s = getComputedStyle(node), r = node.getBoundingClientRect();
        return s.outlineStyle !== "none" && parseFloat(s.outlineWidth) >= 2 &&
          r.left >= 0 && r.right <= innerWidth + 1 && r.top >= 0 && r.bottom <= innerHeight + 1;
      })).toBe(true);
      return;
    }
    await page.keyboard.press("Tab");
  }
  throw Error("Required scenario control is unreachable through native Tab order");
}
async function activate(page: Page, target: Locator) {
  await tabTo(page, target);
  await page.keyboard.press("Enter");
}
async function type(page: Page, label: string, value: string) {
  await tabTo(page, page.getByLabel(label, { exact: true }));
  await page.keyboard.press("ControlOrMeta+A");
  await page.keyboard.insertText(value);
}
async function target(page: Page) {
  const select = page.getByLabel("Declared target", { exact: true });
  await tabTo(page, select);
  await page.keyboard.press("Home");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Tab");
  await expect(select).not.toHaveValue("");
}
async function project(page: Page) {
  const response = await page.request.get(`/api/v1/projects/${context().projectId}`);
  expect(response.status()).toBe(200);
  return response.json();
}
function scenario(p: any) {
  return Object.values(p.documents).map((d: any) => parse(d.content)).find((d: any) => d.kind === "Scenario");
}
async function open(page: Page, info: TestInfo, width: number) {
  await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  await connectStudio(page, info);
  await activate(page, button(page, "X-Verse Studio home"));
  const p = await project(page);
  await activate(page, page.locator(".project-list").getByRole("button").filter({ hasText: p.name }));
  await activate(page, page.getByRole("tab", { name: "Experiments", exact: true }));
  await activate(page, page.getByRole("tab", { name: "Scenario", exact: true }));
  await expect(page.getByRole("region", { name: "Scenario authoring", exact: true })).toBeVisible();
  return p;
}
async function saved(page: Page, opener: Locator) {
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(opener).toBeFocused();
}
async function remove(page: Page, kind: string, id: string, add: string) {
  const opener = button(page, `Remove ${kind} ${id}`);
  await activate(page, opener);
  await page.keyboard.press("Escape");
  await saved(page, opener);
  await activate(page, opener);
  await activate(page, button(page, "Remove draft item"));
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(opener).toHaveCount(0);
  await expect(button(page, add)).toBeFocused();
}
async function report(page: Page, info: TestInfo, width: number, writes: string[]) {
  expect(writes.every(p => p === `/api/v1/projects/${context().projectId}/edits`)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await info.attach("autoverse-authoring-keyboard.json", { body: JSON.stringify({
    width, writes, browser: await page.context().browser()?.version(),
    scope: "Copy-local actual Autoverse draft; native keyboard actions, visible focus and selected contrast; no provider/workload or assistive-technology certification",
  }), contentType: "application/json" });
}

for (const width of [1024, 1440]) {
  test(`native keyboard scenario conditions validate and preserve opaque intent at ${width}`, async ({ page }, info) => {
    const original = await open(page, info, width), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    const opener = button(page, "Edit initial conditions");
    await activate(page, opener);
    const dialog = page.getByRole("dialog", { name: "Edit scenario conditions", exact: true });
    await expect(dialog.getByRole("button", { name: "Close dialog" })).toBeFocused();
    await type(page, "Initial conditions (JSON object)", "[]");
    await activate(page, button(page, "Save scenario conditions"));
    const error = dialog.getByRole("alert");
    await expect(error).toContainText("Supply a nonempty JSON object");
    expect(await project(page)).toEqual(original);
    const contrast = await renderedContrast(error, "Scenario conditions validation error");
    expect(contrast.supported).toBe(true);
    if (contrast.supported) expect(contrast.ratio).toBeGreaterThanOrEqual(4.5);
    const initial = { ...scenario(original).spec.initialConditions, keyboardOpaque: { width, preserved: [1, "untouched"] } };
    await type(page, "Initial conditions (JSON object)", JSON.stringify(initial));
    await activate(page, button(page, "Save scenario conditions"));
    await saved(page, opener);
    const current = await project(page);
    expect(current.revision).toBe(original.revision + 1);
    expect(scenario(current).spec.initialConditions).toEqual(initial);
    await report(page, info, width, writes);
  });

  test(`native keyboard stimulus creation, source, edit and removal at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    const id = `keyboard-step-${width}`, add = button(page, "Add stimulus step"), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    const before = await project(page);
    await activate(page, add);
    await type(page, "Scenario item identifier", id);
    await target(page);
    await type(page, "Action payload (JSON object)", "[]");
    await activate(page, button(page, "Add scenario item"));
    await expect(page.getByRole("dialog").getByRole("alert")).toContainText("Supply a nonempty JSON object");
    expect(await project(page)).toEqual(before);
    const action = { parameter: "target", value: 1, opaque: { retained: width } };
    await type(page, "Action payload (JSON object)", JSON.stringify(action));
    await activate(page, button(page, "Add scenario item"));
    await saved(page, add);
    expect(scenario(await project(page)).spec.steps.find((x: any) => x.id === id).action).toEqual(action);
    const source = button(page, `View source for step ${id}`);
    await activate(page, source);
    await expect(page.getByRole("dialog")).toContainText(id);
    await page.keyboard.press("Escape");
    await saved(page, source);
    const edit = button(page, `Edit step ${id}`);
    await activate(page, edit);
    await type(page, "Scheduled at", "0.5");
    await activate(page, button(page, "Save scenario item"));
    await saved(page, edit);
    expect(scenario(await project(page)).spec.steps.find((x: any) => x.id === id).schedule.at).toBe(0.5);
    await remove(page, "step", id, "Add stimulus step");
    await report(page, info, width, writes);
  });

  test(`native keyboard observer and metric references refuse unsafe removal at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    const observer = `keyboard-observer-${width}`, metric = `keyboard-metric-${width}`, writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    const addObserver = button(page, "Add observer");
    await activate(page, addObserver);
    await type(page, "Scenario item identifier", observer);
    await target(page);
    await type(page, "Sampling intent", "Opaque authored sampling; no live observation.");
    await activate(page, button(page, "Add scenario item"));
    await saved(page, addObserver);
    const addMetric = button(page, "Add metric intent");
    await activate(page, addMetric);
    await type(page, "Scenario item identifier", metric);
    const choice = page.getByRole("group", { name: "Declared observers", exact: true }).getByLabel(observer, { exact: true });
    await tabTo(page, choice);
    await page.keyboard.press("Space");
    await expect(choice).toBeChecked();
    await type(page, "Metric acceptance intent", "Opaque authored acceptance; no verdict.");
    await activate(page, button(page, "Add scenario item"));
    await saved(page, addMetric);
    const before = await project(page), opener = button(page, `Remove observer ${observer}`);
    await activate(page, opener);
    await activate(page, button(page, "Remove draft item"));
    await expect(page.getByRole("dialog").getByRole("alert")).toContainText(/reference|observer|valid/i);
    expect(await project(page)).toEqual(before);
    await page.keyboard.press("Escape");
    await saved(page, opener);
    await remove(page, "metric", metric, "Add metric intent");
    await remove(page, "observer", observer, "Add observer");
    await report(page, info, width, writes);
  });

  test(`native keyboard opaque fault intent stays distinct from provider support at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    const id = `keyboard-fault-${width}`, add = button(page, "Add fault intent"), writes: string[] = [];
    page.on("request", r => { if (r.method() !== "GET") writes.push(new URL(r.url()).pathname); });
    await activate(page, add);
    await expect(page.getByRole("dialog")).toContainText("No compatible provider fault choices are declared");
    await type(page, "Scenario item identifier", id);
    await target(page);
    await type(page, "Activation intent", "Opaque activation; no runtime permission.");
    await type(page, "Recovery intent", "Opaque recovery; no runtime permission.");
    await activate(page, button(page, "Add scenario item"));
    await saved(page, add);
    const authored = scenario(await project(page)).spec.faults.find((x: any) => x.id === id);
    expect(authored.activation).toBe("Opaque activation; no runtime permission.");
    expect(authored.recovery).toBe("Opaque recovery; no runtime permission.");
    expect(authored.maturity).toBe("prototype");
    await remove(page, "fault", id, "Add fault intent");
    await report(page, info, width, writes);
  });
}
