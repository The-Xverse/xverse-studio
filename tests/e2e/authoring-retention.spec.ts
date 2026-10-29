import { test, expect } from "@playwright/test";
import { connectStudio } from "./connect-studio";
import { exerciseNeutralAssets } from "./neutral-assets-flow";
import { exerciseRetention } from "./retention-flow";
test("neutral logical assets: keyboard author, inspect, source anchor and reload without execution", async ({
  page,
}, testInfo) => {
  test.setTimeout(120000);
  await connectStudio(page, testInfo);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await exerciseNeutralAssets(page, testInfo);
  expect(errors).toEqual([]);
});
test("explicit retention: protected project, disposable project and artifact metadata-only deletion", async ({
  page,
}, testInfo) => {
  test.setTimeout(120000);
  await connectStudio(page, testInfo);
  await page
    .locator(".example-grid")
    .getByRole("button", { name: /Process control reference/ })
    .click();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Process control reference",
  );
  const project = await page.evaluate(async () => {
    const id = localStorage.getItem("studio.projectId");
    const p = await fetch("/api/v1/projects/" + id).then((r) => r.json());
    return { projectId: p.projectId, name: p.name };
  });
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Back to draft", exact: true })
    .click();
  await page.getByRole("button", { name: "Catalog", exact: true }).click();
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
    .fill("urn:example:browser-artifact:1");
  await page
    .getByRole("button", { name: "Register metadata only", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("button", { name: "X-Verse Studio home", exact: true })
    .click();
  await page.getByRole("button", { name: "New project", exact: true }).click();
  await page
    .getByLabel("Project name", { exact: true })
    .fill("Retention disposable project");
  await page
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Retention disposable project",
      exact: true,
    }),
  ).toBeVisible();
  const candidateId = await page.evaluate(() =>
    localStorage.getItem("studio.projectId"),
  );
  await exerciseRetention(page, testInfo, project, candidateId!);
});
