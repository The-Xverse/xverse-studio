import { test, expect, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "./connect-studio";

async function makeProject(page: Page, name: string, duration?: number) {
  return page.evaluate(
    async ({ name, duration }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      };
      let r = await fetch("/api/v1/projects", {
        method: "POST",
        headers,
        body: JSON.stringify({ name }),
      });
      if (!r.ok) throw Error(await r.text());
      let project = await r.json();
      if (duration !== undefined) {
        r = await fetch(`/api/v1/projects/${project.projectId}/edits`, {
          method: "POST",
          headers: { ...headers, "If-Match": String(project.revision) },
          body: JSON.stringify({
            baseRevision: project.revision,
            edits: [
              {
                kind: "set_parameter",
                parameterId: "duration",
                value: duration,
              },
            ],
          }),
        });
        if (!r.ok) throw Error(await r.text());
        project = await r.json();
      }
      localStorage.setItem("studio.projectId", project.projectId);
      return project;
    },
    { name, duration },
  );
}
async function showRun(page: Page, projectId: string, runId: string) {
  await page.evaluate(
    ({ projectId, runId }) => {
      localStorage.setItem("studio.projectId", projectId);
      localStorage.setItem("studio.lastRun." + projectId, runId);
      localStorage.setItem("studio.lastRun", runId);
    },
    { projectId, runId },
  );
  await page.reload();
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  await page.getByRole("tab", { name: "Diagnosis", exact: true }).click();
}
const finding = (page: Page, cls: string) =>
  page.locator(`[data-diagnostic-class="${cls}"]`);

test("diagnosis: recorded evidence separates facts, consequences and unknowns without inferring a cause", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await makeProject(page, "Diagnosis recorded evidence");
  const fixture = JSON.parse(
    execFileSync(
      path.resolve(".venv/bin/python"),
      [
        "tests/fixtures/evidence/create_recorded_evidence.py",
        "--data-dir",
        process.env.STUDIO_BROWSER_DATA!,
        "--project-id",
        project.projectId,
      ],
      { encoding: "utf8" },
    ),
  );
  const journal = path.join(
      process.env.STUDIO_BROWSER_DATA!,
      "runs",
      fixture.runId,
      "evidence.jsonl",
    ),
    sha = () =>
      createHash("sha256").update(readFileSync(journal)).digest("hex"),
    before = sha();
  const writes: string[] = [];
  page.on("request", (r) => {
    if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
      writes.push(r.method() + " " + r.url());
  });
  await showRun(page, project.projectId, fixture.runId);
  const panel = page.getByRole("region", { name: "Run diagnosis" });
  await expect(panel).toHaveAttribute("data-explanation-state", "loaded");
  await expect(panel).toContainText("Studio does not infer root causes");
  const clocks = finding(page, "incompatible_time_mapping");
  await expect(clocks).toContainText("Observed facts");
  await expect(clocks).toContainText(/Observations use 2 clock domains/);
  await expect(clocks).toContainText("Inferred consequences");
  await expect(clocks).toContainText(
    "not ordered, aligned or compared by latency",
  );
  await expect(clocks).toContainText(
    "The mapping between these clock domains.",
  );
  const gap = finding(page, "telemetry_gap");
  await expect(gap).toContainText("observation.gap");
  await expect(gap).toContainText("(from F1)");
  await expect(finding(page, "unavailable_evidence")).toContainText(
    "EVIDENCE_PARTIAL",
  );
  // A recorded fixture has no exit, ownership loss or traffic absence to explain.
  for (const cls of ["process_exit", "lost_connection", "no_traffic"])
    await expect(finding(page, cls)).toHaveCount(0);
  await expect(panel.getByText("Hypotheses · unconfirmed")).toHaveCount(0);
  const inspect = gap.getByRole("button", {
    name: "Inspect the referenced retained events and logs.",
  });
  await inspect.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("tab", { name: /Events & logs/ }),
  ).toHaveAttribute("aria-selected", "true");
  expect(writes).toEqual([]);
  expect(sha()).toBe(before);
  await page.getByRole("tab", { name: "Diagnosis", exact: true }).click();
  await page.setViewportSize({ width: 1024, height: 768 });
  await panel.screenshot({
    path: testInfo.outputPath("recorded-evidence-diagnosis-1024.png"),
  });
});

test("diagnosis: a completed owned run reports no findings and claims no functional health", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await makeProject(page, "Diagnosis completed run", 0.5);
  await page.reload();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start frozen snapshot", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /Run results/ }),
  ).toContainText("stopped", { timeout: 15000 });
  const runId = await page.evaluate(() =>
    localStorage.getItem("studio.lastRun"),
  );
  await showRun(page, project.projectId, runId!);
  const panel = page.getByRole("region", { name: "Run diagnosis" });
  await expect(panel).toHaveAttribute("data-explanation-state", "loaded");
  await expect(panel.locator(".diagnostic-none")).toContainText(
    "Completion and liveness are not evidence of functional health.",
  );
  await expect(panel.locator("[data-diagnostic-class]")).toHaveCount(0);
});

test("diagnosis: an unavailable provider explains the blocked snapshot without misattributing unestablished facts", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  await makeProject(page, "Diagnosis blocked preflight");
  await page.reload();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await page
    .getByLabel("Execution provider", { exact: true })
    .selectOption("xverse.lite");
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/preflights") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Recheck readiness", exact: true })
    .click();
  const blocked = await (await response).json();
  expect(blocked.status).toBe("blocked");
  const panel = page.getByRole("region", {
    name: "Readiness explanation",
  });
  await expect(panel).toHaveAttribute("data-explanation-state", "loaded");
  const unsupported = finding(page, "unsupported_capability");
  await expect(unsupported.first()).toContainText(/Preflight provider: /);
  await expect(finding(page, "missing_artifact")).toHaveCount(0);
  // Codeless unknown dimensions are grouped as unestablished, never as failures.
  await expect(finding(page, "readiness_unknown")).toContainText(
    "unknown is not failure",
  );
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeDisabled();
  await panel.screenshot({
    path: testInfo.outputPath("blocked-preflight-diagnosis.png"),
  });
});
