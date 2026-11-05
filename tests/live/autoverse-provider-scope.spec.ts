import { test, expect, type Locator, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
import { renderedContrast } from "../e2e/contrast";

async function activate(page: Page, control: Locator) {
  await expect(control).toBeVisible();
  for (let i = 0; i < 600; i++) {
    if (await control.evaluate(n => n === document.activeElement)) {
      const focus = await control.evaluate(n => {
        const r = n.getBoundingClientRect(), s = getComputedStyle(n);
        return s.outlineStyle !== "none" && parseFloat(s.outlineWidth) > 0 && r.left >= 0 && r.top >= 0 && r.right <= innerWidth + 1 && r.bottom <= innerHeight + 1;
      });
      expect(focus).toBe(true); await page.keyboard.press("Enter"); return;
    }
    await page.keyboard.press("Tab");
  }
  throw Error("Project selection is unreachable through native keyboard navigation");
}
for (const width of [1024, 1440]) {
  for (const mode of ["absent recorded provider", "known authoring descriptor"] as const) {
    test(`workspace scope uses ${mode} at ${width}`, async ({ page }, info) => {
      await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
      await connectStudio(page, info);
      const source = JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "playback-recording.private.json"), "utf8"));
      const descriptorsReply = await page.request.get("/api/v1/providers"); expect(descriptorsReply.status()).toBe(200);
      const descriptors = (await descriptorsReply.json()).items;
      let project: any, expectedId: string, expectedScope: string;
      if (mode === "absent recorded provider") {
        expectedId = "autoverse.demo"; expectedScope = "Provider unavailable";
        expect(descriptors.some((p: any) => p.providerId === expectedId)).toBe(false);
        const response = await page.request.get(`/api/v1/projects/${source.projectId}`); expect(response.status()).toBe(200);
        project = await response.json();
      } else {
        // Inert authoring fixture only. No reference model or provider callback runs.
        const session = await page.request.get("/api/v1/session").then(r => r.json());
        const response = await page.request.post("/api/v1/projects", {
          headers: { Origin: process.env.STUDIO_BASE_URL!, "X-CSRF-Token": session.csrfToken },
          data: { name: `Provider scope authoring ${width}`, blueprintRef: "reference-feedback" },
        });
        expect(response.status()).toBe(201); project = await response.json();
        expectedId = "studio.reference";
        const descriptor = descriptors.find((p: any) => p.providerId === expectedId); expect(descriptor.available).toBe(true);
        expectedScope = descriptor.evidenceScope.replaceAll("_", " ");
        // Refresh the listing after this explicit outside-UI fixture transaction.
        await page.reload();
      }
      await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
      await activate(page, page.locator(`.project-list-row[data-project-id="${project.projectId}"] .project-open`));
      await expect(page.locator(".project-header h1")).toHaveText(project.name);
      // The global shell cannot assign reference evidence scope to every
      // project, including an absent Autoverse provider. Scope belongs below.
      await expect(page.getByRole("banner").getByText("REFERENCE PREVIEW", { exact: true })).toHaveCount(0);
      const status = page.getByRole("status", { name: "Selected provider scope", exact: true });
      await expect(status).toContainText(expectedId); await expect(status).toContainText(expectedScope);
      await expect(status).not.toContainText(/ready to (run|execute)/i);
      if (mode === "absent recorded provider") await expect(status).not.toContainText(/owned reference/i);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      const bounds = await status.boundingBox(); expect(bounds!.x).toBeGreaterThanOrEqual(0);
      expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(width + 1);
      const measurements = [];
      for (const [control, name] of [[status, "Provider label"], [status.locator("code"), "Selected provider identity"], [status.locator(".badge"), "Provider availability or scope"]] as const) {
        const measurement = await renderedContrast(control, name); expect(measurement.supported).toBe(true);
        if (measurement.supported) expect(measurement.ratio).toBeGreaterThanOrEqual(4.5);
        measurements.push(measurement);
      }
      await info.attach("actual-selected-provider-scope", { body: JSON.stringify({ mode, width, expectedId, expectedScope,
        projectId: project.projectId, actualStatus: await status.innerText(), measurements, browser: page.context().browser()?.version(),
        scope: "Actual absent Autoverse provider or real core descriptor with inert source-only authoring; no provider/model/evaluation/campaign or physical operation",
      }), contentType: "application/json" });
    });
  }
}
