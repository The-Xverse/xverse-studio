import { test, expect } from "@playwright/test";
import { connectStudio } from "./connect-studio";

// Rewrites one YAML block of an authored document through the source API (exact text, no parser).
async function replaceSource(
  page: any,
  projectId: string,
  suffix: string,
  from: string,
  to: string,
) {
  return page.evaluate(
    async ({ projectId, suffix, from, to }: Record<string, string>) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const project = await fetch(`/api/v1/projects/${projectId}`).then((r) =>
        r.json(),
      );
      const [id, document] = Object.entries(project.documents).find(
        ([, d]: any) => d.path.endsWith(suffix),
      ) as [string, any];
      if (!document.content.includes(from)) throw new Error("anchor missing");
      const response = await fetch(
        `/api/v1/projects/${projectId}/documents/${id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
            "If-Match": String(project.revision),
          },
          body: JSON.stringify({
            content: document.content.replace(from, to),
          }),
        },
      );
      if (!response.ok) throw new Error(await response.text());
    },
    { projectId, suffix, from, to },
  );
}

test("deployment resolution: effective values, bound resources and variant comparison", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  const projectId = await page.evaluate(async () => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const headers = {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    };
    let project = await fetch("/api/v1/projects", {
      method: "POST",
      headers,
      body: JSON.stringify({ name: "Deployment resolution" }),
    }).then((r) => r.json());
    project = await fetch(
      `/api/v1/projects/${project.projectId}/deployment-variants`,
      {
        method: "POST",
        headers: { ...headers, "If-Match": String(project.revision) },
        body: JSON.stringify({
          baseRevision: project.revision,
          name: "Bench variant",
        }),
      },
    ).then((r) => r.json());
    return project.project.projectId as string;
  });
  // A declared parameter with a default, an instance value and a binding value in the original variant.
  await replaceSource(
    page,
    projectId,
    "/plant.xdl.yaml",
    "  capabilities:\n",
    "  parameters:\n  - id: rate\n    valueType: number\n    unitSemantics: 1/s\n    default: 1.0\n    mutability: configuration\n  capabilities:\n",
  );
  await replaceSource(
    page,
    projectId,
    "/system.xdl.yaml",
    "      name: reference-plant\n    nodeId: plant-node\n",
    "      name: reference-plant\n    nodeId: plant-node\n    parameterValues:\n      rate: 2.0\n",
  );
  await replaceSource(
    page,
    projectId,
    "xdl/deployment.xdl.yaml",
    "  - id: plant-binding\n",
    "  - id: plant-binding\n    parameterValues:\n      rate: 3.0\n",
  );
  // A second System clock lets the bench variant author a time mapping.
  await replaceSource(
    page,
    projectId,
    "/system.xdl.yaml",
    "  defaultTimeDomainId: simulation-time\n",
    "  - id: wall-time\n    clockClass: wall\n    epoch: unix\n    rate: '1'\n    monotonic: false\n  defaultTimeDomainId: simulation-time\n",
  );
  // The bench variant declares a resource that its target offers.
  await replaceSource(
    page,
    projectId,
    "/deployment-bench-variant.xdl.yaml",
    "  targets:\n  - id: reference-target\n",
    "  resources:\n  - id: bench-cpu\n    resourceClass: cpu\n    capacity:\n      value: 2\n      unit: core\n    allocationPolicy: exclusive\n  targets:\n  - id: reference-target\n    offeredResourceIds:\n    - bench-cpu\n",
  );
  await page.evaluate(
    (id) => localStorage.setItem("studio.projectId", id),
    projectId,
  );
  await page.reload();
  await page.getByRole("tab", { name: "Deployment", exact: true }).click();
  await page
    .getByLabel("Deployment variant")
    .selectOption({ label: "local-reference" });
  const resolution = page.getByRole("region", {
    name: "Resolution and effective configuration",
  });
  await expect(resolution.getByRole("status")).toContainText("1 blocking");
  await expect(resolution).toContainText(
    "Fidelity limit: Scalar first-order reference model only",
  );
  const rate = resolution.getByRole("row", { name: /plant\.rate/ });
  await expect(rate).toContainText("ambiguous");
  await expect(rate).toContainText("PRECEDENCE_UNDEFINED");
  await expect(rate.locator(".value-chain li")).toHaveText([
    /^definition-default 1 xdl\/plant\.xdl\.yaml#\/spec\/parameters\/0\/default$/,
    /^system-instance 2 xdl\/system\.xdl\.yaml#\/spec\/componentInstances\/1\/parameterValues\/rate$/,
    /^deployment-binding 3 xdl\/deployment\.xdl\.yaml#\/spec\/bindings\/1\/parameterValues\/rate$/,
  ]);
  // Compare against the bench variant: the logical System is shared, effective values differ.
  await page
    .getByLabel("Comparison variant")
    .selectOption({ label: "bench-variant" });
  const comparison = page.getByRole("region", {
    name: "Compare realization and placement",
  });
  await expect(comparison.getByRole("status")).toContainText(
    "logical element identities are shared",
  );
  await expect(comparison.getByRole("status")).toContainText(
    "does not establish behavioural equivalence",
  );
  await expect(comparison).toContainText(
    "plant.rate: definition-default 1, system-instance 2, deployment-binding 3 (ambiguous) → definition-default 1, system-instance 2 (overridden)",
  );
  const plantRow = comparison.getByRole("row", { name: /^plant/ });
  await expect(plantRow.locator("td").first()).toContainText(
    "simulated → reference-target (model-unit)",
  );
  await expect(plantRow.locator("td").nth(1)).toContainText("resources none");
  await resolution.screenshot({ path: testInfo.outputPath("resolution.png") });
  await comparison.screenshot({ path: testInfo.outputPath("comparison.png") });
  // Bind the offered resource in the bench variant through the form; placement passes.
  const sourceOf = async (suffix: string) =>
    (
      Object.values(
        (
          await page.request
            .get(`/api/v1/projects/${projectId}`)
            .then((r) => r.json())
        ).documents,
      ) as any[]
    ).find((d) => d.path.endsWith(suffix)).content as string;
  const originalBefore = await sourceOf("xdl/deployment.xdl.yaml");
  await page
    .getByLabel("Deployment variant")
    .selectOption({ label: "bench-variant" });
  await page.getByLabel("Binding for resources").selectOption("plant-binding");
  await page.getByRole("checkbox", { name: /bench-cpu/ }).check();
  await page.getByRole("button", { name: "Save bound resources" }).click();
  await expect(
    resolution.getByRole("row", { name: /plant via plant-binding/ }),
  ).toContainText("Target reference-target offers resource bench-cpu.");
  // A clock mapping is authored through the form and resolved as declared, never evaluated.
  const time = page.getByRole("region", { name: "Time mappings" });
  await time.getByLabel("Mapping identifier").fill("wall-to-sim");
  await time.getByLabel("Source clock").selectOption("wall-time");
  await time.getByLabel("Target clock").selectOption("simulation-time");
  await time.getByLabel("Mapping description").fill("offset-at-start");
  await time.getByLabel("Tolerance", { exact: true }).fill("0.01");
  await time.getByRole("button", { name: "Save time mapping" }).click();
  await expect(time).toContainText(
    "wall-to-sim: wall-time → simulation-time (offset-at-start, ±0.01 s)",
  );
  await expect(resolution).toContainText(
    "Time mapping wall-to-sim (offset-at-start) is recorded; its accuracy is not evaluated.",
  );
  await time
    .getByRole("button", { name: "Remove time mapping wall-to-sim" })
    .click();
  await expect(time).toContainText("No time mappings.");
  // Only the bench variant changed; the original deployment's bytes are untouched.
  expect(await sourceOf("xdl/deployment.xdl.yaml")).toBe(originalBefore);
  expect(await sourceOf("/deployment-bench-variant.xdl.yaml")).toContain(
    "- bench-cpu",
  );
});
