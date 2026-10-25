import { test, expect, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { connectStudio } from "./connect-studio";

async function projectWithSystem(page: Page, name: string, variant?: string) {
  const content = variant
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
    "converter no, versionCompatibility no, quality no, causality no, modelCoupling no",
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

test("connections: a feedback cycle and an explicit converter are reported as unsupported, never converted", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  await projectWithSystem(page, "Feedback cycle", "feedback-cycle");
  const summary = page.getByRole("region", { name: "Connection admission" });
  await expect(summary).toContainText(
    "2 of 3 flows cannot execute as declared",
  );
  await expect(summary).toContainText("1 feedback cycle(s) unsupported");
  await expect(summary.getByRole("listitem").first()).toContainText(
    "members controller, plant",
  );
  await expect(summary).toContainText(
    "needs an admitted timing/causality contract",
  );
  await projectWithSystem(page, "Explicit converter", "explicit-converter");
  await expect(
    page.getByRole("button", {
      name: /^Admission unsupported; show checks for .*#command-flow$/,
    }),
  ).toBeVisible();
  await page.getByLabel("Source endpoint").selectOption("controller-out");
  await page.getByLabel("Destination endpoint").selectOption("plant-in");
  await expect(page.locator("#target-guidance")).toContainText(
    "Interface declares explicit-converter; this connection will not be admitted for execution.",
  );
});
