import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { parse, stringify } from "yaml";
import { connectStudio } from "../e2e/connect-studio";

test("Actual Autoverse GUI fault schedules, original units and unsupported profile preservation", async ({ page }, info) => {
  const data = process.env.STUDIO_BROWSER_DATA;
  if (!data) throw Error("An owned native Autoverse host is required");
  const base = JSON.parse(readFileSync(path.join(data, "fault-authoring-project.private.json"), "utf8"));
  await connectStudio(page, info);
  await page.evaluate(id => localStorage.setItem("studio.projectId", id), base.projectId);
  async function open() {
    await page.reload();
    await expect(page.getByRole("heading", { name: base.name, exact: true })).toBeVisible();
    await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  }
  async function project() { return page.request.get(`/api/v1/projects/${base.projectId}`).then(r => r.json()); }
  async function put(p: any, key: string, content: string) {
    return page.evaluate(async ({ id, rev, key, content }) => {
      const session = await fetch("/api/v1/session").then(r => r.json());
      const response = await fetch(`/api/v1/projects/${id}/documents/${key}`, { method: "PUT", headers: { "Content-Type": "application/json", "If-Match": String(rev), "X-CSRF-Token": session.csrfToken }, body: JSON.stringify({ content }) });
      if (!response.ok) throw Error(`Controlled draft edit failed (${response.status})`);
      return response.json();
    }, { id: base.projectId, rev: p.revision, key, content });
  }
  async function restore(revision: number) {
    const p = await project();
    await page.evaluate(async ({ id, rev, old }) => {
      const session = await fetch("/api/v1/session").then(r => r.json());
      const response = await fetch(`/api/v1/projects/${id}/revisions/${old}/restore`, { method: "POST", headers: { "If-Match": String(rev), "X-CSRF-Token": session.csrfToken } });
      if (!response.ok) throw Error(`Controlled restoration failed (${response.status})`);
    }, { id: base.projectId, rev: p.revision, old: revision });
    await open();
  }
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.route("**/api/v1/providers", async route => {
    const response = await route.fetch(), body = await response.json();
    body.items.find((p: any) => p.providerId === "autoverse.demo").scenarioContracts.contractVersion = "unadmitted";
    await route.fulfill({ response, json: body });
  }, { times: 1 });
  await open();
  await page.getByRole("button", { name: "Add fault intent", exact: true }).click();
  await expect(page.getByRole("dialog").getByText("No compatible provider fault choices are declared.", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Close dialog", exact: true }).click();
  await open();
  for (const [id, at] of [["first-loss", 5], ["second-loss", 13], ["interrupted-loss", 21]] as const) {
    await page.getByRole("button", { name: "Add fault intent", exact: true }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Scenario item identifier", { exact: true }).fill(id);
    await dialog.getByLabel("Provider fault choice", { exact: true }).selectOption("0");
    await expect(dialog.getByLabel("Fault clock", { exact: true })).toHaveValue("host-runtime");
    await dialog.getByLabel("Fault activation time", { exact: true }).fill(String(at));
    await dialog.getByLabel("Fault duration", { exact: true }).fill("3");
    await dialog.getByRole("button", { name: "Add scenario item", exact: true }).click();
    await expect(dialog).toHaveCount(0);
    await expect(page.getByRole("button", { name: `Edit fault ${id}`, exact: true })).toBeVisible();
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByRole("button", { name: "Edit fault first-loss", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByLabel("Fault activation time", { exact: true })).toHaveValue("5");
  await dialog.getByLabel("Fault activation unit", { exact: true }).selectOption("ms");
  await dialog.getByLabel("Fault activation time", { exact: true }).fill("5000");
  await dialog.getByRole("button", { name: "Save scenario item", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  const authored = await project();
  const entries: [string, any][] = Object.entries(authored.documents);
  const [scenarioId, scenarioDoc] = entries.find(([, d]) => parse(d.content).kind === "Scenario")!;
  const scenario = parse(scenarioDoc.content);
  expect(scenario.spec.faults).toHaveLength(3);
  expect(scenario.spec.faults[0].extensions["io.xverse.experiment"].trigger).toEqual({ kind: "time", at: 5000, unit: "ms" });
  expect(scenario.spec.faults[0].extensions["io.xverse.experiment"].duration).toEqual({ value: 3, unit: "s" });
  const [profileId, profileDoc] = entries.find(([, d]) => { const r = parse(d.content); return r.kind === "Profile" && r.spec.extensionNamespace === "io.xverse.experiment"; })!;
  const profile = parse(profileDoc.content); profile.metadata.version = "9.0.0";
  await put(authored, profileId, stringify(profile));
  await open();
  await page.getByRole("button", { name: "Edit fault first-loss", exact: true }).click();
  await expect(page.getByRole("dialog").getByText("Timed fault authoring is unavailable", { exact: false })).toBeVisible();
  await expect(page.getByLabel("Fault activation time", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Close dialog", exact: true }).click();
  await restore(authored.revision);
  const restored = await project();
  const unsupported = parse(scenarioDoc.content); unsupported.spec.faults[0].extensions["io.xverse.experiment"].schemaVersion = "9.0";
  const opaque = stringify(unsupported);
  await put(restored, scenarioId, opaque);
  await open();
  await page.getByRole("button", { name: "Edit fault first-loss", exact: true }).click();
  await expect(page.getByRole("dialog").getByText("Timed fault authoring is unavailable", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Save scenario item", exact: true }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toBeVisible();
  expect((await project()).documents[scenarioId].content).toBe(opaque);
  await page.getByRole("button", { name: "Close dialog", exact: true }).click();
  await restore(authored.revision);
  const final = await project();
  expect(final.documents).toEqual(authored.documents);
  const panel = page.getByRole("region", { name: "Scenario support and observation budgets", exact: true });
  await panel.getByRole("button", { name: "Inspect scenario support", exact: true }).click();
  await expect(panel.getByText("Preflight required", { exact: true })).toBeVisible();
  expect((await page.request.get(`/api/v1/runs?projectId=${base.projectId}`).then(r => r.json())).items).toEqual([]);
  await page.screenshot({ path: info.outputPath("authored-faults.png"), fullPage: true });
  await info.attach("autoverse-gui-fault-source", { body: JSON.stringify({ projectId: base.projectId, revision: final.revision, faultIds: scenario.spec.faults.map((f: any) => f.id), originalUnitsPreserved: true, unsupportedProfileAndPayloadPreserved: true, viewports: [1024, 1440], runtimeStartedByBrowser: false }), contentType: "application/json" });
});
