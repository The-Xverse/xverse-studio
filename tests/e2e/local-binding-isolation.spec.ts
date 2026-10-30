import { test, expect } from "@playwright/test";
import { connectStudio } from "./connect-studio";

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test(`private declarations preserve browser authoring at ${viewport.width}`, async ({ page }, info) => {
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const proof = await page.evaluate(async (name) => {
      const session = await fetch("/api/v1/session").then((r) => r.json());
      const headers = { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken };
      const created = await fetch("/api/v1/projects", { method: "POST", headers, body: JSON.stringify({ name }) });
      if (created.status !== 201) throw Error("Owned project creation failed");
      const project = await created.json();
      const base = `/api/v1/projects/${project.projectId}`;
      const compile = () => fetch(`${base}/compilations`, { method: "POST", headers,
        body: JSON.stringify({ revision: project.revision }) }).then((r) => r.json());
      const before = await compile();
      const candidates = ["fixture:model-a", "fixture:model-b"].map((assetId) => ({ bindings: [{
        kind: "asset", bindingId: "model", reference: "urn:fixture:model", providerId: "uninstalled.fixture", assetId,
      }] }));
      const writes = await Promise.all(candidates.map((body) => fetch(`${base}/local-bindings`, {
        method: "PUT", headers: { ...headers, "If-Match": '"0"' }, body: JSON.stringify(body),
      })));
      const current = await fetch(`${base}/local-bindings`).then((r) => r.json());
      const after = await compile();
      const unchanged = await fetch(base).then((r) => r.json());
      localStorage.setItem("studio.projectId", project.projectId);
      return { project, unchanged, before, after, statuses: writes.map((r) => r.status).sort(), current };
    }, `Browser private isolation ${viewport.width}`);
    expect(proof.statuses).toEqual([200, 412]);
    expect(proof.current.bindingRevision).toBe(1);
    expect(proof.current.state).toBe("declared");
    expect(proof.current.validation).toBe("unverified");
    expect(proof.current.executionAllowed).toBe(false);
    expect(proof.unchanged).toEqual(proof.project);
    expect(proof.before.valid).toBe(true);
    expect(proof.after.planDigest).toBe(proof.before.planDigest);
    expect(proof.after.semanticDigest).toBe(proof.before.semanticDigest);
    await page.reload();
    await expect(page.getByRole("heading", { name: proof.project.name, exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Validate", exact: true }).click();
    await expect(page.getByText("Authoritative platform validation passed.", { exact: false })).toBeVisible();
    await page.reload();
    await expect(page.getByRole("heading", { name: proof.project.name, exact: true })).toBeVisible();
    const reopened = await page.request.get(`/api/v1/projects/${proof.project.projectId}/local-bindings`);
    expect(await reopened.json()).toEqual(proof.current);
    const runs = await page.request.get(`/api/v1/runs?projectId=${proof.project.projectId}`).then((r) => r.json());
    expect(runs.items).toEqual([]);
    await info.attach("binding-isolation-scope", { body: JSON.stringify({ viewport,
      nativeBrowser: true, actualAuthenticatedCAS: true, sourceAndPlanUnchanged: true,
      declarationForms: "not part of this storage component", workloadDispatch: false }), contentType: "application/json" });
  });
}
