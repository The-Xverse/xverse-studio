import { test, expect } from "@playwright/test";
import { connectStudio } from "./connect-studio";

// Authoring/exchange on a native Studio host without Autoverse enrollment.
// This deliberately establishes no simulator, Android or Lite execution claim.
for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test(`existing Autoverse development blueprint survives exchange at ${viewport.width}`, async ({ page }, info) => {
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    await page.getByRole("button", { name: "X-Verse Studio home", exact: true }).click();
    await page.locator(".example-grid").getByRole("button", { name: /Autoverse with X-Verse platform/ }).click();
    await expect(page.locator(".project-header h1")).toHaveText("Autoverse with X-Verse platform");
    await expect(page.getByRole("status", { name: "Selected provider scope" })).toContainText("autoverse.platform");
    await page.getByRole("button", { name: "Validate", exact: true }).click();
    await expect(page.getByText("Authoritative platform validation passed.", { exact: false })).toBeVisible();
    const projectId = await page.evaluate(() => localStorage.getItem("studio.projectId"));
    expect(projectId).toBeTruthy();
    const original = await page.request.get(`/api/v1/projects/${projectId}`).then(r => r.json());
    expect(Object.keys(original.documents)).toHaveLength(8);
    const session = await page.request.get("/api/v1/session").then(r => r.json());
    const headers = { Origin: new URL(page.url()).origin, "X-CSRF-Token": session.csrfToken };
    const compilation = await page.request.post(`/api/v1/projects/${projectId}/compilations`, {
      headers,
      data: { revision: original.revision },
    });
    expect(compilation.status()).toBe(200);
    const compiled = await compilation.json();
    expect(compiled.valid).toBe(true);
    expect(compiled.plan.bindings.map((b: any) => b.logicalRef.element).sort()).toEqual(
      ["android", "carla", "driver", "score", "someip-bridge", "vcu"],
    );
    await page.getByRole("tab", { name: "Connections", exact: true }).click();
    await expect(page.getByRole("tab", { name: "Connections", exact: true })).toHaveAttribute("aria-selected", "true");
    const reply = page.waitForResponse(r => r.url().endsWith(`/projects/${projectId}/preflights`) && r.request().method() === "POST");
    await page.getByRole("button", { name: "Preflight & run", exact: true }).click();
    const preflight = await (await reply).json();
    expect(preflight.providerId).toBe("autoverse.platform");
    expect(preflight.status).toBe("blocked");
    await expect(page.getByRole("button", { name: "Start frozen snapshot", exact: true })).toBeDisabled();
    await expect(page.getByRole("region", { name: "Readiness diagnostics" })).toContainText("PROVIDER_UNAVAILABLE");
    await page.getByRole("button", { name: "Back to draft", exact: true }).click();
    await page.getByRole("tab", { name: "Model", exact: true }).click();
    await expect(page.getByRole("status", { name: "Selected provider scope" })).toContainText("autoverse.platform");
    await page.screenshot({ path: info.outputPath("autoverse-development-model.png") });
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Export", exact: true }).click();
    const archive = info.outputPath("autoverse-development.zip");
    await (await download).saveAs(archive);
    await page.getByRole("button", { name: "X-Verse Studio home", exact: true }).click();
    await page.getByLabel("Import project archive").setInputFiles(archive);
    await expect(page.locator(".project-header h1")).toHaveText("Autoverse with X-Verse platform");
    const copiedId = await page.evaluate(() => localStorage.getItem("studio.projectId"));
    expect(copiedId).not.toBe(projectId);
    const copied = await page.request.get(`/api/v1/projects/${copiedId}`).then(r => r.json());
    expect(copied.documents).toEqual(original.documents);
    const recompilation = await page.request.post(`/api/v1/projects/${copiedId}/compilations`, {
      headers,
      data: { revision: copied.revision },
    });
    expect(recompilation.status()).toBe(200);
    const recompiled = await recompilation.json();
    expect(recompiled.valid).toBe(true);
    expect(recompiled.semanticDigest).toBe(compiled.semanticDigest);
    expect(recompiled.planDigest).toBe(compiled.planDigest);
    expect((await page.request.get("/api/v1/runs").then(r => r.json())).items).toEqual([]);
    await info.attach("verification", { body: JSON.stringify({ viewport, blueprint: "autoverse-platform", documentCount: 8, bindingCount: 6, semanticDigest: compiled.semanticDigest, planDigest: compiled.planDigest, exactExchange: true, runsCreated: 0, liveExecution: "NOT_RUN" }), contentType: "application/json" });
  });
}
