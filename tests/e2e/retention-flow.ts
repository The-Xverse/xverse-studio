import { expect, type Page, type TestInfo } from "@playwright/test";
export async function exerciseRetention(
  page: Page,
  testInfo: TestInfo,
  protectedProject: { projectId: string; name: string },
  candidateId: string,
  candidateName = "Retention disposable project",
) {
  await page
    .getByRole("button", { name: "X-Verse Studio home", exact: true })
    .click();
  await page
    .getByRole("button", {
      name: `Review retention for project ${protectedProject.name}`,
      exact: true,
    })
    .focus();
  await page.keyboard.press("Enter");
  await page
    .getByRole("button", { name: "Preview removal dependencies", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await expect(
    page
      .locator(".retention-protected")
      .getByText("SNAPSHOT_DEPENDS_ON_PROJECT", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("table", {
      name: "Retention dependency reasons",
      exact: true,
    }),
  ).toContainText(protectedProject.projectId);
  await expect(
    page.getByRole("button", {
      name: "Apply deletion of 0 eligible selection(s)",
      exact: true,
    }),
  ).toBeDisabled();
  await page.screenshot({
    path: testInfo.outputPath("retention-protected-project.png"),
    fullPage: true,
  });
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("heading", { name: "Recent projects", exact: true }),
  ).toBeFocused();
  await page
    .getByRole("button", {
      name: `Review retention for project ${candidateName}`,
      exact: true,
    })
    .focus();
  await page.keyboard.press("Enter");
  await page
    .getByRole("button", { name: "Preview removal dependencies", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("table", {
      name: "Eligible retention removals",
      exact: true,
    }),
  ).toContainText(candidateId);
  const before = await page.evaluate(
    async (id) => ({
      candidate: (await fetch("/api/v1/projects/" + id)).status,
      runs: (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
    }),
    candidateId,
  );
  expect(before.candidate).toBe(200);
  await page
    .getByRole("button", {
      name: "Apply deletion of 1 eligible selection(s)",
      exact: true,
    })
    .focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("region", { name: "Retention apply outcome", exact: true }),
  ).toContainText("removed");
  await page
    .getByRole("button", { name: "Close retention review", exact: true })
    .click();
  await expect(
    page.getByRole("button", {
      name: `Review retention for project ${candidateName}`,
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Recent projects", exact: true }),
  ).toBeFocused();
  const persisted = await page.evaluate(
    async (ids) => ({
      candidate: (await fetch("/api/v1/projects/" + ids.candidateId)).status,
      protected: (await fetch("/api/v1/projects/" + ids.protectedId)).status,
    }),
    { candidateId, protectedId: protectedProject.projectId },
  );
  expect(persisted).toEqual({ candidate: 404, protected: 200 });
  await page.getByRole("button", { name: "Catalog", exact: true }).click();
  await page
    .getByLabel("Catalog kind", { exact: true })
    .selectOption("artifact");
  const entry = await page.evaluate(async () =>
    (
      await fetch("/api/v1/catalog?kind=artifact").then((r) => r.json())
    ).items.find((e: any) => e.name === "Browser metadata reference"),
  );
  expect(entry.entryId).toBeTruthy();
  await page
    .getByRole("button", {
      name: "Review retention for artifact Browser metadata reference",
      exact: true,
    })
    .click();
  await page
    .getByRole("button", { name: "Preview removal dependencies", exact: true })
    .click();
  await expect(
    page.getByRole("table", {
      name: "Eligible retention removals",
      exact: true,
    }),
  ).toContainText("catalog_registration_metadata_only");
  await expect(
    page.getByRole("table", {
      name: "Eligible retention removals",
      exact: true,
    }),
  ).toContainText(entry.entryId);
  await page
    .getByRole("button", {
      name: "Apply deletion of 1 eligible selection(s)",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("region", { name: "Retention apply outcome", exact: true }),
  ).toContainText("removed");
  await page.screenshot({
    path: testInfo.outputPath("retention-artifact-metadata-only.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Close retention review", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Browser metadata reference",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Catalog", exact: true }),
  ).toBeFocused();
  const after = await page.evaluate(async () => ({
    entries: (
      await fetch("/api/v1/catalog?kind=artifact").then((r) => r.json())
    ).items,
    runs: (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
  }));
  expect(after.entries.some((e: any) => e.entryId === entry.entryId)).toBe(
    false,
  );
  expect(after.runs).toBe(before.runs);
  await page
    .getByRole("button", { name: "X-Verse Studio home", exact: true })
    .click();
  await testInfo.attach("retention-resources", {
    body: JSON.stringify(
      {
        protectedProject,
        candidateId,
        artifactId: entry.entryId,
        outcome: persisted,
      },
      null,
      2,
    ),
    contentType: "application/json",
  });
}
