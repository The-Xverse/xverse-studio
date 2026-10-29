import { test, expect, type Locator, type Page } from "@playwright/test";
import { parse } from "yaml";
import { createHash } from "node:crypto";
import { connectStudio } from "./connect-studio";
import { renderedContrast } from "./contrast";

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 160; i++) {
    if (await target.evaluate((node) => document.activeElement === node)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error("Wizard control is unreachable through native Tab order");
}
async function activate(page: Page, target: Locator) {
  await tabTo(page, target);
  await page.keyboard.press("Enter");
}
async function type(page: Page, target: Locator, value: string) {
  await tabTo(page, target);
  await page.keyboard.press("ControlOrMeta+A");
  await page.keyboard.insertText(value);
}
async function choose(page: Page, target: Locator, value: string) {
  const options = await target.locator("option").evaluateAll((nodes) => nodes.map((n) => (n as HTMLOptionElement).value));
  const index = options.indexOf(value);
  expect(index).toBeGreaterThanOrEqual(0);
  await tabTo(page, target);
  await page.keyboard.press("Home");
  for (let i = 0; i < index; i++) await page.keyboard.press("ArrowDown");
  await expect(target).toHaveValue(value);
}
async function radio(page: Page, group: Locator, target: Locator) {
  // A native radio group has one Tab stop. Arrow keys visit its other options.
  for (let i = 0; i < 160; i++) {
    if (await group.evaluate((node) => node.contains(document.activeElement) && (document.activeElement as HTMLInputElement)?.type === "radio")) break;
    await page.keyboard.press("Tab");
  }
  const count = await group.getByRole("radio").count();
  for (let i = 0; i < count; i++) {
    if (await target.evaluate((node) => node === document.activeElement)) {
      await page.keyboard.press("Space");
      await expect(target).toBeChecked();
      return;
    }
    await page.keyboard.press("ArrowDown");
  }
  throw new Error("Radio option is unreachable through the group's native arrow navigation");
}
async function focusGeometry(target: Locator) {
  return target.evaluate((node) => {
    const rect = node.getBoundingClientRect(), style = getComputedStyle(node), clips: { top: number; right: number; bottom: number; left: number }[] = [];
    for (let parent = node.parentElement; parent; parent = parent.parentElement) {
      const paint = getComputedStyle(parent);
      if (/(auto|scroll|hidden|clip)/.test(paint.overflowX + paint.overflowY)) {
        const box = parent.getBoundingClientRect();
        clips.push({ left: box.left + parent.clientLeft, top: box.top + parent.clientTop,
          right: box.left + parent.clientLeft + parent.clientWidth, bottom: box.top + parent.clientTop + parent.clientHeight });
      }
    }
    return { focused: document.activeElement === node, activeTag: document.activeElement?.tagName, rect: rect.toJSON(), clips,
      outline: style.outlineStyle, outlineWidth: parseFloat(style.outlineWidth),
      viewport: { width: innerWidth, height: innerHeight } };
  });
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
for (const mode of ["depart", "focus elsewhere", "newer head"] as const) {
test(`wizard accessibility: late history ${mode} at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
  test.setTimeout(90000);
  await page.setViewportSize(viewport);
  await connectStudio(page, testInfo);
  const project = await page.evaluate(async (name) => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const response = await fetch("/api/v1/projects", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify({ name }) });
    if (!response.ok) throw Error("Owned history fixture failed");
    const value = await response.json(); localStorage.setItem("studio.projectId", value.projectId); return value;
  }, `Late keyboard history ${mode} ${viewport.width}`);
  await page.reload();
  await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
  await activate(page, page.getByRole("button", { name: "Parameters", exact: true }));
  await type(page, page.getByLabel("Duration"), "6");
  await activate(page, page.getByLabel("Duration").locator("xpath=ancestor::form").getByRole("button", { name: "Apply", exact: true }));
  await expect(page.locator(".alerts")).toContainText("Draft saved");
  let release!: () => void, prepared = false, routeFinished: Promise<void> | undefined;
  const held = new Promise<void>((resolve) => { release = resolve; });
  const pattern = `**/api/v1/projects/${project.projectId}/revisions/*/restore`;
  await page.route(pattern, async (route) => {
    let finish!: () => void;
    routeFinished = new Promise<void>((resolve) => { finish = resolve; });
    try { const response = await route.fetch(); prepared = true; await held; await route.fulfill({ response }); }
    finally { finish(); }
  });
  try {
    await activate(page, page.getByRole("button", { name: "Undo", exact: true }));
    await expect.poll(() => prepared).toBe(true);
    const home = page.getByRole("button", { name: "X-Verse Studio home", exact: true });
    await tabTo(page, home);
    let newerHead: string | null = null, newerRevision: number | null = null;
    if (mode !== "focus elsewhere") {
      await page.keyboard.press("Enter");
      await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
    }
    if (mode === "newer head") {
      await activate(page, page.locator(`.project-list-row[data-project-id="${project.projectId}"] .project-open`));
      await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
      if (!(await page.getByLabel("Duration").isVisible())) await activate(page, page.getByRole("button", { name: "Parameters", exact: true }));
      await type(page, page.getByLabel("Duration"), "7");
      await activate(page, page.getByLabel("Duration").locator("xpath=ancestor::form").getByRole("button", { name: "Apply", exact: true }));
      await expect(page.locator(".alerts")).toContainText("Draft saved");
      newerHead = await page.evaluate((id) => sessionStorage.getItem("studio.graphHistory." + id), project.projectId);
      newerRevision = (await page.request.get(`/api/v1/projects/${project.projectId}`).then((r) => r.json())).revision;
      expect(newerRevision).toBe(project.revision + 3);
      await tabTo(page, home);
    }
    const focused = await page.evaluate(() => document.activeElement?.getAttribute("aria-label"));
    const done = page.waitForResponse((r) => new URL(r.url()).pathname.endsWith("/restore") && r.request().method() === "POST");
    release(); await done;
    await expect(page.locator(".notice.busy")).toHaveCount(0);
    if (mode === "depart") {
      await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
      const retained = await page.evaluate((id) => JSON.parse(sessionStorage.getItem("studio.graphHistory." + id) || "null"), project.projectId);
      expect(retained.redo[retained.redo.length - 1].at).toBe(project.revision + 2);
    } else await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
    await expect(home).toBeFocused();
    if (mode === "newer head") {
      expect(await page.evaluate((id) => sessionStorage.getItem("studio.graphHistory." + id), project.projectId)).toBe(newerHead);
      await expect(page.getByLabel("Duration")).toHaveValue("7");
      await expect(page.locator(".project-header .revision")).toHaveText(`rev ${newerRevision}`);
    }
    await testInfo.attach("late-history-navigation.json", { body: JSON.stringify({ viewport, mode, realOwnedRestore: true, currentIntentPreserved: true, newerRevision, newerHeadPreserved: mode === "newer head", focusedBeforeRelease: focused, noRunRequested: true,
      browser: await page.context().browser()?.version(), platform: process.platform }), contentType: "application/json" });
  } finally { release(); if (routeFinished) await routeFinished; await page.unroute(pattern); }
});
}
}
function checkFocus(value: Awaited<ReturnType<typeof focusGeometry>>) {
  expect(value.focused).toBe(true);
  expect(value.outline).not.toBe("none");
  expect(value.outlineWidth).toBeGreaterThanOrEqual(2);
  for (const clip of [{ left: 0, top: 0, right: value.viewport.width, bottom: value.viewport.height }, ...value.clips]) {
    expect(value.rect.left).toBeGreaterThanOrEqual(clip.left - 1);
    expect(value.rect.top).toBeGreaterThanOrEqual(clip.top - 1);
    expect(value.rect.right).toBeLessThanOrEqual(clip.right + 1);
    expect(value.rect.bottom).toBeLessThanOrEqual(clip.bottom + 1);
  }
}
function source(project: any, suffix: string): string {
  return (Object.values(project.documents) as any[]).find((d) => d.path.endsWith("/" + suffix)).content;
}
const hash = (text: string) => createHash("sha256").update(text).digest("hex");

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test(`wizard accessibility: native keyboard instance, placement and binding at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
    test.setTimeout(120000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    const project = await page.evaluate(async (width) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
      const response = await fetch("/api/v1/projects", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify({ name: `Keyboard instance ${width}` }) });
      if (!response.ok) throw Error("Owned project setup failed");
      const value = await response.json(); localStorage.setItem("studio.projectId", value.projectId); return value;
    }, viewport.width);
    const runsBefore = await page.request.get("/api/v1/runs").then((r) => r.json());
    await page.reload();
    await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
    const writes: { method: string; path: string; body: any }[] = [];
    page.on("request", (r) => {
      if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method())) writes.push({ method: r.method(), path: new URL(r.url()).pathname, body: r.postDataJSON() });
    });
    const geometry: { step: string; value: Awaited<ReturnType<typeof focusGeometry>> }[] = [];
    const measurements: Awaited<ReturnType<typeof renderedContrast>>[] = [];
    const add = page.getByRole("button", { name: "Add element", exact: true });
    const dialog = page.getByRole("dialog", { name: "Add Unit", exact: true });
    const instance = `keyboard-plant-${viewport.width}`;
    try {
      await activate(page, add);
      await expect(dialog.getByLabel("Element family")).toHaveValue("component");
      const definitions = dialog.getByRole("radiogroup", { name: "Definitions" });
      const plant = definitions.getByRole("radio", { name: /reference-plant org\.xverse\.studio\.process-control/ });
      await radio(page, definitions, plant);
      geometry.push({ step: "definition radio", value: await focusGeometry(plant) });
      const identifier = dialog.getByLabel("Instance identifier"), submit = dialog.getByRole("button", { name: "Add instance", exact: true });
      await type(page, identifier, "Bad_ID");
      await expect(submit).toBeDisabled();
      await expect(dialog.getByRole("region", { name: "Review" }).getByRole("status")).toContainText("lowercase, hyphenated instance identifier");
      expect(writes).toEqual([]);
      measurements.push(await renderedContrast(dialog.getByRole("status"), "Rejected identifier status"));
      await type(page, identifier, instance);
      measurements.push(await renderedContrast(identifier.locator("xpath=ancestor::fieldset").locator(".field-hint"), "Instance identity explanation"));
      await choose(page, dialog.getByLabel("Role filter"), "plant");
      await choose(page, dialog.getByLabel("Placement node"), "plant-node");
      measurements.push(await renderedContrast(dialog.getByLabel("Placement node").locator("xpath=ancestor::fieldset").locator(".field-hint"), "Role and placement explanation"));
      const variant = dialog.getByLabel("Deployment variant");
      const variantId = await variant.locator("option").filter({ hasText: /^local-reference$/ }).getAttribute("value");
      expect(variantId).toBeTruthy();
      await choose(page, variant, variantId!);
      await expect(submit).toBeDisabled();
      await radio(page, dialog.getByRole("radiogroup", { name: "Realization class" }), dialog.getByRole("radio", { name: "simulated", exact: true }));
      await choose(page, dialog.getByLabel("Deployment target"), "reference-target");
      const artifact = dialog.getByRole("checkbox", { name: /reference-model/ });
      await tabTo(page, artifact); await page.keyboard.press("Space"); await expect(artifact).toBeChecked();
      const review = dialog.getByRole("region", { name: "Review" });
      await expect(review.getByRole("listitem")).toHaveText([
        `Add instance ${instance} of reference-plant on node plant-node`,
        new RegExp(`^Bind ${instance} as simulated to target reference-target \\(${instance}-binding\\)`),
      ]);
      await expect(review).toContainText("Nothing is built, flashed or executed");
      await tabTo(page, submit);
      geometry.push({ step: "long wizard submit", value: await focusGeometry(submit) });
      measurements.push(await renderedContrast(review.locator(".field-hint"), "No execution or provider authority explanation"));
      const edited = page.waitForResponse((r) => new URL(r.url()).pathname === `/api/v1/projects/${project.projectId}/edits` && r.request().method() === "POST");
      await page.keyboard.press("Enter"); expect((await edited).status()).toBe(200);
      await expect(dialog).toHaveCount(0);
      await expect(add).toBeFocused();
      geometry.push({ step: "returned Add element", value: await focusGeometry(add) });
      expect(writes.map((r) => r.method + " " + r.path)).toEqual([`POST /api/v1/projects/${project.projectId}/edits`]);
      expect(writes[0].body.edits.map((e: any) => e.kind)).toEqual(["add_element", "add_binding"]);
      const saved = await page.request.get(`/api/v1/projects/${project.projectId}`).then((r) => r.json());
      expect(saved.revision).toBe(project.revision + 1);
      const system = parse(source(saved, "system.xdl.yaml")), deployment = parse(source(saved, "deployment.xdl.yaml"));
      expect(system.spec.componentInstances.find((c: any) => c.id === instance)).toMatchObject({ componentRef: { name: "reference-plant" }, nodeId: "plant-node" });
      expect(deployment.spec.bindings.find((b: any) => b.id === `${instance}-binding`)).toMatchObject({ logicalRef: { element: instance }, realizationClass: "simulated", targetId: "reference-target", artifactIds: ["reference-model"] });
      expect(source(saved, "plant.xdl.yaml")).toBe(source(project, "plant.xdl.yaml"));
      // Recover a mistaken creation and restore it through the same keyboard workflow.
      const undo = page.getByRole("button", { name: "Undo", exact: true });
      const redo = page.getByRole("button", { name: "Redo", exact: true });
      await activate(page, undo);
      await expect(page.locator(".alerts")).toContainText("Undid a graph edit");
      await expect(page.locator(".notice.busy")).toHaveCount(0);
      geometry.push({ step: "Undo completion offers Redo", value: await focusGeometry(redo) });
      const undone = await page.request.get(`/api/v1/projects/${project.projectId}`).then((r) => r.json());
      expect(undone.revision).toBe(saved.revision + 1);
      for (const name of ["system.xdl.yaml", "deployment.xdl.yaml", "plant.xdl.yaml"]) expect(source(undone, name)).toBe(source(project, name));
      await expect(redo).toBeFocused();
      await page.keyboard.press("ControlOrMeta+Shift+z");
      await expect(page.locator(".alerts")).toContainText("Redid a graph edit");
      await expect(page.locator(".notice.busy")).toHaveCount(0);
      geometry.push({ step: "Shortcut Redo completion offers Undo", value: await focusGeometry(undo) });
      const redone = await page.request.get(`/api/v1/projects/${project.projectId}`).then((r) => r.json());
      expect(redone.revision).toBe(undone.revision + 1);
      for (const name of ["system.xdl.yaml", "deployment.xdl.yaml", "plant.xdl.yaml"]) expect(source(redone, name)).toBe(source(saved, name));
      await page.keyboard.press("ControlOrMeta+z");
      await expect(page.locator(".alerts")).toContainText("Undid a graph edit");
      await expect(page.locator(".notice.busy")).toHaveCount(0);
      geometry.push({ step: "Shortcut Undo completion offers Redo", value: await focusGeometry(redo) });
      const undoneAgain = await page.request.get(`/api/v1/projects/${project.projectId}`).then((r) => r.json());
      expect(undoneAgain.revision).toBe(redone.revision + 1);
      for (const name of ["system.xdl.yaml", "deployment.xdl.yaml", "plant.xdl.yaml"]) expect(source(undoneAgain, name)).toBe(source(project, name));
      await activate(page, redo);
      await expect(page.locator(".alerts")).toContainText("Redid a graph edit");
      await expect(page.locator(".notice.busy")).toHaveCount(0);
      geometry.push({ step: "Final Redo completion offers Undo", value: await focusGeometry(undo) });
      const finalProject = await page.request.get(`/api/v1/projects/${project.projectId}`).then((r) => r.json());
      expect(finalProject.revision).toBe(undoneAgain.revision + 1);
      for (const name of ["system.xdl.yaml", "deployment.xdl.yaml", "plant.xdl.yaml"]) expect(source(finalProject, name)).toBe(source(saved, name));
      const validation = page.waitForResponse((r) => new URL(r.url()).pathname === `/api/v1/projects/${project.projectId}/validations` && r.request().method() === "POST");
      await activate(page, page.getByRole("button", { name: "Validate", exact: true }));
      expect((await (await validation).json()).valid).toBe(true);
      const runsAfter = await page.request.get("/api/v1/runs").then((r) => r.json());
      expect(runsAfter.items.filter((r: any) => r.projectId === project.projectId).map((r: any) => r.runId).sort()).toEqual(runsBefore.items.filter((r: any) => r.projectId === project.projectId).map((r: any) => r.runId).sort());
      await testInfo.attach("wizard-semantics.json", { body: JSON.stringify({ viewport, projectId: project.projectId, initialRevision: project.revision, savedRevision: saved.revision,
        transactionKinds: writes[0].body.edits.map((e: any) => e.kind), systemElement: instance, placement: "plant-node", realization: "simulated", binding: `${instance}-binding`,
        definitionBeforeSha256: hash(source(project, "plant.xdl.yaml")), definitionAfterSha256: hash(source(saved, "plant.xdl.yaml")), authoritativeValidation: true, projectRunSetUnchanged: true,
        undoRevision: undone.revision, redoRevision: redone.revision, shortcutUndoRevision: undoneAgain.revision, finalRedoRevision: finalProject.revision,
        undoRestoresInitialBytes: true, redoRestoresCreatedBytes: true }), contentType: "application/json" });
    } finally {
      await testInfo.attach("wizard-keyboard-observations.json", { body: JSON.stringify({ viewport, browser: await page.context().browser()?.version(), platform: process.platform,
        geometry, measurements, writes, scope: "Native keyboard authoring against owned Linux backend; no build/flash/run/device action", limitations: ["No native Windows or actual screen-reader execution", "Selected controls/text and paint only"] }), contentType: "application/json" });
    }
    for (const step of geometry) checkFocus(step.value);
    for (const pair of measurements) {
      expect.soft(pair.supported, pair.label).toBe(true);
      if (pair.supported) expect.soft(pair.ratio, pair.label).toBeGreaterThanOrEqual(4.5);
    }
  });
}
