import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "./connect-studio";

test("onboarding: a prepared example opens ready, an unresolved import stays inert and out-of-range parameters block admission", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  await page.evaluate(() => localStorage.removeItem("studio.projectId"));
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Start with an example", exact: true }),
  ).toBeVisible();
  // 1. Prepared example: the card states its scope and maturity; the guided path opens a ready, valid project.
  const card = page
    .locator(".example-grid")
    .getByRole("button", { name: /Automotive reference/ });
  await expect(card).toContainText("Guided example");
  await expect(card).toContainText("owned_reference");
  await expect(card).toContainText("fixture");
  await expect(page.locator(".scope-note")).toContainText(
    "do not establish external simulator or physical-device integration",
  );
  await card.click();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Automotive reference",
  );
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  await expect(
    page.getByText("Authoritative platform validation passed.", {
      exact: false,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Back to draft", exact: true })
    .click();
  // 2. The form refuses an out-of-range value before any request (usability only)...
  const edits: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST" && r.url().endsWith("/edits"))
      edits.push(r.url());
  });
  const exampleId = await page.evaluate(() =>
    localStorage.getItem("studio.projectId"),
  );
  const revisionOf = async (id: string | null) =>
    (await page.request.get(`/api/v1/projects/${id}`).then((r) => r.json()))
      .revision;
  const revisionBefore = await revisionOf(exampleId);
  await page.getByRole("button", { name: "plant plant", exact: true }).click();
  await page.getByRole("button", { name: "Parameters", exact: true }).click();
  await page.getByLabel("Duration").fill("31");
  await page
    .getByLabel("Duration")
    .locator("xpath=ancestor::form")
    .getByRole("button", { name: "Apply", exact: true })
    .click();
  await expect(page.getByLabel("Duration")).toHaveJSProperty(
    "validity.rangeOverflow",
    true,
  );
  expect(
    await page
      .getByLabel("Duration")
      .evaluate((input: HTMLInputElement) => input.validationMessage),
  ).not.toBe("");
  // Give a non-validating submit time to reach the network before asserting none did.
  await page.waitForTimeout(750);
  expect(edits).toEqual([]);
  expect(await revisionOf(exampleId)).toBe(revisionBefore);
  // ...while the backend enforces the bound at admission for a draft written elsewhere.
  const created = await page.evaluate(async () => {
    const projectId = localStorage.getItem("studio.projectId")!;
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const project = await fetch(`/api/v1/projects/${projectId}`).then((r) =>
      r.json(),
    );
    const r = await fetch(`/api/v1/projects/${projectId}/edits`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
        "If-Match": String(project.revision),
      },
      body: JSON.stringify({
        baseRevision: project.revision,
        edits: [{ kind: "set_parameter", parameterId: "duration", value: 31 }],
      }),
    });
    return r.status;
  });
  expect(created).toBe(200);
  await page.reload();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("region", { name: "Readiness diagnostics" }),
  ).toContainText("LIMIT_EXCEEDED");
  await page
    .getByRole("button", { name: "Back to draft", exact: true })
    .click();
  // 3. Import through the UI: unresolved content is preserved, inspectable and not executable.
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
  const imported = await page.request
    .get(`/api/v1/projects/${projectId}`)
    .then((r) => r.json());
  const system = (Object.values(imported.documents) as any[]).find((d) =>
    d.path.endsWith("/system.xdl.yaml"),
  ).content as string;
  expect(system).toContain("org.example.unresolved");
  expect(system).toContain("rm -rf /");
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("region", { name: "Readiness diagnostics" }),
  ).toContainText("XDL-SEMANTIC-PROFILE-MISSING");
  expect(
    (await page.request.get("/api/v1/runs").then((r) => r.json())).items.filter(
      (r: any) => r.projectId === projectId,
    ),
  ).toEqual([]);
  // 4. Recent projects reopen a saved draft from the workspace list.
  await page
    .getByRole("button", { name: "Back to draft", exact: true })
    .click();
  await page
    .locator(".breadcrumb")
    .getByRole("button", { name: "Workspace", exact: true })
    .click();
  await page
    .locator(".project-list .project-open")
    .filter({ hasText: "Automotive reference" })
    .first()
    .click();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Automotive reference",
  );
});
