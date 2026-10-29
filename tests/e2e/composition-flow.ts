import { expect, type Page, type TestInfo } from "@playwright/test";
export async function exerciseComposition(page: Page, testInfo: TestInfo) {
  await page
    .getByRole("button", { name: "Compatibility and environment", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Admitted profile locks", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Select profile Declared experiment intent", { exact: true })
    .check();
  await page
    .getByLabel("Select profile Bounded experiment assessment", { exact: true })
    .check();
  await page
    .getByRole("button", { name: "Bind selected profile locks", exact: true })
    .click();
  await expect(
    page.getByText(
      "Profile locks saved with exact schema and presentation identities.",
      { exact: true },
    ),
  ).toBeVisible();
  const binding = await page.evaluate(async () => {
    const projectId = localStorage.getItem("studio.projectId");
    const [project, profiles] = await Promise.all([
      fetch("/api/v1/projects/" + projectId).then((response) =>
        response.json(),
      ),
      fetch("/api/v1/profiles").then((response) => response.json()),
    ]);
    return { locks: project.manifest.profiles, admitted: profiles.items };
  });
  expect(binding.locks).toHaveLength(2);
  for (const lock of binding.locks) {
    const admitted = binding.admitted.find(
      (profile: any) => profile.namespace === lock.namespace,
    );
    expect(lock.version).toBe(admitted.version);
    expect(lock.schemaDigest).toBe(admitted.schemaDigest);
    expect(lock.presentationDigest).toBe(admitted.presentationDigest);
  }
  await page.getByRole("tab", { name: "Deployment", exact: true }).click();
  await expect(
    page.getByLabel("Associated Scenario", { exact: true }),
  ).not.toHaveValue("");
  const originalScenario = await page
    .getByLabel("Associated Scenario", { exact: true })
    .inputValue();
  const originalDeployment = await page
    .getByLabel("Deployment variant", { exact: true })
    .inputValue();
  await page
    .getByLabel("New variant name", { exact: true })
    .fill("Browser alternative");
  await page
    .getByRole("button", { name: "Create deployment variant", exact: true })
    .click();
  await expect(
    page.getByLabel("Deployment variant", { exact: true }),
  ).toHaveValue(/\/browser-alternative$/);
  await expect(
    page.getByLabel("Associated Scenario", { exact: true }),
  ).toHaveValue(/\/browser-alternative-scenario$/);
  const chosenScenario = await page
    .getByLabel("Associated Scenario", { exact: true })
    .inputValue();
  const chosenDeployment = await page
    .getByLabel("Deployment variant", { exact: true })
    .inputValue();
  expect(chosenScenario).not.toBe(originalScenario);
  expect(chosenDeployment).not.toBe(originalDeployment);
  await page.screenshot({
    path: testInfo.outputPath("deployment-variant.png"),
    fullPage: true,
  });
  const requestedPreflight = page.waitForRequest(
    (request) =>
      request.method() === "POST" && request.url().endsWith("/preflights"),
  );
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  const selectedInputs = (await requestedPreflight).postDataJSON();
  expect(selectedInputs.deploymentRef).toBe(chosenDeployment);
  expect(selectedInputs.scenarioRef).toBe(chosenScenario);
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
    timeout: 15000,
  });
  const executed = await page.evaluate(async () => {
    const runId = localStorage.getItem("studio.lastRun");
    return fetch("/api/v1/runs/" + runId).then((response) => response.json());
  });
  expect(executed.planDigest).toMatch(/^sha256:[a-f0-9]{64}$/);
  expect(executed.effectivePlanDigest).toBe(executed.planDigest);
  expect(executed.effectiveSemanticDigest).toBe(executed.semanticDigest);
  await page.reload();
  await page.getByRole("tab", { name: "Deployment", exact: true }).click();
  await expect(
    page.getByLabel("Deployment variant", { exact: true }),
  ).toHaveValue(chosenDeployment);
  await expect(
    page.getByLabel("Associated Scenario", { exact: true }),
  ).toHaveValue(chosenScenario);
  await page.getByRole("tab", { name: "Model", exact: true }).click();
  await page
    .locator(".tree-list")
    .getByRole("button", { name: "plant plant", exact: true })
    .click();
  await page.getByRole("button", { name: "Properties", exact: true }).click();
  const bindingsRow = page
    .locator(".inspector .key-values > div")
    .filter({ has: page.getByText("Deployment bindings", { exact: true }) });
  const displayedBindings = JSON.parse(
    await bindingsRow.locator("dd").innerText(),
  );
  expect(displayedBindings.map((value: any) => value.variant).sort()).toEqual(
    [
      originalDeployment.split("/").at(-1),
      chosenDeployment.split("/").at(-1),
    ].sort(),
  );
  expect(
    displayedBindings.every(
      (value: any) => value.realization === "simulated" && value.target,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Catalog", exact: true }).click();
  await page
    .getByLabel("Catalog kind", { exact: true })
    .selectOption("component");
  await expect(
    page.getByRole("heading", { name: "reference-controller", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Open as project", exact: true }),
  ).toHaveCount(0);
  const runsBefore = await page.evaluate(
    async () =>
      (await fetch("/api/v1/runs").then((response) => response.json())).items
        .length,
  );
  await page
    .getByRole("button", { name: "Register artifact metadata", exact: true })
    .click();
  await page
    .getByLabel("Artifact name", { exact: true })
    .fill("Browser metadata reference");
  await page.getByLabel("Artifact version", { exact: true }).fill("1.0.0");
  await page
    .getByLabel("Declared SHA-256 digest", { exact: true })
    .fill("sha256:" + "2".repeat(64));
  await page
    .getByLabel("Portable origin reference", { exact: true })
    .fill("urn:xverse:studio:browser-test:metadata-v1");
  await page
    .getByRole("button", { name: "Register metadata only", exact: true })
    .click();
  await expect(
    page.getByText(
      "Artifact metadata registered. No artifact was downloaded or executed.",
      { exact: true },
    ),
  ).toBeVisible();
  const artifactState = await page.evaluate(async () => {
    const [catalog, runs] = await Promise.all([
      fetch("/api/v1/catalog?kind=artifact").then((response) =>
        response.json(),
      ),
      fetch("/api/v1/runs").then((response) => response.json()),
    ]);
    return {
      entry: catalog.items.find(
        (entry: any) => entry.name === "Browser metadata reference",
      ),
      runs: runs.items.length,
    };
  });
  expect(artifactState.entry.executionAllowed).toBe(false);
  expect(artifactState.entry.availability).toBe("unavailable");
  expect(artifactState.runs).toBe(runsBefore);
  await page
    .getByLabel("Catalog kind", { exact: true })
    .selectOption("artifact");
  await expect(
    page.getByRole("heading", {
      name: "Browser metadata reference",
      exact: true,
    }),
  ).toBeVisible();
  // Scoped to this test's own entry: the shared catalog may list other registrations.
  await expect(
    page
      .locator("article.panel")
      .filter({
        has: page.getByRole("heading", {
          name: "Browser metadata reference",
          exact: true,
        }),
      })
      .getByText(
        "Registered reference only. Availability and provider execution remain unresolved.",
        { exact: true },
      ),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("artifact-catalog.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Back to workspace", exact: true })
    .click();
}
