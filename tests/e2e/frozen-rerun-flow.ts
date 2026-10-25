import { expect, type Page, type TestInfo } from "@playwright/test";
export async function exerciseFrozenRerun(page: Page, testInfo: TestInfo) {
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  const original = await page.evaluate(async () => {
    const id = localStorage.getItem("studio.lastRun");
    const [run, input] = await Promise.all([
      fetch("/api/v1/runs/" + id).then((response) => response.json()),
      fetch("/api/v1/runs/" + id + "/snapshot").then((response) =>
        response.json(),
      ),
    ]);
    return { run, input };
  });
  expect(original.input.integrity).toBe("valid");
  expect(original.input.readOnly).toBe(true);
  await page
    .getByRole("button", { name: "Frozen inputs", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Frozen run inputs · read-only",
      exact: true,
    }),
  ).toBeVisible();
  const document = await page
    .getByLabel("Frozen document", { exact: true })
    .inputValue();
  await expect(
    page.getByLabel("Frozen source text (read-only)", { exact: true }),
  ).toHaveValue(original.input.snapshot.documents[document]);
  expect(
    await page
      .getByLabel("Frozen source text (read-only)", { exact: true })
      .evaluate((element: HTMLTextAreaElement) => element.readOnly),
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("frozen-inputs.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Close dialog", exact: true }).click();
  await page.getByRole("tab", { name: "Model", exact: true }).click();
  await page.getByRole("button", { name: "Parameters", exact: true }).click();
  const target = page.getByLabel("Target", { exact: false });
  await target.fill("0.5");
  await target
    .locator("xpath=ancestor::form")
    .getByRole("button", { name: "Apply", exact: true })
    .click();
  await expect(
    page.getByText("Draft saved. Existing run snapshots remain unchanged.", {
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  await expect(
    page.getByRole("button", { name: "Rerun frozen inputs", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Rerun frozen inputs", exact: true })
    .click();
  await expect
    .poll(async () =>
      page.evaluate(() => localStorage.getItem("studio.lastRun")),
    )
    .not.toBe(original.run.runId);
  await expect(page.getByText("stopped", { exact: true }).first()).toBeVisible({
    timeout: 15000,
  });
  const result = await page.evaluate(async (originalRunId) => {
    const id = localStorage.getItem("studio.lastRun");
    const [created, inputs, previous] = await Promise.all([
      fetch("/api/v1/runs/" + id).then((response) => response.json()),
      fetch("/api/v1/runs/" + id + "/snapshot").then((response) =>
        response.json(),
      ),
      fetch("/api/v1/runs/" + originalRunId + "/snapshot").then((response) =>
        response.json(),
      ),
    ]);
    return { created, inputs, previous };
  }, original.run.runId);
  expect(result.created.runId).not.toBe(original.run.runId);
  expect(result.created.snapshotId).not.toBe(original.run.snapshotId);
  expect(result.inputs.snapshot.parentSnapshotId).toBe(original.run.snapshotId);
  expect(result.inputs.snapshot.sourceRunId).toBe(original.run.runId);
  expect(result.inputs.snapshot.configuration).toEqual(
    original.input.snapshot.configuration,
  );
  expect(result.inputs.snapshot.configuration.target).not.toBe(0.5);
  expect(result.inputs.snapshot.planDigest).toBe(
    original.input.snapshot.planDigest,
  );
  expect(result.created.effectivePlanDigest).toBe(result.created.planDigest);
  expect(result.previous.snapshot).toEqual(original.input.snapshot);
  await page.screenshot({
    path: testInfo.outputPath("frozen-rerun.png"),
    fullPage: true,
  });
}
