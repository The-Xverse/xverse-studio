import { test, expect, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { connectStudio } from "./connect-studio";

async function projectWithSystem(
  page: Page,
  name: string,
  variant?: string,
  transform: (content: string) => string = (content) => content,
) {
  const generated = variant
    ? execFileSync(
        path.resolve(".venv/bin/python"),
        [
          "-I",
          "tests/fixtures/connections/connection_fixtures.py",
          "--variant",
          variant,
        ],
        { encoding: "utf8" },
      )
    : null;
  const content = generated === null ? null : transform(generated);
  const project = await page.evaluate(
    async ({ name, content }) => {
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
      let project = await r.json();
      if (content) {
        const [id] = Object.entries(project.documents).find(([, d]: any) =>
          d.path.endsWith("/system.xdl.yaml"),
        )!;
        r = await fetch(
          `/api/v1/projects/${project.projectId}/documents/${id}`,
          {
            method: "PUT",
            headers: { ...headers, "If-Match": String(project.revision) },
            body: JSON.stringify({ content, format: "yaml" }),
          },
        );
        if (!r.ok) throw Error(await r.text());
        project = await r.json();
      }
      localStorage.setItem("studio.projectId", project.projectId);
      return project;
    },
    { name, content },
  );
  await page.reload();
  await page.getByRole("tab", { name: /Connections/ }).click();
  return project;
}

test("connections: admission is shown per flow and the connect form guides compatible targets", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  await projectWithSystem(page, "Connection admission");
  const summary = page.getByRole("region", { name: "Connection admission" });
  await expect(summary).toContainText(
    "All 2 declared flows are admitted for their declared semantics.",
  );
  await expect(summary).toContainText(
    "not prove routing, traffic or executable correctness",
  );
  await expect(summary).toContainText(
    "converter yes, versionCompatibility no, quality no, causality yes, modelCoupling no",
  );
  await expect(summary).toContainText(
    "Communication flows are never presented as physical couplings.",
  );
  const commandFlow = page.getByRole("button", {
    name: /^Admission admitted; show checks for .*#command-flow$/,
  });
  await commandFlow.click();
  await expect(commandFlow).toHaveAttribute("aria-expanded", "true");
  await expect(page.locator(".admission-checks").first()).toContainText(
    "Exact interface compatibility; no conversion is involved.",
  );
  // Guidance: same interface and input capability; others are listed with the reason.
  await page.getByLabel("Source endpoint").selectOption("controller-out");
  const destination = page.getByLabel("Destination endpoint");
  await expect(
    destination.locator("option", { hasText: "plant-in" }),
  ).toHaveJSProperty("disabled", false);
  await expect(
    destination.locator("option", { hasText: "observer-in" }),
  ).toHaveJSProperty("disabled", true);
  await expect(
    destination.locator("option", { hasText: "observer-in" }),
  ).toContainText(
    "Interface state differs from command; no converter is admitted.",
  );
  await expect(
    destination.locator("option", { hasText: "plant-out" }),
  ).toContainText("Not input-capable.");
  await expect(page.locator("#target-guidance")).toContainText(
    "1 compatible destination(s)",
  );
});

test("connections: an undelayed feedback cycle and an undeclared converter are never admitted or converted", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  await projectWithSystem(page, "Feedback cycle", "feedback-cycle");
  const summary = page.getByRole("region", { name: "Connection admission" });
  await expect(summary).toContainText(
    "2 of 3 flows cannot execute as declared",
  );
  await expect(summary).toContainText("1 feedback cycle(s) not admitted");
  await expect(summary.getByRole("listitem").first()).toContainText(
    "members controller, plant",
  );
  await expect(summary).toContainText(
    "No flow in this feedback cycle declares a unit delay, so the loop is algebraic",
  );
  await projectWithSystem(page, "Explicit converter", "explicit-converter");
  await expect(
    page.getByRole("button", {
      name: /^Admission rejected; show checks for .*#command-flow$/,
    }),
  ).toBeVisible();
  await page.getByLabel("Source endpoint").selectOption("controller-out");
  await page.getByLabel("Destination endpoint").selectOption("plant-in");
  await expect(page.locator("#target-guidance")).toContainText(
    "Interface requires an explicit converter; declare a converter mapping the selected provider admits, or this connection is rejected.",
  );
});

test("connections: the owned feedback blueprint shows its admitted unit-delay loop and linear converter", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  await page.evaluate(async () => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const project = await fetch("/api/v1/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({
        name: "Feedback contracts",
        blueprintRef: "reference-feedback",
      }),
    }).then((r) => r.json());
    localStorage.setItem("studio.projectId", project.projectId);
  });
  await page.reload();
  await page.getByRole("tab", { name: /Connections/ }).click();
  const summary = page.getByRole("region", { name: "Connection admission" });
  await expect(summary).toContainText(
    "All 4 declared flows are admitted for their declared semantics.",
  );
  await expect(summary).toContainText(
    "1 feedback cycle(s) admitted under a declared unit-delay contract.",
  );
  await expect(
    summary.locator("li").filter({ hasText: "members" }),
  ).toContainText("admitted");
  const stateFlow = page.getByRole("button", {
    name: /^Admission admitted; show checks for .*#state-flow$/,
  });
  await stateFlow.click();
  await expect(page.locator(".converter-mapping")).toHaveText(
    " y = 100·x + 0 (1 → %)",
  );
  const command = page.getByRole("button", {
    name: /^Admission admitted; show checks for .*#command-flow$/,
  });
  await command.click();
  await expect(
    page.locator(".admission-checks").filter({ hasText: "causality" }).last(),
  ).toContainText("Admitted under unit-delay causality on command-flow");
});

test("connections: relations are shown by kind with their own meaning and actions, and contracts are declared per flow", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  await projectWithSystem(page, "Relation kinds", "model-coupling", (content) =>
    content.replace(
      "  provenance:\n",
      "  traceability:\n  - relation: satisfies\n    ref: urn:example:requirement:loop-1\n    revision: '3'\n    maturity: prototype\n    elementId: controller\n  provenance:\n",
    ),
  );
  const kinds = page.getByRole("region", { name: "Relations by kind" });
  await expect(kinds.locator(".relation-coupling")).toContainText(
    "no model-coupling provider or solver is admitted",
  );
  await expect(kinds.locator(".relation-deployment")).toContainText(
    "controller → reference-target (simulated) in local-reference",
  );
  await expect(kinds.locator(".relation-traceability")).toContainText(
    "satisfies urn:example:requirement:loop-1 (3)",
  );
  await expect(kinds.locator(".relation-traceability")).toContainText(
    "never fetched and never proves a result",
  );
  await kinds
    .getByRole("button", { name: "Edit placement in Deployment" })
    .click();
  await expect(
    page.getByRole("tab", { name: "Deployment", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  // A unit delay declared on a flow outside any cycle is recorded without admission effect.
  await page.getByRole("tab", { name: /Connections/ }).click();
  const form = page.getByRole("form", { name: "Flow contract" });
  await form.locator("select").first().selectOption("command-flow");
  await form.getByLabel(/Unit delay/).check();
  await form.getByRole("button", { name: "Save flow contract" }).click();
  const command = page.getByRole("button", {
    name: /show checks for .*#command-flow$/,
  });
  await command.click();
  await expect(
    page
      .locator(".admission-checks")
      .filter({ hasText: "outside any feedback cycle" }),
  ).toBeVisible();
});
