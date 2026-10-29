import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "./connect-studio";

test("project journeys: scoped example claims, dependency review and unresolved-content inspection", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  await page.evaluate(() => localStorage.removeItem("studio.projectId"));
  await page.reload();
  // Example cards state what they do not demonstrate before anything is created.
  const card = page
    .locator(".example-grid")
    .getByRole("button", { name: /Process control reference/ });
  await expect(card.locator(".card-limit")).toContainText(
    "Scope limit: Owned executable reference only",
  );
  await card.click();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Process control reference",
  );
  const dependencies = page.getByRole("button", { name: /^Dependencies/ });
  await expect(dependencies).toHaveAccessibleName(
    "Dependencies: none unresolved",
  );
  await dependencies.click();
  let dialog = page.getByRole("dialog", {
    name: "Dependencies and unresolved content",
  });
  await expect(dialog).toContainText("Created from Process control reference");
  await expect(dialog).toContainText("Demonstrates: Normalized state");
  await expect(dialog).toContainText(
    "Scope limit: Owned executable reference only",
  );
  await expect(dialog).toContainText("Runs on provider studio.reference only.");
  await expect(dialog.getByRole("status")).toContainText(
    "Nothing here blocks execution",
  );
  await expect(dialog).toContainText(
    "Every extension namespace is declared by an admitted profile.",
  );
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  // An imported archive with an unresolved extension is flagged and inspectable in place.
  const archive = testInfo.outputPath("unknown-extension.zip");
  writeFileSync(
    archive,
    Buffer.from(
      execFileSync(
        path.resolve(
          process.platform === "win32"
            ? ".venv/Scripts/python.exe"
            : ".venv/bin/python",
        ),
        [
          "-I",
          "tests/fixtures/projects/create_catalog_archive.py",
          "--variant",
          "unknown-extension",
        ],
        { encoding: "utf8" },
      ).trim(),
      "base64",
    ),
  );
  await page
    .locator(".breadcrumb")
    .getByRole("button", { name: "Workspace", exact: true })
    .click();
  await page.getByLabel("Import project archive").setInputFiles(archive);
  await expect(page.locator(".project-header h1")).toHaveText(
    "Catalog fixture (unknown-extension)",
  );
  const projectId = await page.evaluate(() =>
    localStorage.getItem("studio.projectId"),
  );
  const before = await page.request
    .get(`/api/v1/projects/${projectId}`)
    .then((r) => r.json());
  await expect(dependencies).toHaveAccessibleName(
    "Dependencies: 1 unresolved item",
  );
  await dependencies.click();
  dialog = page.getByRole("dialog", {
    name: "Dependencies and unresolved content",
  });
  await expect(dialog).toContainText("Imported archive.");
  const item = dialog.locator(".inspection-unresolved li").first();
  await expect(item.locator(".badge").first()).toHaveText("unresolved");
  await expect(dialog.getByRole("status")).toContainText(
    "Execution is blocked by this content",
  );
  await expect(item).toContainText("org.example.unresolved");
  await expect(item).toContainText("/extensions/org.example.unresolved");
  await expect(
    dialog.getByLabel("Preserved content of org.example.unresolved"),
  ).toContainText("rm -rf /");
  await page.screenshot({ path: testInfo.outputPath("inspection.png") });
  // The source link opens the exact preserved document.
  await item.getByRole("button", { name: /system\.xdl\.yaml$/ }).click();
  const source = page.getByRole("dialog", { name: "Authored XDL source" });
  await expect(source).toBeVisible();
  // Focus moves into the source dialog, never stays behind it.
  await expect
    .poll(() =>
      page.evaluate(
        () =>
          document.activeElement
            ?.closest('[role="dialog"]')
            ?.getAttribute("aria-label") ?? null,
      ),
    )
    .toBe("Authored XDL source");
  await expect(source.locator("textarea")).toHaveValue(
    /org\.example\.unresolved/,
  );
  await page.keyboard.press("Escape");
  await expect(source).toHaveCount(0);
  // Focus returns to the header entry point rather than behind a closed dialog.
  await expect(dependencies).toBeFocused();
  // Inspection changed nothing and ran nothing.
  const after = await page.request
    .get(`/api/v1/projects/${projectId}`)
    .then((r) => r.json());
  expect(after.revision).toBe(before.revision);
  expect(after.documents).toEqual(before.documents);
  expect(
    (await page.request.get("/api/v1/runs").then((r) => r.json())).items.filter(
      (r: any) => r.projectId === projectId,
    ),
  ).toEqual([]);
});
