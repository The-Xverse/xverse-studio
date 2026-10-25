import { test, expect } from "@playwright/test";
import { parse } from "yaml";
import { connectStudio } from "./connect-studio";
test("scenario intent: typed stimulus, fault, observer and metric forms preserve opaque source and block unsupported execution", async ({
  page,
}, testInfo) => {
  test.setTimeout(120000);
  await connectStudio(page, testInfo);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.getByRole("button", { name: "New project", exact: true }).click();
  await page
    .getByLabel("Project name", { exact: true })
    .fill("Scenario intent authoring");
  await page
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Scenario intent authoring",
  );
  const projectId = await page.evaluate(() =>
    localStorage.getItem("studio.projectId"),
  );
  const runsBefore = await page.evaluate(
    async () =>
      (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
  );
  await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  await page
    .getByRole("button", { name: "Edit initial conditions", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("dialog", { name: "Edit scenario conditions", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Initial conditions (JSON object)", { exact: true })
    .fill('{"stateParameterRef":"initial","opaque":{"preserved":true}}');
  await page
    .getByLabel("Scenario acceptance intent", { exact: true })
    .fill("Authored acceptance intent, not an evaluated verdict.");
  await page
    .getByRole("button", { name: "Save scenario conditions", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  async function chooseTarget(id: string) {
    const value = await page
      .getByLabel("Declared target", { exact: true })
      .locator("option")
      .evaluateAll(
        (nodes, suffix) =>
          nodes
            .map((n) => (n as HTMLOptionElement).value)
            .find((v) => v.endsWith("#" + suffix)),
        id,
      );
    expect(value).toBeTruthy();
    await page
      .getByLabel("Declared target", { exact: true })
      .selectOption(value!);
  }
  async function add(
    label: string,
    id: string,
    configure: () => Promise<void>,
  ) {
    await page.getByRole("button", { name: label, exact: true }).focus();
    await page.keyboard.press("Enter");
    await page.getByLabel("Scenario item identifier", { exact: true }).fill(id);
    await configure();
    await page
      .getByRole("button", { name: "Add scenario item", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toHaveCount(0);
  }
  await add("Add stimulus step", "browser-stimulus", async () => {
    await chooseTarget("plant");
    await page
      .getByLabel("Declared clock domain", { exact: true })
      .selectOption("simulation-time");
    await page.getByLabel("Scheduled at", { exact: true }).fill("0.5");
    await page.getByLabel("Schedule unit", { exact: true }).fill("s");
    await page.getByLabel("Action kind", { exact: true }).fill("set_parameter");
    await page
      .getByLabel("Action payload (JSON object)", { exact: true })
      .fill('{"parameter":"target","value":2,"opaque":{"keep":[1,2]}}');
  });
  await add("Add fault intent", "browser-fault", async () => {
    await chooseTarget("plant");
    await page
      .getByLabel("Activation intent", { exact: true })
      .fill("Opaque activation: provider must admit this intent.");
    await page
      .getByLabel("Recovery intent", { exact: true })
      .fill("Opaque recovery: no equipment operation authorized.");
  });
  await add("Add observer", "browser-observer", async () => {
    await chooseTarget("state-flow");
    await page
      .getByLabel("Sampling intent", { exact: true })
      .fill("Every declared model step; intent only.");
  });
  await add("Add metric intent", "browser-metric", async () => {
    await page
      .getByRole("group", { name: "Declared observers", exact: true })
      .getByLabel("browser-observer", { exact: true })
      .check();
    await page
      .getByLabel("Metric acceptance intent", { exact: true })
      .fill("Opaque condition; not an assertion verdict.");
  });
  const beforeRejectedRemoval = await page.evaluate(
    async (id) => fetch("/api/v1/projects/" + id).then((r) => r.json()),
    projectId,
  );
  await page
    .getByRole("button", {
      name: "Remove observer browser-observer",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", { name: "Remove draft item", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    /rejected|unresolved|observer/i,
  );
  const afterRejectedRemoval = await page.evaluate(
    async (id) => fetch("/api/v1/projects/" + id).then((r) => r.json()),
    projectId,
  );
  expect(afterRejectedRemoval.revision).toBe(beforeRejectedRemoval.revision);
  expect(afterRejectedRemoval.documents).toEqual(
    beforeRejectedRemoval.documents,
  );
  await page.getByRole("button", { name: "Keep item", exact: true }).click();
  await page
    .getByRole("button", { name: "Edit step browser-stimulus", exact: true })
    .click();
  await page.getByLabel("Scheduled at", { exact: true }).fill("0.75");
  await page
    .getByRole("button", { name: "Save scenario item", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("button", {
      name: "View source for step browser-stimulus",
      exact: true,
    })
    .focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByText("spec.steps[id=browser-stimulus]", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Selected declaration highlighted in this draft.", {
      exact: true,
    }),
  ).toBeVisible();
  const selected = await page
    .getByLabel("XDL source", { exact: true })
    .evaluate((node: HTMLTextAreaElement) =>
      node.value.slice(node.selectionStart, node.selectionEnd),
    );
  expect(selected).toContain("browser-stimulus");
  expect(selected).toContain("0.75");
  expect(selected).toContain("opaque");
  await page.screenshot({
    path: testInfo.outputPath("scenario-selected-step-source.png"),
    fullPage: true,
  });
  await page.keyboard.press("Escape");
  const saved = await page.evaluate(
    async (id) => fetch("/api/v1/projects/" + id).then((r) => r.json()),
    projectId,
  );
  const scenario: any = Object.values(saved.documents)
    .map((doc: any) => parse(doc.content))
    .find((resource: any) => resource.kind === "Scenario");
  expect(scenario.spec.initialConditions.opaque).toEqual({ preserved: true });
  const step = scenario.spec.steps.find(
    (s: any) => s.id === "browser-stimulus",
  );
  expect(step.action.opaque).toEqual({ keep: [1, 2] });
  expect(step.schedule.at).toBe(0.75);
  expect(scenario.spec.faults[0].activation).toContain("Opaque activation");
  expect(
    scenario.spec.metrics.find((m: any) => m.id === "browser-metric")
      .observerIds,
  ).toEqual(["browser-observer"]);
  await page.reload();
  await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: "Edit metric browser-metric",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  await expect(
    page.getByText("Authoritative platform validation passed.", {
      exact: false,
    }),
  ).toBeVisible();
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/preflights") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  const preflight = await response;
  expect(preflight.status()).toBe(200);
  const blocked = await preflight.json();
  expect(blocked.status).not.toBe("ready");
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeDisabled();
  await page.keyboard.press("Escape");
  await page
    .getByRole("button", { name: "Remove metric browser-metric", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Remove draft item", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("button", {
      name: "Edit metric browser-metric",
      exact: true,
    }),
  ).toHaveCount(0);
  await page
    .getByRole("button", {
      name: "Remove observer browser-observer",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", { name: "Remove draft item", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("button", {
      name: "Edit observer browser-observer",
      exact: true,
    }),
  ).toHaveCount(0);
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
    await page.screenshot({
      path: testInfo.outputPath(`scenario-authoring-${viewport.width}.png`),
      fullPage: true,
    });
  }
  expect(
    await page.evaluate(
      async () =>
        (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
    ),
  ).toBe(runsBefore);
  expect(errors).toEqual([]);
  await testInfo.attach("scenario-admission-refusal", {
    body: JSON.stringify(blocked, null, 2),
    contentType: "application/json",
  });
});
