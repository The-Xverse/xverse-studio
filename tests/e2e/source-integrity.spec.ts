import { test, expect } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "./connect-studio";
test("external source inspection: modified bytes remain readable with warning, blocked save and no execution", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  await page.getByRole("button", { name: "New project", exact: true }).click();
  await page
    .getByLabel("Project name", { exact: true })
    .fill("Owned external source inspection");
  await page
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Owned external source inspection",
  );
  const original = await page.evaluate(async () =>
    fetch("/api/v1/projects/" + localStorage.getItem("studio.projectId")).then(
      (r) => r.json(),
    ),
  );
  expect(original.sourceIntegrity).toBe("intact");
  const docId = Object.keys(original.documents)[0],
    document = original.documents[docId],
    data = process.env.STUDIO_BROWSER_DATA!;
  expect(data).toBeTruthy();
  const file = path.resolve(
    data,
    "projects",
    original.projectId,
    "revisions",
    String(original.revision),
    document.path,
  );
  expect(file.startsWith(path.resolve(data) + path.sep)).toBe(true);
  expect(readFileSync(file, "utf8")).toBe(document.content);
  const modified =
    document.content + "\n# owned external-byte inspection fixture\n";
  writeFileSync(file, modified, "utf8");
  try {
    const runsBefore = await page.evaluate(
      async () =>
        (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
    );
    await page.reload();
    await expect(
      page.getByText("Source files changed outside Studio", { exact: true }),
    ).toBeVisible();
    await expect(page.locator(".workspace-footer")).toContainText(
      "External source changes",
    );
    const inspected = await page.evaluate(async (id) => {
      const response = await fetch("/api/v1/projects/" + id);
      return { status: response.status, body: await response.json() };
    }, original.projectId);
    expect(inspected.status).toBe(200);
    expect(inspected.body.sourceIntegrity).toBe("modified");
    expect(inspected.body.documents[docId].content).toBe(modified);
    expect(inspected.body.sourceDiagnostics[0].code).toBe("REVISION_CONFLICT");
    await page.getByRole("button", { name: "XDL source", exact: true }).click();
    await page.getByLabel("Resource", { exact: true }).selectOption(docId);
    const source = page.getByLabel("XDL source", { exact: true });
    await expect(source).toHaveValue(modified);
    await expect(
      page
        .locator(".source-toolbar")
        .getByText("Inspected external bytes", { exact: true }),
    ).toBeVisible();
    const writes: string[] = [];
    page.on("request", (r) => {
      if (r.method() === "PUT" && r.url().includes("/documents/"))
        writes.push(r.url());
    });
    await source.fill(modified + "# local draft remains inspectable\n");
    await expect(
      page.getByRole("button", { name: "Save source revision", exact: true }),
    ).toBeDisabled();
    await source.press("Control+s");
    expect(writes).toEqual([]);
    await page
      .getByRole("button", { name: "Compare changes", exact: true })
      .click();
    await expect(page.locator(".source-baseline")).toHaveText(modified);
    await expect(
      page
        .locator(".source-panels")
        .getByText("Inspected external bytes", { exact: true }),
    ).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath("external-source-inspection.png"),
      fullPage: true,
    });
    await page.keyboard.press("Escape");
    const blocked = page.waitForResponse(
      (r) => r.url().endsWith("/preflights") && r.request().method() === "POST",
    );
    await page
      .getByRole("button", { name: "Preflight & run", exact: true })
      .click();
    expect((await blocked).status()).toBe(412);
    expect(
      await page.evaluate(
        async () =>
          (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
      ),
    ).toBe(runsBefore);
    expect(readFileSync(file, "utf8")).toBe(modified);
    expect(writes).toEqual([]);
    await testInfo.attach("external-source-inspection", {
      body: JSON.stringify(
        {
          projectId: original.projectId,
          docId,
          path: document.path,
          readStatus: inspected.status,
          sourceIntegrity: inspected.body.sourceIntegrity,
          diagnostics: inspected.body.sourceDiagnostics,
          preflightStatus: 412,
          writes: writes.length,
        },
        null,
        2,
      ),
      contentType: "application/json",
    });
  } finally {
    // Restore only this owned fixture's original bytes so independent tests are not contaminated.
    writeFileSync(file, document.content, "utf8");
  }
});
