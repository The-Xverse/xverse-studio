import { test, expect } from "@playwright/test";
import { parse, stringify } from "yaml";
import { connectStudio } from "./connect-studio";
import { traceApi } from "./trace-claims-flow";
test("annotation run context: rerun resets prior edits and ignores a delayed prior save refresh", async ({
  page,
}, testInfo) => {
  test.setTimeout(120000);
  await connectStudio(page, testInfo);
  await page.getByRole("button", { name: "New project", exact: true }).click();
  await page
    .getByLabel("Project name", { exact: true })
    .fill("Annotation context reference");
  await page
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Annotation context reference",
  );
  const pid = await page.evaluate(() =>
    localStorage.getItem("studio.projectId"),
  );
  const project = (await traceApi(page, "/projects/" + pid)).body;
  const [did, document] = Object.entries(project.documents).find(
    ([, value]: any) => parse(value.content).kind === "Scenario",
  )! as [string, any];
  const scenario = parse(document.content);
  scenario.extensions["io.xverse.experiment"].parameters.find(
    (p: any) => p.id === "duration",
  ).value = 0.2;
  scenario.extensions[
    "io.xverse.studio.experiments"
  ].definitions[0].window.endTick = "200000";
  expect(
    (
      await traceApi(
        page,
        `/projects/${pid}/documents/${did}`,
        "PUT",
        { content: stringify(scenario), format: "yaml" },
        project.revision,
      )
    ).status,
  ).toBe(200);
  await page.reload();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Start frozen snapshot", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /Run results/ }),
  ).toBeVisible();
  await expect(page.getByText("stopped", { exact: true }).first()).toBeVisible({
    timeout: 20000,
  });
  const firstRun = (await page.evaluate(() =>
    localStorage.getItem("studio.lastRun"),
  ))!;
  await page.getByRole("tab", { name: "Annotations", exact: true }).click();
  await page
    .getByRole("textbox", { name: "Comment", exact: true })
    .fill("Prior run review note");
  await page
    .getByRole("button", { name: "Save separate annotation", exact: true })
    .click();
  const prior = (await traceApi(page, `/runs/${firstRun}/annotations`)).body
    .items[0];
  await page
    .getByRole("article")
    .filter({ hasText: "Prior run review note" })
    .getByRole("button", { name: "Edit note", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Add external reference", exact: true })
    .click();
  await page
    .getByLabel("Requirement or test URI", { exact: true })
    .fill("urn:requirements:old-unsaved-context");
  async function rerun(old: string) {
    await page
      .getByRole("button", { name: "Rerun frozen inputs", exact: true })
      .click();
    await expect
      .poll(() => page.evaluate(() => localStorage.getItem("studio.lastRun")))
      .not.toBe(old);
    const id = (await page.evaluate(() =>
      localStorage.getItem("studio.lastRun"),
    ))!;
    await expect
      .poll(async () => (await traceApi(page, "/runs/" + id)).body.state)
      .toBe("stopped");
    return id;
  }
  const secondRun = await rerun(firstRun);
  await expect(page.getByRole("textbox", { name: "Comment", exact: true })).toHaveValue("");
  await expect(
    page.getByRole("heading", { name: "Add a review note", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Save annotation revision", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByLabel("Requirement or test URI", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Add external reference", exact: true }),
  ).toBeVisible();
  expect(
    (await traceApi(page, `/runs/${firstRun}/annotations`)).body.items,
  ).toEqual([prior]);
  expect(
    (await traceApi(page, `/runs/${secondRun}/annotations`)).body.items,
  ).toEqual([]);

  await page.getByRole("textbox", { name: "Comment", exact: true }).fill("Second run note");
  await page
    .getByRole("button", { name: "Save separate annotation", exact: true })
    .click();
  await expect(
    page.getByRole("article").filter({ hasText: "Second run note" }),
  ).toBeVisible();
  const second = (await traceApi(page, `/runs/${secondRun}/annotations`)).body
    .items[0];
  await page
    .getByRole("article")
    .filter({ hasText: "Second run note" })
    .getByRole("button", { name: "Edit note", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Comment", exact: true })
    .fill("Intentionally saved on second run");
  await testInfo.attach("review-note-label-diagnostic", {
    body: JSON.stringify(await page.getByRole("textbox", { name: "Comment", exact: true }).evaluate((element: HTMLTextAreaElement) => ({ labelTexts: [...(element.labels || [])].map((label) => label.textContent), value: element.value }))),
    contentType: "application/json",
  });
  let release!: () => void, entered!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const intercepted = new Promise<void>((resolve) => {
    entered = resolve;
  });
  await page.route(`**/api/v1/runs/${secondRun}/annotations`, async (route) => {
    if (route.request().method() !== "GET") return route.continue();
    const response = await route.fetch();
    entered();
    await gate;
    await route.fulfill({ response });
  });
  await page
    .getByRole("button", { name: "Save annotation revision", exact: true })
    .click();
  await intercepted;
  const thirdRun = await rerun(secondRun);
  await expect(page.getByRole("textbox", { name: "Comment", exact: true })).toHaveValue("");
  await page
    .getByRole("textbox", { name: "Comment", exact: true })
    .fill("New run unsaved note remains here");
  const flushed = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/runs/${secondRun}/annotations`) &&
      response.request().method() === "GET",
  );
  release();
  await flushed;
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  );
  await expect(page.getByRole("textbox", { name: "Comment", exact: true })).toHaveValue(
    "New run unsaved note remains here",
  );
  await expect(
    page
      .getByRole("article")
      .filter({ hasText: "Intentionally saved on second run" }),
  ).toHaveCount(0);
  await page.unroute(`**/api/v1/runs/${secondRun}/annotations`);
  expect(
    (await traceApi(page, `/runs/${secondRun}/annotations`)).body.items[0],
  ).toMatchObject({
    annotationId: second.annotationId,
    revision: 2,
    text: "Intentionally saved on second run",
  });
  expect(
    (await traceApi(page, `/runs/${thirdRun}/annotations`)).body.items,
  ).toEqual([]);
  expect(
    (await traceApi(page, `/runs/${firstRun}/annotations`)).body.items,
  ).toEqual([prior]);
  await page.screenshot({
    path: testInfo.outputPath("annotation-context-new-run.png"),
    fullPage: true,
  });
});
