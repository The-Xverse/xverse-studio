import { expect, type Page } from "@playwright/test";

/** Actual UI + server authoring before the complete native demo. No response mocks. */
export async function inspectAutoverseComposition(page: Page, original: { projectId: string; revision: number }) {
  const pid = "autoverse.demo";
  await page.getByRole("tab", { name: "Connections", exact: true }).click();
  await expect(page.getByRole("button", { name: /^Admission admitted; show checks for/ }).first()).toBeVisible();
  await expect(page.getByText(pid, { exact: true }).first()).toBeVisible();
  const admission = await page.request.get(`/api/v1/projects/${original.projectId}/connections?providerId=${pid}`).then(r => r.json());
  expect(admission.providerId).toBe(pid); expect(admission.blocking).toBe(0);
  expect(admission.cycles.length).toBeGreaterThan(0);
  expect(admission.cycles.every((c: any) => c.status === "admitted")).toBe(true);
  await page.getByRole("tab", { name: "Deployment", exact: true }).click();
  const resolution = page.locator(".resolution-summary");
  await expect(resolution).toContainText(pid);
  await expect(resolution).toContainText("no blocking findings");
  const before = await page.request.get(`/api/v1/projects/${original.projectId}/deployment-variants`).then(r => r.json());
  expect(before.items).toHaveLength(1);
  await page.getByLabel("New variant name", { exact: true }).fill("Autoverse browser alternative");
  await page.getByRole("button", { name: "Create deployment variant", exact: true }).click();
  await expect(page.getByLabel("Deployment variant", { exact: true }).locator("option")).toHaveCount(3);
  const variants = await page.request.get(`/api/v1/projects/${original.projectId}/deployment-variants`).then(r => r.json());
  const other = variants.items.find((v: any) => v.ref !== before.items[0].ref);
  expect(other).toBeTruthy();
  const selected = await page.getByLabel("Deployment variant", { exact: true }).inputValue();
  await page.getByLabel("Comparison variant", { exact: true }).selectOption(selected === other.ref ? before.items[0].ref : other.ref);
  const comparison = page.getByRole("region", { name: "Time, control and physical evidence", exact: true });
  await expect(comparison).toContainText(pid);
  await expect(comparison).toContainText("Unverified");
  await expect(comparison).toContainText("Fresh preflight required");
  // The server compares one captured project and the actual installed descriptor.
  const compared = await page.request.get(`/api/v1/projects/${original.projectId}/deployment-variants/${before.items[0].documentId}/comparison?otherDocumentId=${other.documentId}&revision=${variants.revision}&providerId=${pid}`).then(r => r.json());
  expect(compared.providerId).toBe(pid);
  expect(compared.left.resolution.providerId).toBe(pid); expect(compared.right.resolution.providerId).toBe(pid);
  expect(compared.fidelity).toBe("unverified"); expect(compared.physicalState).toBe("unknown");
  // Restore exact supported inputs as a new forward revision before preflight.
  const restored = await page.evaluate(async ({ projectId, revision, oldRevision }) => {
    const s = await fetch("/api/v1/session").then(r => r.json());
    const r = await fetch(`/api/v1/projects/${projectId}/revisions/${oldRevision}/restore`, {
      method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": s.csrfToken, "If-Match": String(revision) },
    });
    if (!r.ok) throw Error(`Original supported source restoration failed (${r.status})`);
    return r.json();
  }, { projectId: original.projectId, revision: variants.revision, oldRevision: original.revision });
  expect(restored.revision).toBeGreaterThan(variants.revision);
  await page.reload();
  // Restoring through the API deliberately leaves browser selection untouched.
  // Choose the restored authored pair through the real UI before preflight.
  await page.getByRole("tab", { name: "Deployment", exact: true }).click();
  await page.getByLabel("Deployment variant", { exact: true }).selectOption(before.items[0].ref);
  await expect(page.getByLabel("Associated Scenario", { exact: true })).toHaveValue(before.items[0].scenarioRefs[0]);
  await expect(page.getByRole("button", { name: "Preflight & run", exact: true })).toBeVisible();
  return { providerId: pid, admittedConnections: admission.connections.length, admittedCycles: admission.cycles.length, browserViews: ["Connections", "Deployment", "Comparison"], variantsCreated: 1, restoredRevision: restored.revision, fidelity: compared.fidelity, physicalState: compared.physicalState };
}

export async function inspectAutoverseCommunication(page: Page, projectId: string, runId: string) {
  const report = await page.request.get(`/api/v1/projects/${projectId}/communication?runId=${runId}`).then(r => r.json());
  expect(report.providerId).toBe("autoverse.demo"); expect(report.runId).toBe(runId);
  expect(report.flows.length).toBeGreaterThan(0);
  expect(report.flows.every((f: any) => f.declared.status === "declared")).toBe(true);
  // Classic canonical records do not provide an admitted per-flow route/observer
  // mapping. Preserve that unavailable scope instead of fabricating native traffic.
  expect(report.flows.every((f: any) => f.resolved.status === "not_resolved")).toBe(true);
  expect(report.flows.every((f: any) => ["not_collected", "collected_none"].includes(f.observed.status))).toBe(true);
  const refusals = await page.evaluate(async (runId) => {
    const session = await fetch("/api/v1/session").then(r => r.json());
    const outcomes = [];
    for (const kind of ["pause", "resume", "step", "reset", "set_parameter"]) {
      const live = await fetch(`/api/v1/runs/${runId}`).then(r => r.json());
      const response = await fetch(`/api/v1/runs/${runId}/commands`, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken, "Idempotency-Key": `composition-unsupported-${kind}` }, body: JSON.stringify({ kind, expectedStateVersion: live.stateVersion }) });
      outcomes.push({ kind, status: response.status, code: (await response.json()).code });
    }
    return outcomes;
  }, runId);
  for (const r of refusals) { expect(r.status).toBe(422); expect(r.code).toBe("CAPABILITY_UNSUPPORTED"); }
  return { providerId: report.providerId, runId, flowCount: report.flows.length, resolvedStatuses: [...new Set(report.flows.map((f: any) => f.resolved.status))], observedStatuses: [...new Set(report.flows.map((f: any) => f.observed.status))], unsupportedCommandRefusals: refusals };
}
