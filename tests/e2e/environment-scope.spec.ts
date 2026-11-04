import { test, expect } from "@playwright/test";
import { connectStudio } from "./connect-studio";

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test(`environment separates required targets, unverified Windows and provider support at ${viewport.width}`, async ({ page }, info) => {
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const capabilities = await page.request.get("/api/v1/capabilities").then((r) => r.json());
    expect(capabilities.studio.nativeTargets).toEqual(["Linux", "Windows"]);
    expect(capabilities.studio.windowsAcceptance).toBe("NOT_RUN");
    await page.getByRole("button", { name: "Environment", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Environment", exact: true })).toBeVisible();
    const backend = page.locator("section").filter({ has: page.getByRole("heading", { name: "Studio backend", exact: true }) });
    await expect(backend.getByText("Windows scope", { exact: true })).toBeVisible();
    await expect(backend.getByText("NOT_RUN", { exact: true })).toBeVisible();
    await expect(backend.getByText("Native target OS", { exact: true })).toBeVisible();
    await expect(backend.getByText("BLOCKED_USER_REQUEST", { exact: true })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "Provider compatibility", exact: true })).toBeVisible();
    for (const provider of capabilities.providers) {
      await expect(page.getByRole("heading", { name: provider.name || provider.providerId, exact: true })).toBeVisible();
    }
    await info.attach("delivery-scope", { body: JSON.stringify({ viewport, nativeTargets: capabilities.studio.nativeTargets,
      windowsScope: capabilities.studio.windowsAcceptance, providerCount: capabilities.providers.length,
      scope: "Native Linux browser/API; provider declarations remain independent, no workload dispatch" }), contentType: "application/json" });
  });
}
