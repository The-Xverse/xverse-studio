import { parse } from "yaml";
import {
  expect,
  type Page,
  type TestInfo,
  type Request,
} from "@playwright/test";
export async function exerciseNeutralAssets(page: Page, testInfo: TestInfo) {
  // Passive diagnostics only: do not delay, retry or alter project requests.
  const diagnosticStart = Date.now(),
    requestLog: Record<string, unknown>[] = [],
    byRequest = new Map<Request, Record<string, unknown>>();
  let creationFailed = false,
    afterKeyboard: unknown;
  const started = (request: Request) => {
    const path = new URL(request.url()).pathname;
    if (!/^\/api\/v1\/projects(?:\/[^/]+)?$/.test(path)) return;
    const row = {
      method: request.method(),
      path,
      startedMs: Date.now() - diagnosticStart,
    };
    if (requestLog.length < 64) {
      requestLog.push(row);
      byRequest.set(request, row);
    }
  };
  const responded = (response: import("@playwright/test").Response) => {
    const row = byRequest.get(response.request());
    if (row)
      Object.assign(row, {
        status: response.status(),
        responseMs: Date.now() - diagnosticStart,
      });
  };
  const finished = (request: Request) => {
    const row = byRequest.get(request);
    if (row) Object.assign(row, { finishedMs: Date.now() - diagnosticStart });
  };
  const failed = (request: Request) => {
    const row = byRequest.get(request);
    if (row)
      Object.assign(row, {
        failedMs: Date.now() - diagnosticStart,
        failure: request.failure()?.errorText,
      });
  };
  page.on("request", started);
  page.on("response", responded);
  page.on("requestfinished", finished);
  page.on("requestfailed", failed);
  try {
    await page
      .getByRole("button", { name: "X-Verse Studio home", exact: true })
      .click();
    await page
      .getByRole("button", { name: "New project", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await page
      .getByLabel("Project name", { exact: true })
      .fill("Neutral asset authoring");
    const createProject = page.getByRole("button", {
      name: "Create project",
      exact: true,
    });
    await expect(createProject).toBeEnabled();
    await createProject.focus();
    await expect(createProject).toBeFocused();
    await page.keyboard.press("Enter");
    afterKeyboard = await page.evaluate(() => ({
      activeTag: document.activeElement?.tagName,
      activeText: document.activeElement?.textContent?.trim().slice(0, 120),
      createDisabled:
        [...document.querySelectorAll<HTMLButtonElement>("button")].find(
          (button) => button.textContent?.trim() === "Create project",
        )?.disabled ?? null,
      observedAt: Date.now(),
    }));
    await expect(
      page.getByRole("heading", {
        name: "Neutral asset authoring",
        exact: true,
      }),
    ).toBeVisible();
  } catch (error) {
    creationFailed = true;
    throw error;
  } finally {
    page.off("request", started);
    page.off("response", responded);
    page.off("requestfinished", finished);
    page.off("requestfailed", failed);
    if (creationFailed)
      await testInfo.attach("neutral-create-request-lifecycle", {
        body: JSON.stringify({
          scope:
            "passive native browser request diagnostics; heading timeout unchanged",
          elapsedMs: Date.now() - diagnosticStart,
          afterKeyboard,
          requests: requestLog,
        }),
        contentType: "application/json",
      });
  }
  const before = await page.evaluate(async () => ({
    projectId: localStorage.getItem("studio.projectId"),
    runs: (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
  }));
  async function add(kind: string, id: string, configure: () => Promise<void>) {
    await page
      .getByRole("button", { name: "Add element", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await page
      .getByLabel("Element family", { exact: true })
      .selectOption("logical");
    await page
      .getByLabel("Logical asset kind", { exact: true })
      .selectOption(kind);
    await page.getByLabel("Element identifier", { exact: true }).fill(id);
    await configure();
    await page
      .getByRole("button", { name: "Add logical asset", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    const entry = page
      .locator(".tree-list")
      .getByRole("button", { name: `${id} ${kind}`, exact: true });
    await entry.focus();
    await page.keyboard.press("Enter");
    await expect(
      page
        .locator(".inspector")
        .getByRole("heading", { name: id, exact: true }),
    ).toBeVisible();
  }
  await add("device", "measurement-device", async () => {
    await page
      .getByLabel("Logical containing node", { exact: true })
      .selectOption("plant-node");
    await page.getByLabel("physical", { exact: true }).check();
    await page
      .getByLabel("Optional new device port", { exact: true })
      .selectOption("output");
    await page
      .getByLabel("New port identifier", { exact: true })
      .fill("measurement-out");
    await page
      .getByLabel("New port interface", { exact: true })
      .selectOption("state");
  });
  await expect(
    page.locator(".inspector").getByText("simulated", { exact: false }).first(),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Edit logical asset", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await page
    .getByLabel("Logical containing node", { exact: true })
    .selectOption("");
  await page
    .getByRole("button", { name: "Save logical asset", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.locator(".inspector").getByText("Unplaced", { exact: true }),
  ).toBeVisible();
  await add("sensor", "state-sensor", async () => {
    await page
      .getByLabel("Associated logical device", { exact: true })
      .selectOption("measurement-device");
    await page
      .getByLabel("Output endpoint", { exact: true })
      .selectOption("measurement-out");
  });
  await add("actuator", "command-actuator", async () => {
    await page
      .getByLabel("Associated logical device", { exact: true })
      .selectOption("measurement-device");
    await page
      .getByLabel("Controlled quantity", { exact: true })
      .fill("command");
    await page
      .getByLabel("Input endpoint", { exact: true })
      .selectOption("plant-in");
  });
  await add("model", "logical-model", async () => {
    await page
      .getByRole("group", { name: "Input interfaces", exact: true })
      .getByLabel("command", { exact: true })
      .check();
    await page
      .getByRole("group", { name: "Output interfaces", exact: true })
      .getByLabel("state", { exact: true })
      .check();
    await page
      .getByLabel("Maturity", { exact: true })
      .selectOption("architectural-target");
  });
  await page
    .getByRole("button", { name: "View selected declaration", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  const source = page.getByLabel("XDL source", { exact: true });
  await expect(
    page.getByText("spec.models[id=logical-model]", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Selected declaration highlighted in this draft.", {
      exact: true,
    }),
  ).toBeVisible();
  const anchor = await source.evaluate((element: HTMLTextAreaElement) => ({
    selected: element.value.slice(element.selectionStart, element.selectionEnd),
    document: element.value,
  }));
  expect(anchor.selected).toContain("logical-model");
  expect(anchor.selected).toContain("opaque-reference");
  expect(anchor.document).toContain("measurement-out");
  const selectedDocument = await page
    .getByLabel("Resource", { exact: true })
    .inputValue();
  const file = await page.evaluate(async (projectId) => {
    const p = await fetch("/api/v1/projects/" + projectId).then((r) =>
      r.json(),
    );
    return Object.entries(p.documents).find(([, v]: any) =>
      v.content.includes("logical-model"),
    )?.[0];
  }, before.projectId);
  expect(selectedDocument).toBe(file);
  await page.screenshot({
    path: testInfo.outputPath("neutral-selected-source.png"),
    fullPage: true,
  });
  await page.keyboard.press("Escape");
  const projectSources = await page.evaluate(
    async (projectId) =>
      fetch("/api/v1/projects/" + projectId).then((r) => r.json()),
    before.projectId,
  );
  const resourceEntry = Object.entries(projectSources.documents)
    .map(([documentId, doc]: any) => ({
      documentId,
      resource: parse(doc.content),
    }))
    .find(({ resource }) => resource.kind === "Component")!;
  await page
    .locator(".tree-section")
    .getByRole("button", {
      name: `${resourceEntry.resource.metadata.name} Component`,
      exact: true,
    })
    .focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Resource", { exact: true })).toHaveValue(
    resourceEntry.documentId,
  );
  await expect(page.getByText("Selected declaration highlighted in this draft.",{exact:true})).toBeVisible();
  expect(
    await page
      .getByLabel("XDL source", { exact: true })
      .evaluate((node: HTMLTextAreaElement) =>
        node.value.slice(node.selectionStart, node.selectionEnd),
      ),
  ).toContain("kind: Component");
  await page.keyboard.press("Escape");
  await page.reload();
  await page.getByRole("button", { name: "Table view", exact: true }).focus();
  await page.keyboard.press("Enter");
  for (const id of [
    "measurement-device",
    "state-sensor",
    "command-actuator",
    "logical-model",
  ]) {
    await expect(
      page.getByRole("table").getByRole("button", { name: id, exact: true }),
    ).toBeVisible();
  }
  await page
    .getByRole("button", { name: "logical-model", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await page.screenshot({
    path: testInfo.outputPath("neutral-assets-table.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  await expect(
    page.getByText("Authoritative platform validation passed.", {
      exact: false,
    }),
  ).toBeVisible();
  const refusal = page.waitForResponse(
    (r) => r.url().endsWith("/preflights") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  const rejected = await refusal;
  expect(rejected.status()).toBe(200);
  const refusalBody = await rejected.json();
  expect(refusalBody.status).not.toBe("ready");
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeDisabled();
  const runsAfter = await page.evaluate(
    async () =>
      (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
  );
  expect(runsAfter).toBe(before.runs);
  await testInfo.attach("neutral-asset-admission-refusal", {
    body: JSON.stringify(refusalBody, null, 2),
    contentType: "application/json",
  });
  await page.keyboard.press("Escape");
  return before.projectId!;
}
