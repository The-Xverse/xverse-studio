import { test, expect } from "@playwright/test";
import { connectStudio } from "./connect-studio";
test("source drafts: preserve empty recovery and atomically bind rapid resource switches to their own text", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  await page.getByRole("button", { name: "New project", exact: true }).click();
  await page
    .getByLabel("Project name", { exact: true })
    .fill("Source draft isolation");
  await page
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Source draft isolation",
  );
  const original = await page.evaluate(async () =>
    fetch("/api/v1/projects/" + localStorage.getItem("studio.projectId")).then(
      (r) => r.json(),
    ),
  );
  await page.getByRole("button", { name: "XDL source", exact: true }).click();
  const resource = page.getByLabel("Resource", { exact: true }),
    source = page.getByLabel("XDL source", { exact: true }),
    save = page.getByRole("button", {
      name: "Save source revision",
      exact: true,
    });
  const firstId = await resource.inputValue(),
    secondId = Object.keys(original.documents).find((id) => id !== firstId)!;
  await expect(source).toHaveValue(original.documents[firstId].content);
  await expect(save).toBeDisabled();
  await source.fill("");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "XDL source", exact: true }).click();
  await expect(resource).toHaveValue(firstId);
  await expect(source).toHaveValue("");
  await expect(
    page.getByText(
      "Recovered an uncommitted draft from this browser tab. Review it before saving.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(save).toBeEnabled();
  const writes: { url: string; body: any }[] = [];
  page.on("request", (r) => {
    if (r.method() === "PUT" && r.url().includes("/documents/"))
      writes.push({ url: r.url(), body: r.postDataJSON() });
  });
  await page.evaluate((id) => {
    const select = document.querySelector<HTMLSelectElement>(
      'select[aria-label="Resource"]',
    )!;
    select.value = id;
    select.dispatchEvent(new Event("change", { bubbles: true }));
    Array.from(document.querySelectorAll<HTMLButtonElement>("button"))
      .find((button) => button.textContent?.includes("Save source revision"))!
      .click();
  }, secondId);
  await expect(resource).toHaveValue(secondId);
  await expect(source).toHaveValue(original.documents[secondId].content);
  await expect(save).toBeDisabled();
  expect(writes).toEqual([]);
  await resource.selectOption(firstId);
  await expect(source).toHaveValue("");
  const edited =
    original.documents[firstId].content + "\n# selected-document-only\n";
  await source.fill(edited);
  await page.evaluate((id) => {
    const select = document.querySelector<HTMLSelectElement>(
      'select[aria-label="Resource"]',
    )!;
    select.value = id;
    select.dispatchEvent(new Event("change", { bubbles: true }));
    Array.from(document.querySelectorAll<HTMLButtonElement>("button"))
      .find((button) => button.textContent?.includes("Save source revision"))!
      .click();
  }, secondId);
  await expect(source).toHaveValue(original.documents[secondId].content);
  expect(writes).toEqual([]);
  const untouched = await page.evaluate(
    async (id) => fetch("/api/v1/projects/" + id).then((r) => r.json()),
    original.projectId,
  );
  expect(untouched.documents).toEqual(original.documents);
  expect(untouched.revision).toBe(original.revision);
  await resource.selectOption(firstId);
  await expect(source).toHaveValue(edited);
  await save.click();
  await expect(
    page.getByText("Source revision saved. Validate it before running.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(save).toBeDisabled();
  expect(writes).toHaveLength(1);
  expect(writes[0].url).toContain("/documents/" + firstId);
  expect(writes[0].body.content).toBe(edited);
  const saved = await page.evaluate(
    async (id) => fetch("/api/v1/projects/" + id).then((r) => r.json()),
    original.projectId,
  );
  expect(saved.documents[firstId].content).toBe(edited);
  for (const id of Object.keys(original.documents)) {
    if (id !== firstId)
      expect(saved.documents[id]).toEqual(original.documents[id]);
  }
  await page.screenshot({
    path: testInfo.outputPath("source-document-isolation.png"),
    fullPage: true,
  });
  await page.keyboard.press("Escape");
  await testInfo.attach("source-draft-isolation", {
    body: JSON.stringify(
      {
        projectId: original.projectId,
        firstId,
        secondId,
        attemptedRapidSwitches: 2,
        actualWrites: writes.length,
        beforeRevision: original.revision,
        afterRevision: saved.revision,
      },
      null,
      2,
    ),
    contentType: "application/json",
  });
});
