import { test, expect } from "@playwright/test";
import { connectStudio } from "./connect-studio";

test("instance wizard: role, placement and realization are separate choices committed as existing XDL", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await page.evaluate(async () => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const r = await fetch("/api/v1/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ name: "Instance wizard" }),
    });
    const project = await r.json();
    localStorage.setItem("studio.projectId", project.projectId);
    return project;
  });
  await page.reload();
  const writes: string[] = [];
  page.on("request", (r) => {
    if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
      writes.push(r.method() + " " + new URL(r.url()).pathname);
  });
  await page.getByRole("button", { name: "Add element", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByLabel("Element family")).toHaveValue("component");
  // 1. Definition: project and catalog definitions keep their own identities.
  await dialog.getByLabel("Search definitions").fill("state");
  const definitions = dialog.getByRole("radiogroup", { name: "Definitions" });
  await expect(definitions.getByRole("radio")).toHaveCount(2);
  await definitions
    .getByRole("radio", {
      name: /reference-plant org\.xverse\.studio\.reference/,
    })
    .check();
  await expect(definitions).toContainText("catalog only");
  await expect(dialog.getByLabel("Definition details")).toContainText(
    "Declared realization support: simulated",
  );
  await expect(dialog.getByRole("region", { name: "Review" })).toContainText(
    "can be inspected but not instantiated",
  );
  await definitions
    .getByRole("radio", {
      name: /reference-plant org\.xverse\.studio\.process-control/,
    })
    .check();
  const details = dialog.getByLabel("Definition details");
  await expect(details).toContainText("state (bidirectional, unit 1)");
  await expect(details).toContainText(
    "model first-order → urn:xverse:studio:reference:first-order:v1",
  );
  await expect(
    dialog.getByText("The definition declares no configuration parameters."),
  ).toBeVisible();
  // 2. Identity: invalid identifiers block submission with a stated reason.
  const submit = dialog.getByRole("button", { name: "Add instance" });
  await dialog.getByLabel("Instance identifier").fill("Bad_ID");
  await expect(submit).toBeDisabled();
  await expect(dialog.getByRole("region", { name: "Review" })).toContainText(
    "lowercase, hyphenated instance identifier",
  );
  await dialog.getByLabel("Instance identifier").fill("second-plant");
  // 3. Role filter narrows placement; the node choice is the placement.
  await dialog.getByLabel("Role filter").selectOption("plant");
  const placement = dialog.getByLabel("Placement node");
  await expect(placement.locator("option")).toHaveText([
    "Not placed on a node",
    "plant-node (plant)",
  ]);
  await placement.selectOption("plant-node");
  // 4. Realization is a separate, optional deployment binding.
  await dialog
    .getByLabel("Deployment variant")
    .selectOption({ label: "local-reference" });
  await expect(submit).toBeDisabled(); // a target is required once a variant is chosen
  await dialog
    .getByRole("radiogroup", { name: "Realization class" })
    .getByRole("radio", { name: "virtual" })
    .check();
  await dialog.getByLabel("Deployment target").selectOption("reference-target");
  await dialog.getByRole("checkbox", { name: /reference-model/ }).check();
  const review = dialog.getByRole("region", { name: "Review" });
  await expect(review.getByRole("listitem")).toHaveText([
    "Add instance second-plant of reference-plant on node plant-node",
    /^Bind second-plant as virtual to target reference-target \(second-plant-binding\) with lifecycle prepare, ready, start, stop, failure$/,
  ]);
  await expect(review).toContainText("Nothing is built, flashed or executed");
  await submit.focus();
  await page.keyboard.press("Enter");
  await expect(dialog).toHaveCount(0);
  await expect(
    page.getByText("Draft saved. Existing run snapshots remain unchanged."),
  ).toBeVisible();
  // Exactly one semantic transaction; no artifact, run or provider operation.
  expect(writes).toEqual([`POST /api/v1/projects/${project.projectId}/edits`]);
  const saved = await page.request
    .get(`/api/v1/projects/${project.projectId}`)
    .then((r) => r.json());
  expect(saved.revision).toBe(project.revision + 1);
  const source = (suffix: string) =>
    (Object.values(saved.documents) as any[]).find((d) =>
      d.path.endsWith(suffix),
    ).content as string;
  expect(source("/system.xdl.yaml")).toMatch(
    /- id: second-plant\n\s+componentRef:[\s\S]*?name: reference-plant\n\s+nodeId: plant-node/,
  );
  expect(source("/deployment.xdl.yaml")).toMatch(
    /- id: second-plant-binding\n\s+logicalRef:[\s\S]*?element: second-plant\n\s+realizationClass: virtual\n\s+targetId: reference-target/,
  );
  // The reusable definition itself is unchanged.
  expect(source("/plant.xdl.yaml")).toBe(
    (Object.values(project.documents) as any[]).find((d) =>
      d.path.endsWith("/plant.xdl.yaml"),
    ).content,
  );
  const history = await page.request
    .get(`/api/v1/projects/${project.projectId}/revisions?limit=1`)
    .then((r) => r.json());
  expect(history.items[0].origin.edits).toEqual(["add_element", "add_binding"]);
});

