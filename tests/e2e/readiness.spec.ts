import { test, expect, type Page } from "@playwright/test";
import { connectStudio } from "./connect-studio";
const dimensions = [
  "Studio backend",
  "Provider / host compatibility",
  "Model validity",
  "Artifact availability",
  "Capability compatibility",
  "Target readiness",
  "Resource availability",
  "Execution ownership",
  "Clock mappings",
  "Execution authority",
];
async function create(page: Page, name: string) {
  await page.getByRole("button", { name: "New project", exact: true }).click();
  await page.getByLabel("Project name", { exact: true }).fill(name);
  await page
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(page.locator(".project-header h1")).toHaveText(name);
}
async function preflight(page: Page) {
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/preflights") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  const result = await response;
  expect(result.status()).toBe(200);
  return result.json();
}
test("readiness review: independent backend facts, exact limits and frozen compiled plan with keyboard and both viewports", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  await create(page, "Readiness admitted reference");
  const before = await page.evaluate(
    async () =>
      (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
  );
  const report = await preflight(page);
  expect(report.status).toBe("ready");
  await expect(
    page.getByRole("heading", { name: "Readiness checks", exact: true }),
  ).toBeVisible();
  const table = page.getByRole("table", {
    name: "Independent readiness dimensions",
    exact: true,
  });
  await expect(
    table.getByRole("rowheader", { name: "Studio backend", exact: true }),
  ).toBeInViewport();
  await page.getByText("Frozen request identities", { exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".preflight-identities")).toContainText(
    report.snapshotDigest,
  );
  await page.getByText("Frozen request identities", { exact: true }).focus();
  await page.keyboard.press("Enter");
  for (const name of dimensions)
    await expect(
      table.getByRole("row").filter({ hasText: name }),
    ).toBeVisible();
  const limits = page.getByRole("table", {
    name: "Advertised execution limits",
    exact: true,
  });
  for (const [key, value] of Object.entries(report.limits)) {
    const row = limits
      .getByRole("row")
      .filter({ has: page.getByRole("cell", { name: key, exact: true }) });
    await expect(row).toContainText(String(value));
  }
  await page
    .getByRole("button", { name: "Inspect compiled plan", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByText("Frozen plan identities match", { exact: true }),
  ).toBeVisible();
  const shown = await page
    .getByLabel("Compiled execution plan (read-only)", { exact: true })
    .textContent();
  expect(JSON.parse(shown!)).toEqual(report.planPreview.plan);
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeEnabled();
  for (const viewport of [
    { width: 1024, height: 768 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth + 1,
      ),
    ).toBe(false);
    await expect(table).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath(`readiness-ready-${viewport.width}.png`),
      fullPage: true,
    });
  }
  await page
    .getByLabel("Execution provider", { exact: true })
    .selectOption("xverse.lite");
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByText("Provider choice changed.", { exact: false }),
  ).toBeVisible();
  await page
    .getByLabel("Execution provider", { exact: true })
    .selectOption("studio.reference");
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeEnabled();
  let release!: () => void, observed!: () => void;
  const gate = new Promise<void>((resolve) => {
      release = resolve;
    }),
    reached = new Promise<void>((resolve) => {
      observed = resolve;
    });
  const endpoint = "**/api/v1/projects/*/preflights";
  await page.route(endpoint, async (route) => {
    const response = await route.fetch();
    observed();
    await gate;
    await route.fulfill({ response });
  });
  await page
    .getByRole("button", { name: "Recheck readiness", exact: true })
    .click();
  await reached;
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Preflight & run", exact: true }),
  ).toBeFocused();
  release();
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.unroute(endpoint);

  expect(
    await page.evaluate(
      async () =>
        (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
    ),
  ).toBe(before);
  await testInfo.attach("readiness-ready-report", {
    body: JSON.stringify(report, null, 2),
    contentType: "application/json",
  });
});
test("readiness review: unsupported topology and unavailable provider remain separate from model and backend availability", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  await create(page, "Readiness blocked reference");
  const before = await page.evaluate(
    async () =>
      (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
  );
  const authored = await page.evaluate(async () => {
    const project = await fetch(
        "/api/v1/projects/" + localStorage.getItem("studio.projectId"),
      ).then((r) => r.json()),
      session = await fetch("/api/v1/session").then((r) => r.json());
    const docId = Object.entries(project.documents).find(([, doc]: any) =>
      doc.content.includes("kind: System"),
    )![0];
    const response = await fetch(
      `/api/v1/projects/${project.projectId}/edits`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": session.csrfToken,
          "If-Match": String(project.revision),
        },
        body: JSON.stringify({
          baseRevision: project.revision,
          edits: [
            {
              kind: "add_logical_asset",
              documentId: docId,
              assetKind: "device",
              elementId: "readiness-device",
              properties: {
                capabilities: ["measurement"],
                supportedRealizationClasses: ["simulated"],
              },
            },
          ],
        }),
      },
    );
    return { status: response.status, project: await response.json() };
  });
  expect(authored.status).toBe(200);
  await page.reload();
  const blocked = await preflight(page);
  expect(blocked.status).toBe("blocked");
  const table = page.getByRole("table", {
    name: "Independent readiness dimensions",
    exact: true,
  });
  await expect(
    table.getByRole("row").filter({ hasText: "Model validity" }),
  ).toContainText(/valid|ready/);
  await expect(
    table.getByRole("row").filter({ hasText: "Capability compatibility" }),
  ).toContainText(/unsupported|blocked/);
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("region", { name: "Readiness diagnostics", exact: true }),
  ).toContainText("CAPABILITY_UNSUPPORTED");
  await expect(
    page.getByRole("region", { name: "Readiness diagnostics", exact: true }),
  ).toContainText("readiness-device");
  await page.screenshot({
    path: testInfo.outputPath("readiness-unsupported-topology.png"),
    fullPage: true,
  });
  await page
    .getByLabel("Execution provider", { exact: true })
    .selectOption("xverse.lite");
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeDisabled();
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/preflights") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Recheck readiness", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  const unavailable = await (await response).json();
  expect(unavailable.providerId).toBe("xverse.lite");
  await expect(
    table.getByRole("row").filter({ hasText: "Studio backend" }),
  ).toContainText(/available|ready/);
  await expect(
    table.getByRole("row").filter({ hasText: "Provider / host compatibility" }),
  ).toContainText(/unavailable|unsupported|blocked/);
  await expect(
    page.getByRole("region", { name: "Readiness diagnostics", exact: true }),
  ).toContainText(/PROVIDER_UNAVAILABLE|DEP-RUN-CONFIG/);
  await expect(
    page.getByText("No execution limits reported for this provider.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeDisabled();
  await page.screenshot({
    path: testInfo.outputPath("readiness-unavailable-provider.png"),
    fullPage: true,
  });
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Preflight & run", exact: true }),
  ).toBeFocused();
  expect(
    await page.evaluate(
      async () =>
        (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
    ),
  ).toBe(before);
  await testInfo.attach("readiness-blocked-reports", {
    body: JSON.stringify({ blocked, unavailable }, null, 2),
    contentType: "application/json",
  });
});
