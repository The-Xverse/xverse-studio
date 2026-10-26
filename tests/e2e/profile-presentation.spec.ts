import { test, expect, type Page } from "@playwright/test";
import { connectStudio } from "./connect-studio";

async function fromBlueprint(page: Page, blueprintRef: string, name: string) {
  await page.evaluate(
    async ({ blueprintRef, name }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const project = await fetch("/api/v1/projects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({ name, blueprintRef }),
      }).then((r) => r.json());
      localStorage.setItem("studio.projectId", project.projectId);
    },
    { blueprintRef, name },
  );
  await page.reload();
}

test("profile presentation: domain terms relabel shared workflows as inert text", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  await fromBlueprint(page, "reference-automotive", "Vehicle terms");
  const header = page.locator(".project-header");
  await expect(header.locator(".domain-badge")).toContainText(
    "Automotive terms",
  );
  // The same parameters, arranged by the domain's form groups.
  await page.getByRole("button", { name: "plant plant", exact: true }).click();
  await page.getByRole("button", { name: "Parameters", exact: true }).click();
  const groups = page.locator(".parameter-group legend");
  await expect(groups).toHaveText([
    "Reference and response",
    "Drive horizon",
    "Sensor faults",
  ]);
  await expect(page.getByLabel("Duration")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Vehicle function explorer" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Deployment", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Vehicle deployment variants" }),
  ).toBeVisible();
  await fromBlueprint(page, "reference-process-control", "Process terms");
  await expect(header.locator(".domain-badge")).toContainText(
    "Process control terms",
  );
  // The profile's allowlisted icons mark the header and the matching workflow tabs.
  await expect(header.locator(".system-icon svg")).toHaveAttribute(
    "data-icon",
    "settings",
  );
  await expect(
    page.getByRole("tab", { name: /Experiments/ }).locator("svg"),
  ).toHaveAttribute("data-icon", "experiment");
  await expect(
    page.getByRole("heading", { name: "Process explorer" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Author operating scenario intent" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: /Connections/ }).click();
  await expect(page.locator(".view-page").first()).toContainText(
    "Inspect declared signal flows",
  );
  // Each definition keeps its own domain label in the instance wizard.
  await page.getByRole("tab", { name: /Model/ }).click();
  await page.getByRole("button", { name: "Add element", exact: true }).click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("radio", {
        name: /reference-plant org\.xverse\.studio\.process-control/,
      })
      .locator("xpath=ancestor::label"),
  ).toContainText("Process control");
  await page.keyboard.press("Escape");
  // Domain profiles show their terminology as text and never fetch documentation.
  await page
    .getByRole("button", { name: "Compatibility and environment" })
    .click();
  const automotive = page
    .locator("article")
    .filter({ hasText: "Automotive terminology" });
  await expect(automotive).toContainText("Element → ECU");
  await expect(automotive).toContainText(
    "Documentation reference (not fetched): urn:xverse:studio:domain:automotive:1.0",
  );
  await expect(automotive.locator("a")).toHaveCount(0);
});
