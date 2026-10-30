import { test, expect } from "@playwright/test";
import { connectStudio } from "../e2e/connect-studio";

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test(`Autoverse installed admission and authoring at ${viewport.width}`, async ({ page }, info) => {
    const fault = process.env.STUDIO_AUTOVERSE_DESCRIPTOR_FAULT;
    if (fault !== "valid" && fault !== "invalid") throw Error("An explicit native Autoverse descriptor check is required");
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const proof = await page.evaluate(async (name) => {
      const session = await fetch("/api/v1/session").then((r) => r.json());
      const headers = { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken };
      const create = await fetch("/api/v1/projects", { method: "POST", headers, body: JSON.stringify({ name, blueprintRef: "autoverse-classic" }) });
      if (create.status !== 201) throw Error("Actual Autoverse authoring target could not be created");
      const project = await create.json();
      const providers = await fetch("/api/v1/providers").then((r) => r.json());
      const preflight = await fetch(`/api/v1/projects/${project.projectId}/preflights`, { method: "POST", headers,
        body: JSON.stringify({ revision: project.revision, providerId: "autoverse.demo" }) }).then((r) => r.json());
      localStorage.setItem("studio.projectId", project.projectId);
      return { project, preflight, provider: providers.items.find((p: {providerId: string}) => p.providerId === "autoverse.demo") };
    }, `Autoverse admission ${fault} ${viewport.width}`);
    expect(proof.provider.available).toBe(fault === "valid");
    expect(proof.preflight.status).toBe(fault === "valid" ? "ready" : "blocked");
    expect(proof.preflight.providerId).toBe("autoverse.demo");
    if (fault === "invalid") {
      expect(proof.provider.operations).toEqual([]);
      expect(proof.provider.blockedReasons[0].code).toBe("PROVIDER_DESCRIPTOR_INVALID");
    }
    await page.reload();
    await expect(page.getByRole("heading", { name: proof.project.name, exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Validate", exact: true }).click();
    await expect(page.getByText("Authoritative platform validation passed.", { exact: false })).toBeVisible();
    await page.getByRole("button", { name: "Environment", exact: true }).click();
    const provider = page.locator("section").filter({ has: page.getByRole("heading", {
      name: fault === "valid" ? "Autoverse complete demo" : "autoverse.demo", exact: true }) });
    await expect(provider.getByText(fault === "valid" ? "Available" : "Unavailable", { exact: true })).toBeVisible();
    if (fault === "invalid") await expect(provider.getByText(proof.provider.blockedReasons[0].message, { exact: true })).toBeVisible();
    const runs = await page.request.get(`/api/v1/runs?projectId=${proof.project.projectId}`).then((r) => r.json());
    expect(runs.items).toEqual([]);
    await info.attach("autoverse-admission", { body: JSON.stringify({ viewport, descriptorFault: fault,
      target: "actual enrolled Autoverse complete demo", nativeBrowser: true,
      actualReadiness: proof.preflight.status, authoringAvailable: true, runtimeStarted: false }), contentType: "application/json" });
  });
}
