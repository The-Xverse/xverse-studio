import { test, expect } from "@playwright/test";
import { parse, stringify } from "yaml";
import { connectStudio } from "./connect-studio";
import { inspectTraceForm, traceApi } from "./trace-claims-flow";
// Keep bounded request metadata when this workflow fails; never capture auth or bodies.
let traceRequestDiagnostics: { events: object[]; omitted: number } = { events: [], omitted: 0 };
test.beforeEach(async ({ page }) => {
  traceRequestDiagnostics = { events: [], omitted: 0 };
  const requests = new WeakMap<object, number>();
  let sequence = 0;
  const relevant = (url: string) => {
    const p = new URL(url).pathname;
    return p === "/api/v1/runs" || p.startsWith("/api/v1/annotations/") || /^\/api\/v1\/runs\/[^/]+(?:\/annotations)?$/.test(p);
  };
  const record = (value: object) => {
    if (traceRequestDiagnostics.events.length < 512) traceRequestDiagnostics.events.push(value);
    else traceRequestDiagnostics.omitted++;
  };
  page.on("request", (request) => {
    if (!relevant(request.url())) return;
    const id = ++sequence; requests.set(request, id);
    record({ event: "request", id, at: Date.now(), method: request.method(), path: new URL(request.url()).pathname });
  });
  page.on("response", (response) => {
    const id = requests.get(response.request());
    if (id !== undefined) record({ event: "response", id, at: Date.now(), status: response.status(), etag: response.headers()["etag"] });
  });
  page.on("requestfinished", (request) => {
    const id = requests.get(request);
    if (id !== undefined) record({ event: "finished", id, at: Date.now() });
  });
  page.on("requestfailed", (request) => {
    const id = requests.get(request);
    if (id !== undefined) record({ event: "failed", id, at: Date.now(), failure: request.failure()?.errorText });
  });
});
test.afterEach(async ({}, info) => {
  await info.attach("bounded-run-annotation-request-timings", { body: JSON.stringify(traceRequestDiagnostics), contentType: "application/json" });
});
test("reported external claims: frozen subjects, revision history, neutral PASS label and immutable exchange", async ({
  page,
}, testInfo) => {
  test.setTimeout(120000);
  await connectStudio(page, testInfo);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.getByRole("button", { name: "New project", exact: true }).click();
  await page
    .getByLabel("Project name", { exact: true })
    .fill("Reported claim browser reference");
  await page
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Reported claim browser reference",
  );
  const projectId = await page.evaluate(() =>
    localStorage.getItem("studio.projectId"),
  );
  const project = (await traceApi(page, "/projects/" + projectId)).body;
  const [documentId, document] = Object.entries(project.documents).find(
    ([, value]: any) => parse(value.content).kind === "Scenario",
  )! as [string, any];
  const scenario = parse(document.content);
  scenario.extensions["io.xverse.experiment"].parameters.find(
    (p: any) => p.id === "duration",
  ).value = 0.2;
  scenario.extensions[
    "io.xverse.studio.experiments"
  ].definitions[0].window.endTick = "200000";
  scenario.extensions[
    "io.xverse.studio.experiments"
  ].definitions[0].expression.right.value = -1;
  expect(
    (
      await traceApi(
        page,
        `/projects/${projectId}/documents/${documentId}`,
        "PUT",
        { content: stringify(scenario), format: "yaml" },
        project.revision,
      )
    ).status,
  ).toBe(200);
  await page.reload();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Reported claim browser reference",
  );
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Start frozen snapshot", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /Run results/ }),
  ).toBeVisible();
  await expect(page.getByText("stopped", { exact: true }).first()).toBeVisible({
    timeout: 20000,
  });
  const runId = (await page.evaluate(() =>
    localStorage.getItem("studio.lastRun"),
  ))!;
  const run = (await traceApi(page, "/runs/" + runId)).body;
  const definition = (await traceApi(page, `/runs/${runId}/definitions`)).body
    .items[0];
  const evaluated = await traceApi(page, `/runs/${runId}/evaluations`, "POST", {
    snapshotId: run.snapshotId,
    definitionRef: definition.definitionRef,
    definitionDigest: definition.definitionDigest,
    evidenceRefs: [runId + ":reference-journal"],
  });
  expect(evaluated.status).toBe(202);
  const beforeSnapshot = (await traceApi(page, `/runs/${runId}/snapshot`)).body
    .snapshot;
  const beforeEvidence = (await traceApi(page, `/runs/${runId}/evidence`)).body;
  expect((await traceApi(page, "/runs/" + runId)).body.verdict).toBe("fail");
  await page.reload();
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  await expect(
    page.locator(".status-card").filter({ hasText: "Assertion verdict" }),
  ).toContainText("fail");
  await inspectTraceForm(page);
  await page
    .getByLabel("Requirement or test URI", { exact: true })
    .fill("urn:requirements:browser:trace-1");
  await page
    .getByLabel("Referenced revision", { exact: true })
    .fill("external-r7");
  await page
    .getByLabel("Include reported claim status", { exact: true })
    .check();
  await page
    .getByLabel("Reported claim status", { exact: true })
    .fill("  PASS reported externally  ");
  const subjects = page.getByRole("group", {
    name: "Frozen model and Scenario references",
    exact: true,
  });
  await subjects
    .getByLabel("componentInstance · plant", { exact: true })
    .check();
  await subjects
    .getByLabel("Scenario · reference-response", { exact: true })
    .check();
  await page
    .getByRole("group", { name: "Frozen assertions and metrics", exact: true })
    .getByRole("checkbox")
    .first()
    .check();
  await page.getByLabel("Owned run journal", { exact: true }).check();
  await page
    .getByRole("button", { name: "Save external reference", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  const row = page.getByRole("article", {
    name: "External reference urn:requirements:browser:trace-1",
    exact: true,
  });
  await expect(row.locator(".trace-reported-status")).toHaveText(
    "  PASS reported externally  ",
  );
  expect(await row.locator(".trace-reported-status").textContent()).toBe(
    "  PASS reported externally  ",
  );
  await expect(
    row.getByText("Reported claim status", { exact: true }),
  ).toBeVisible();
  await expect(row.locator(".badge")).toHaveCount(0);
  await expect(
    page.locator(".status-card").filter({ hasText: "Assertion verdict" }),
  ).toContainText("fail");
  await row
    .getByRole("button", { name: "Edit external reference", exact: true })
    .click();
  await expect(
    page.getByLabel("Reported claim status", { exact: true }),
  ).toHaveValue("  PASS reported externally  ");
  await page
    .getByLabel("Reported claim status", { exact: true })
    .fill("Review still pending");
  await page
    .getByRole("button", { name: "Save reference revision", exact: true })
    .click();
  await expect(row).toContainText("Review still pending");
  const rows = (await traceApi(page, `/runs/${runId}/annotations`)).body.items;
  const linked = rows.find(
    (r: any) => r.target?.uri === "urn:requirements:browser:trace-1",
  );
  expect(linked.revision).toBe(2);
  expect(linked.target.claimStatus).toBe("Review still pending");
  expect(linked.history[0].target.claimStatus).toBe(
    "  PASS reported externally  ",
  );
  expect(linked.definitionRefs).toEqual([
    {
      definitionRef: definition.definitionRef,
      definitionDigest: definition.definitionDigest,
    },
  ]);
  await row
    .getByRole("button", { name: "Remove external reference", exact: true })
    .click();
  await expect(row).toContainText(
    "Annotation removed; historical revisions retained.",
  );
  await page.route(`**/api/v1/runs/${runId}/snapshot`, (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        code: "SNAPSHOT_UNAVAILABLE",
        message: "Subject reader unavailable for this UI transport fixture.",
      }),
    }),
  );
  await inspectTraceForm(page);
  await expect(
    page
      .getByRole("alert")
      .filter({ hasText: "Journal-only references remain available" }),
  ).toBeVisible();
  await page
    .getByLabel("Requirement or test URI", { exact: true })
    .fill("urn:requirements:browser:legacy");
  await page.getByLabel("Referenced revision", { exact: true }).fill("unknown");
  await page
    .getByRole("button", { name: "Save external reference", exact: true })
    .click();
  await expect(
    page.getByRole("article", {
      name: "External reference urn:requirements:browser:legacy",
      exact: true,
    }),
  ).toContainText("Not supplied");
  await page.unroute(`**/api/v1/runs/${runId}/snapshot`);
  const latest = (await traceApi(page, `/runs/${runId}/annotations`)).body
    .items;
  expect(
    latest.find((r: any) => r.target?.uri.endsWith(":legacy")).target,
  ).not.toHaveProperty("claimStatus");
  expect(
    latest.find((r: any) => r.annotationId === linked.annotationId).deleted,
  ).toBe(true);
  expect(
    (await traceApi(page, `/runs/${runId}/snapshot`)).body.snapshot,
  ).toEqual(beforeSnapshot);
  expect((await traceApi(page, `/runs/${runId}/evidence`)).body).toEqual(
    beforeEvidence,
  );
  expect((await traceApi(page, "/runs/" + runId)).body.verdict).toBe("fail");
  await page.screenshot({
    path: testInfo.outputPath("reported-claim-separate-from-fail.png"),
    fullPage: true,
  });
  await page.getByRole("tab", { name: "Evidence", exact: true }).click();
  const downloadPromise = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export evidence bundle", exact: true })
    .click();
  const download = await downloadPromise;
  const bundle = testInfo.outputPath("reported-claim-evidence.zip");
  await download.saveAs(bundle);
  await page
    .getByRole("button", { name: "X-Verse Studio home", exact: true })
    .click();
  const imported = page.waitForResponse(
    (r) =>
      r.url().endsWith("/evidence/imports") && r.request().method() === "POST",
  );
  await page
    .getByLabel("Import evidence archive", { exact: true })
    .setInputFiles(bundle);
  const response = await imported;
  expect(response.status()).toBe(201);
  const importedBundle = await response.json();
  expect(importedBundle.annotations).toEqual(latest);
  expect(importedBundle.inspection.executionAllowed).toBe(false);
  expect(errors).toEqual([]);
});
