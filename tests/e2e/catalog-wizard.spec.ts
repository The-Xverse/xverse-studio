import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import type { AddressInfo } from "node:net";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
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

async function importFixture(
  page: import("@playwright/test").Page,
  variant: string,
) {
  const archive = execFileSync(
    path.resolve(".venv/bin/python"),
    [
      "-I",
      "tests/fixtures/projects/create_catalog_archive.py",
      "--variant",
      variant,
    ],
    { encoding: "utf8" },
  ).trim();
  const project = await page.evaluate(async (archiveBase64) => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const r = await fetch("/api/v1/projects/imports", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ archiveBase64 }),
    });
    if (!r.ok) throw Error(await r.text());
    const project = await r.json();
    localStorage.setItem("studio.projectId", project.projectId);
    return project;
  }, archive);
  await page.reload();
  return project;
}

test("instance wizard: representative service and controller instances are generic roles, not core types", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await importFixture(page, "service");
  const add = async (
    definition: RegExp,
    id: string,
    role: string,
    node: string,
  ) => {
    await page
      .getByRole("button", { name: "Add element", exact: true })
      .click();
    const dialog = page.getByRole("dialog");
    await dialog
      .getByRole("radiogroup", { name: "Definitions" })
      .getByRole("radio", { name: definition })
      .check();
    await dialog.getByLabel("Instance identifier").fill(id);
    await dialog.getByLabel("Role filter").selectOption(role);
    await dialog.getByLabel("Placement node").selectOption(node);
    await dialog.getByRole("button", { name: "Add instance" }).click();
    await expect(dialog).toHaveCount(0);
  };
  await add(
    /telemetry-service org\.xverse\.studio\.process-control/,
    "telemetry-gateway",
    "service",
    "service-node",
  );
  await add(
    /reference-controller org\.xverse\.studio\.process-control/,
    "backup-controller",
    "controller",
    "controller-node",
  );
  const saved = await page.request
    .get(`/api/v1/projects/${project.projectId}`)
    .then((r) => r.json());
  const system = (Object.values(saved.documents) as any[]).find((d) =>
    d.path.endsWith("/system.xdl.yaml"),
  ).content as string;
  expect(system).toMatch(
    /- id: telemetry-gateway\n[\s\S]*?name: telemetry-service\n\s+nodeId: service-node/,
  );
  expect(system).toMatch(
    /- id: backup-controller\n[\s\S]*?name: reference-controller\n\s+nodeId: controller-node/,
  );
  const valid = await page.evaluate(
    async ({ projectId, revision }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      return fetch(`/api/v1/projects/${projectId}/validations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({ revision }),
      }).then((r) => r.json());
    },
    { projectId: project.projectId, revision: saved.revision },
  );
  expect(valid.valid).toBe(true);
});

test("instance wizard: a definition in a non-admitted XDL version stays inspectable but cannot be instantiated", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await importFixture(page, "unsupported");
  const writes: string[] = [];
  page.on("request", (r) => {
    if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
      writes.push(r.method() + " " + new URL(r.url()).pathname);
  });
  await page.getByRole("button", { name: "Add element", exact: true }).click();
  const dialog = page.getByRole("dialog");
  const option = dialog
    .getByRole("radiogroup", { name: "Definitions" })
    .getByRole("radio", { name: /telemetry-service/ });
  await option.check();
  await expect(
    dialog.locator(".wizard-option", { hasText: "telemetry-service" }),
  ).toContainText("unsupported version");
  await dialog.getByLabel("Instance identifier").fill("telemetry-gateway");
  await expect(dialog.getByRole("region", { name: "Review" })).toContainText(
    "XDL version xverse.io/xdl/v9 is not admitted",
  );
  await expect(
    dialog.getByRole("button", { name: "Add instance" }),
  ).toBeDisabled();
  await dialog.getByRole("button", { name: "Close dialog" }).click();
  // The original bytes remain readable.
  const current = await page.request
    .get(`/api/v1/projects/${project.projectId}`)
    .then((r) => r.json());
  expect(
    (Object.values(current.documents) as any[]).find((d) =>
      d.path.endsWith("/service.xdl.yaml"),
    ).content,
  ).toContain("apiVersion: xverse.io/xdl/v9");
  expect(writes).toEqual([]);
});

test("implementation registration: invalid versions are refused and a registered artifact stays inert metadata", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const data = process.env.STUDIO_BROWSER_DATA!;
  // Every file outside the database (and this test's session) with its content digest.
  const files = () =>
    (readdirSync(data, { recursive: true }) as string[])
      .filter((name) => !/^studio\.sqlite|browser-session/.test(name))
      .filter((name) => statSync(path.join(data, name)).isFile())
      .sort()
      .map(
        (name) =>
          name +
          ":" +
          createHash("sha256")
            .update(readFileSync(path.join(data, name)))
            .digest("hex"),
      );
  // A fetchable origin: registration must never contact it.
  let originHits = 0;
  const origin = createServer((_, response) => {
    originHits++;
    response.end("artifact bytes");
  });
  await new Promise<void>((resolve) => origin.listen(0, "127.0.0.1", resolve));
  const originUrl = `http://127.0.0.1:${(origin.address() as AddressInfo).port}/firmware.bin`;
  const before = files();
  const runsBefore = await page.request
    .get("/api/v1/runs")
    .then((r) => r.json());
  const writes: string[] = [];
  page.on("request", (r) => {
    if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
      writes.push(r.method() + " " + new URL(r.url()).pathname);
  });
  await page.getByRole("button", { name: "Catalog", exact: true }).click();
  await page
    .getByRole("button", { name: "Register artifact metadata", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Artifact name").fill("neutral-firmware-image");
  await dialog.getByLabel("Artifact version").fill("1.0");
  await dialog.getByLabel("Artifact kind").selectOption("firmware");
  await dialog
    .getByLabel("Declared SHA-256 digest")
    .fill("sha256:" + "a1".repeat(32));
  await dialog.getByLabel("Portable origin reference").fill(originUrl);
  await dialog.getByRole("button", { name: "Register metadata only" }).click();
  // The malformed version is refused before any request is sent.
  await expect(dialog.getByLabel("Artifact version")).toHaveJSProperty(
    "validity.valid",
    false,
  );
  expect(writes).toEqual([]);
  await dialog.getByLabel("Artifact version").fill("1.0.0-rc.1");
  await dialog.getByRole("button", { name: "Register metadata only" }).click();
  await expect(
    page.getByText(
      "Artifact metadata registered. No artifact was downloaded or executed.",
    ),
  ).toBeVisible();
  expect(writes).toEqual(["POST /api/v1/catalog/artifacts"]);
  const entry = (
    await page.request.get("/api/v1/catalog").then((r) => r.json())
  ).items.find((e: any) => e.name === "neutral-firmware-image");
  expect(entry).toMatchObject({
    kind: "artifact",
    version: "1.0.0-rc.1",
    availability: "unavailable",
    executionAllowed: false,
    provenance: { registration: "metadata_only" },
  });
  // No build, flash or execution: no runs and no new files beside the database.
  const runsAfter = await page.request
    .get("/api/v1/runs")
    .then((r) => r.json());
  expect(runsAfter.items.length).toBe(runsBefore.items.length);
  expect(files()).toEqual(before);
  expect(entry.originRef).toBe(originUrl);
  expect(originHits).toBe(0);
  await new Promise((resolve) => origin.close(resolve));
});
