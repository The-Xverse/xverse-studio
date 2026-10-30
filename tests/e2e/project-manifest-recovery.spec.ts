import { test, expect, type Page, type Locator } from "@playwright/test";
import { readFileSync, realpathSync, writeFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "./connect-studio";

async function activate(page: Page, control: Locator) {
  await expect(control).toBeVisible();
  for (let i = 0; i < 220; ++i) {
    if (await control.evaluate((node) => document.activeElement === node)) break;
    await page.keyboard.press("Tab");
  }
  await expect(control).toBeFocused();
  await page.keyboard.press("Enter");
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  for (const action of ["adopt_external", "restore_revision"] as const) {
    test(`project envelope recovery ${action} at ${viewport.width}`, async ({ page }, info) => {
      await page.setViewportSize(viewport);
      await connectStudio(page, info);
      const project = await page.evaluate(async (name) => {
        const session = await fetch("/api/v1/session").then((r) => r.json());
        const response = await fetch("/api/v1/projects", { method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken },
          body: JSON.stringify({ name }) });
        if (response.status !== 201) throw Error("Owned envelope fixture creation failed");
        const p = await response.json();
        localStorage.setItem("studio.projectId", p.projectId);
        return p;
      }, `Envelope recovery ${action} ${viewport.width}`);
      const configured = process.env.STUDIO_BROWSER_DATA;
      if (!configured) throw Error("An isolated native browser-test root is required");
      const root = realpathSync(configured), allowed = realpathSync(path.resolve(".studio-local/browser-tests"));
      expect(root.startsWith(allowed + path.sep)).toBe(true);
      const file = path.join(root, "projects", project.projectId, "revisions", String(project.revision), "project.studio.json");
      expect(realpathSync(file)).toBe(file);
      const original = readFileSync(file), external = Buffer.from('{"foreign":"owned envelope corruption fixture","resources":[],"profiles":[]}');
      writeFileSync(file, external);
      try {
        await page.reload();
        await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
        await expect(page.getByText(/revision envelope differs from its recorded identity/)).toBeVisible();
        const recovery = page.getByRole("group", { name: "Source recovery", exact: true });
        await expect(recovery).toHaveAccessibleDescription(/Sidecars keep their recorded content/);
        const button = recovery.getByRole("button", { name: action === "adopt_external"
          ? "Adopt external changes as a new revision" : `Restore committed revision ${project.revision}`, exact: true });
        const reply = page.waitForResponse((r) => new URL(r.url()).pathname === `/api/v1/projects/${project.projectId}/recoveries` && r.request().method() === "POST");
        await activate(page, button);
        const response = await reply;
        expect(response.status()).toBe(200);
        const result = await response.json();
        expect(result.project.revision).toBe(project.revision + 1);
        expect(result.project.manifest).toEqual(project.manifest);
        expect(result.project.sourceIntegrity).toBe("intact");
        await expect(recovery).toHaveCount(0);
        expect(readFileSync(file)).toEqual(external);
        const preserved = await page.request.get(`/api/v1/projects/${project.projectId}/recoveries/${result.recovery.recoveryId}/preserved?key=${encodeURIComponent("sidecar:project.studio.json")}`);
        expect(preserved.status()).toBe(200);
        expect(Buffer.from((await preserved.json()).content)).toEqual(external);
        const newFile = path.join(root, "projects", project.projectId, "revisions", String(result.project.revision), "project.studio.json");
        expect(readFileSync(newFile)).toEqual(original);
        await activate(page, page.getByRole("button", { name: "Validate", exact: true }));
        await expect(page.getByText("Authoritative platform validation passed.", { exact: false })).toBeVisible();
        const runs = await page.request.get(`/api/v1/runs?projectId=${project.projectId}`).then((r) => r.json());
        expect(runs.items).toEqual([]);
        await page.reload();
        await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
        await expect(page.getByRole("group", { name: "Source recovery", exact: true })).toHaveCount(0);
        await info.attach("envelope-recovery-scope", { body: JSON.stringify({ viewport, action,
          originalEnvelopePreserved: true, recoveredEnvelopeUsesRecordedMetadata: true,
          nativeBackend: true, workloadDispatch: false }), contentType: "application/json" });
      } finally {
        // Only this test's own original file is reset, after preservation assertions.
        writeFileSync(file, original);
      }
    });
  }
}