test("instance wizard: configuration follows the definition's typed parameters and hidden selections cannot be submitted", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await page.evaluate(async () => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const headers = {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    };
    let r = await fetch("/api/v1/projects", {
      method: "POST",
      headers,
      body: JSON.stringify({ name: "Configurable instance" }),
    });
    let project = await r.json();
    const [id, plant] = Object.entries(project.documents).find(([, d]: any) =>
      d.path.endsWith("/plant.xdl.yaml"),
    ) as [string, any];
    // Declare one typed configuration parameter on the reusable definition.
    const content = plant.content.replace(
      "  models:\n",
      "  parameters:\n  - id: response-scale\n    valueType: number\n    unitSemantics: '1'\n    mutability: configuration\n    default: 1.0\n    description: Scales the response.\n  models:\n",
    );
    r = await fetch(`/api/v1/projects/${project.projectId}/documents/${id}`, {
      method: "PUT",
      headers: { ...headers, "If-Match": String(project.revision) },
      body: JSON.stringify({ content, format: "yaml" }),
    });
    if (!r.ok) throw Error(await r.text());
    project = await r.json();
    localStorage.setItem("studio.projectId", project.projectId);
    return project;
  });
  await page.reload();
  await page.getByRole("button", { name: "Add element", exact: true }).click();
  const dialog = page.getByRole("dialog");
  const definitions = dialog.getByRole("radiogroup", { name: "Definitions" });
  await definitions
    .getByRole("radio", {
      name: /reference-plant org\.xverse\.studio\.process-control/,
    })
    .check();
  await dialog.getByLabel("Instance identifier").fill("scaled-plant");
  const scale = dialog.getByLabel("response-scale (number, unit 1)");
  await expect(scale).toHaveValue("1");
  await expect(
    dialog.getByText(/Scales the response\. Default 1\./),
  ).toBeVisible();
  await scale.fill("2.5");
  const review = dialog.getByRole("region", { name: "Review" });
  await expect(review.getByRole("listitem")).toHaveText([
    "Add instance scaled-plant of reference-plant, not placed with response-scale configured",
  ]);
  // A selection hidden by the filters is not the selection.
  await dialog.getByLabel("Search definitions").fill("controller");
  await expect(review).toContainText("Choose a reusable definition.");
  await expect(
    dialog.getByRole("button", { name: "Add instance" }),
  ).toBeDisabled();
  await dialog.getByLabel("Search definitions").fill("");
  await expect(review.getByRole("listitem")).toHaveCount(1);
  await dialog.getByRole("button", { name: "Add instance" }).click();
  await expect(dialog).toHaveCount(0);
  const saved = await page.request
    .get(`/api/v1/projects/${project.projectId}`)
    .then((r) => r.json());
  const system = (Object.values(saved.documents) as any[]).find((d) =>
    d.path.endsWith("/system.xdl.yaml"),
  ).content as string;
  expect(system).toMatch(
    /- id: scaled-plant\n\s+componentRef:[\s\S]*?parameterValues:\n\s+response-scale: 2\.5/,
  );
});
