import { test, expect } from "@playwright/test";
import { connectStudio } from "../e2e/connect-studio";

for (const width of [1024, 1440]) {
  test(`Actual Autoverse scenario inspection and revision boundaries at ${width}`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const project = await page.evaluate(async (name) => {
      const session = await fetch("/api/v1/session").then(r => r.json());
      const created = await fetch("/api/v1/projects", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken }, body: JSON.stringify({ name, blueprintRef: "autoverse-classic" }) });
      if (created.status !== 201) throw Error("The actual Autoverse target was not enrolled");
      const p = await created.json();
      localStorage.setItem("studio.projectId", p.projectId);
      return p;
    }, `Autoverse scenario support ${width}`);
    await page.reload();
    await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
    await page.getByRole("tab", { name: "Experiments", exact: true }).click();
    const panel = page.getByRole("region", { name: "Scenario support and observation budgets", exact: true });
    const inspect = panel.getByRole("button", { name: "Inspect scenario support", exact: true });
    await inspect.focus();
    await page.keyboard.press("Enter");
    await expect(panel.getByText("Preflight required", { exact: true })).toBeVisible();
    await expect(panel.getByRole("cell", { name: "observer-slot", exact: true })).toBeVisible();
    await expect(panel.getByRole("cell", { name: "satisfied", exact: true })).toBeVisible();
    await expect(panel.getByRole("heading", { name: "autoverse-telemetry", exact: true })).toBeVisible();
    await expect(panel.getByText("Unknown", { exact: true })).toBeVisible();
    await expect(panel.getByText("Not declared", { exact: true })).toBeVisible();
    await expect(inspect).toBeFocused();
    await expect(panel).toContainText("autoverse.demo");
    for (const fault of ["provider", "revision", "version"]) {
      await page.route("**/scenario-admission?**", async route => {
        const response = await route.fetch(), value = await response.json();
        if (fault === "provider") value.providerId = "unselected-provider";
        else if (fault === "revision") value.revision++;
        else value.scenarioAdmissionVersion = "unadmitted";
        await route.fulfill({ response, json: value });
      }, { times: 1 });
      await inspect.click();
      await expect(panel.getByRole("alert")).toContainText("does not match");
      await expect(panel.getByRole("heading", { name: "autoverse-telemetry", exact: true })).toHaveCount(0);
    }
    await inspect.click();
    await expect(panel.getByText("Preflight required", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Edit initial conditions", exact: true }).click();
    await page.getByLabel("Scenario acceptance intent", { exact: true }).fill("An altered draft must be inspected independently.");
    await page.getByRole("button", { name: "Save scenario conditions", exact: true }).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(panel.getByText("Preflight required", { exact: true })).toHaveCount(0);
    await expect(panel.getByRole("heading", { name: "autoverse-telemetry", exact: true })).toHaveCount(0);
    await inspect.click();
    await expect(panel.getByText("Source support blocked", { exact: true })).toBeVisible();
    const current = await page.request.get(`/api/v1/projects/${project.projectId}`).then(r => r.json());
    expect(current.revision).toBeGreaterThan(project.revision);
    await expect(panel).toContainText(`revision ${current.revision}`);
    expect((await page.request.get(`/api/v1/runs?projectId=${project.projectId}`).then(r => r.json())).items).toEqual([]);
    await info.attach("autoverse-scenario-inspection", { body: JSON.stringify({ target: "actual enrolled Autoverse", width, sourceRevision: current.revision, runtimeStarted: false, staleAndMismatchedReportsRefused: true, unknownCostsPreserved: true }), contentType: "application/json" });
  });
}
