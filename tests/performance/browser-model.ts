import { expect, type Page, type TestInfo } from "@playwright/test";
import { parse, stringify } from "yaml";
import { writeFileSync } from "node:fs";
export async function measureModel(page: Page, testInfo: TestInfo) {
  const request = async (path: string, body?: unknown, revision?: number) =>
    page.evaluate(
      async ({ path, body, revision }) => {
        const s = await (await fetch("/api/v1/session")).json();
        const r = await fetch("/api/v1" + path, {
          method:
            body === undefined
              ? "GET"
              : path.includes("/documents/")
                ? "PUT"
                : "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": s.csrfToken,
            ...(revision ? { "If-Match": String(revision) } : {}),
          },
          body: body === undefined ? undefined : JSON.stringify(body),
        });
        const data = await r.json();
        if (!r.ok) throw new Error(`Fixture request rejected: ${data.code}`);
        return data;
      },
      { path, body, revision },
    );
  let project = await request("/projects", {
    name: `Performance reference ${Date.now()} · 200 elements / 400 flows`,
  });
  const docId = Object.keys(project.documents).find(
    (key) => parse(project.documents[key].content).kind === "System",
  )!;
  const system = parse(project.documents[docId].content),
    componentRef = system.spec.componentInstances[0].componentRef;
  system.spec.nodes = Array.from({ length: 200 }, (_, i) => ({
    id: `host-${i}`,
    roles: ["reference"],
  }));
  system.spec.componentInstances = Array.from({ length: 200 }, (_, i) => ({
    id: i === 0 ? "controller" : i === 1 ? "plant" : `element-${i}`,
    nodeId: `host-${i}`,
    componentRef: { ...componentRef },
  }));
  system.spec.endpoints = Array.from({ length: 200 }, (_, i) => [
    {
      id: `out-${i}`,
      ownerId: i === 0 ? "controller" : i === 1 ? "plant" : `element-${i}`,
      interfaceId: "command",
      direction: "output",
    },
    {
      id: `in-${i}`,
      ownerId: i === 0 ? "controller" : i === 1 ? "plant" : `element-${i}`,
      interfaceId: "command",
      direction: "input",
    },
  ]).flat();
  const pairs: number[][] = [];
  for (let i = 0; i < 200; i++) {
    if (i + 1 < 200) pairs.push([i, i + 1]);
    if (i + 2 < 200) pairs.push([i, i + 2]);
  }
  pairs.push([0, 3], [1, 4], [2, 5]);
  system.spec.flows = pairs.map(([source, target], i) => ({
    id: i === 0 ? "state-flow" : `flow-${i}`,
    sourceEndpointId: `out-${source}`,
    destinationEndpointIds: [`in-${target}`],
    interfaceId: "command",
    timeDomainId: "simulation-time",
    deliveryIntent: "ordered",
  }));
  expect(system.spec.flows.length).toBe(400);
  project = await request(
    `/projects/${project.projectId}/documents/${docId}`,
    { content: stringify(system), format: "yaml" },
    project.revision,
  );
  await page.evaluate(
    (projectId) => localStorage.setItem("studio.projectId", projectId),
    project.projectId,
  );
  await page.reload();
  await expect(page.locator(".tree-list button")).toHaveCount(200);
  const opens: number[] = [],
    selections: number[] = [];
  for (let i = -1; i < 30; i++) {
    await page
      .getByRole("button", { name: "X-Verse Studio home", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Recent projects", exact: true }),
    ).toBeVisible();
    const begin = await page.evaluate(() => performance.now());
    await page
      .locator(".project-list")
      .getByRole("button")
      .filter({ hasText: project.name })
      .click();
    await expect(page.locator(".tree-list button")).toHaveCount(200);
    await page.getByRole("button", { name: "Validate", exact: true }).click();
    await expect(page.locator(".alerts")).toContainText(
      /Authoritative platform validation passed|Validation found issues/,
    );
    const end = await page.evaluate(() => performance.now());
    const elapsed = await page.evaluate(
      async (index) => {
        const id =
            index === 0
              ? "controller"
              : index === 1
                ? "plant"
                : `element-${index}`,
          button = [
            ...document.querySelectorAll<HTMLButtonElement>(
              ".tree-list button",
            ),
          ].find((b) => b.querySelector("span")?.textContent === id)!;
        const start = performance.now();
        button.click();
        return new Promise<number>((resolve) =>
          requestAnimationFrame(() =>
            requestAnimationFrame(() => resolve(performance.now() - start)),
          ),
        );
      },
      i < 0 ? 0 : i + 1,
    );
    await expect(page.locator(".inspector-summary h3")).toHaveText(
      i < 0 ? "controller" : i === 0 ? "plant" : `element-${i + 1}`,
    );
    if (i >= 0) {
      opens.push(end - begin);
      selections.push(elapsed);
    }
  }
  const p95 = (values: number[]) =>
    [...values].sort((a, b) => a - b)[Math.ceil(values.length * 0.95) - 1];
  const result = {
    scope: "owned-browser-rendering-fixture; no live-provider or Windows claim",
    platform: process.platform,
    architecture: process.arch,
    browser: await page.context().browser()?.version(),
    viewport: page.viewportSize(),
    elements: 200,
    connections: 400,
    warmups: 1,
    repetitions: 30,
    openAndValidationPresentation: {
      milliseconds: opens,
      p95: p95(opens),
      threshold: 3000,
      passed: p95(opens) <= 3000,
    },
    selectionAndInspector: {
      milliseconds: selections,
      p95: p95(selections),
      threshold: 150,
      passed: p95(selections) <= 150,
    },
    limitations: [
      "The workload is an authored presentation/validation fixture; no runtime scalability or model fidelity is claimed.",
      "Native Windows and other browser engine measurements NOT_RUN.",
    ],
  };
  writeFileSync(
    testInfo.outputPath("model-performance.json"),
    JSON.stringify(result, null, 2),
  );
  await page.screenshot({
    path: testInfo.outputPath("model-performance.png"),
    fullPage: true,
  });
  expect(result.openAndValidationPresentation.passed).toBe(true);
  expect(result.selectionAndInspector.passed).toBe(true);
}
