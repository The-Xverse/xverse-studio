import { test, expect, type Page, type TestInfo } from "@playwright/test";
import { connectStudio } from "./connect-studio";

async function get(page: Page, path: string) {
  const response = await page.request.get("/api/v1" + path);
  expect(response.ok()).toBe(true);
  return response.json();
}

async function post(page: Page, path: string, body: unknown, key: string) {
  const { csrfToken } = await get(page, "/session");
  return page.request.post("/api/v1" + path, {
    headers: {
      "X-CSRF-Token": csrfToken,
      "Idempotency-Key": key,
      Origin: new URL(page.url()).origin,
    },
    data: body,
  });
}

async function startPaused(page: Page, info: TestInfo) {
  await connectStudio(page, info);
  await page
    .getByRole("button", { name: "X-Verse Studio home", exact: true })
    .click();
  const example = page
    .locator(".example-grid")
    .getByRole("button", { name: /Live target reference/ });
  await example.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", { name: "Live target reference", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await page
    .getByRole("dialog", { name: "Execution preflight" })
    .getByRole("button", { name: "Start frozen snapshot", exact: true })
    .click();
  const controls = page.getByRole("region", {
    name: "Run controls",
    exact: true,
  });
  const pause = controls.getByRole("button", { name: "Pause", exact: true });
  await expect(pause).toBeEnabled();
  await pause.focus();
  await page.keyboard.press("Enter");
  await expect(
    controls.locator('[data-control-operation="completed"]'),
  ).toContainText("Pause request");
  const projectId = await page.evaluate(() =>
    localStorage.getItem("studio.projectId"),
  );
  const { items } = await get(page, `/runs?projectId=${projectId}`);
  expect(items).toHaveLength(1);
  expect(items[0].state).toBe("paused");
  const run = items[0];
  expect(run.capabilities).toContain("set_parameter");
  expect(run.liveValues).toEqual({ target: 1 });
  const frozen = await get(page, `/runs/${run.runId}/snapshot`);
  return { controls, run, frozen };
}

for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  test(`owned live target: lost acknowledgement and reload keep one mutation and frozen inputs at ${viewport.width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize(viewport);
    const { controls, run, frozen } = await startPaused(page, info);
    const target = controls.getByRole("region", {
      name: "Live model input",
      exact: true,
    });
    await expect(target).toContainText("Observed target: 1");
    const requests: { key: string | undefined; body: unknown }[] = [];
    let lost = false;
    await page.route(`**/api/v1/runs/${run.runId}/commands`, async (route) => {
      const request = route.request();
      if (request.postDataJSON().kind !== "set_parameter")
        return route.continue();
      requests.push({
        key: request.headers()["idempotency-key"],
        body: request.postDataJSON(),
      });
      if (!lost) {
        lost = true;
        const response = await route.fetch();
        expect(response.status()).toBe(202);
        await route.abort("connectionreset");
      } else await route.continue();
    });
    await target.getByLabel("Proposed live target").fill("2");
    await target
      .getByRole("button", { name: "Apply live target", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(
      controls.locator('[data-control-operation="unacknowledged"]'),
    ).toContainText("Requested target: 1 → 2");
    const stored = await page.evaluate(
      (id) => JSON.parse(localStorage.getItem("studio.pendingCommand." + id)!),
      run.runId,
    );
    expect(stored.parameters).toEqual({
      inputId: "target",
      expectedValue: 1,
      value: 2,
    });
    await expect
      .poll(
        async () => (await get(page, `/runs/${run.runId}`)).liveMutationCount,
      )
      .toBe(1);
    await page.reload();
    await page.getByRole("tab", { name: /^Results/ }).click();
    await expect(
      controls.locator('[data-control-operation="unacknowledged"]'),
    ).toContainText("Requested target: 1 → 2");
    await controls.getByRole("button", { name: /Retry same request/ }).click();
    await expect(
      controls.locator('[data-control-operation="completed"]'),
    ).toContainText("Live target request");
    expect(requests).toHaveLength(2);
    expect(requests[0]).toEqual(requests[1]);
    expect(requests[0].key).toBe(stored.key);
    await expect(target).toContainText("Observed target: 2");
    const receipt = await page.evaluate(
      (id) => JSON.parse(localStorage.getItem("studio.pendingCommand." + id)!),
      run.runId,
    );
    const operation = await get(page, `/operations/${receipt.operationId}`);
    expect(operation.result.mutation).toMatchObject({
      inputId: "target",
      oldValue: 1,
      newValue: 2,
      authority: {
        principal: "local-operator",
        scope: "native-backend-owned",
        physicalEffects: false,
      },
    });
    await controls.getByRole("button", { name: "Resume", exact: true }).click();
    await expect(
      controls.locator('[data-control-operation="completed"]'),
    ).toContainText("Resume request");
    await expect
      .poll(async () =>
        (
          await get(page, `/runs/${run.runId}/observations?field=target`)
        ).items.some((item: any) => item.values.target === 2),
      )
      .toBe(true);
    await controls.getByRole("button", { name: "Stop", exact: true }).click();
    await expect(
      controls.locator('[data-control-operation="completed"]'),
    ).toContainText("Stop request");
    const ended = await get(page, `/runs/${run.runId}`);
    expect(ended).toMatchObject({
      state: "stopped",
      liveMutationCount: 1,
      liveValues: { target: 2 },
      cleanup: "complete",
      evidence: "complete",
    });
    expect(await get(page, `/runs/${run.runId}/snapshot`)).toEqual(frozen);
    expect((await get(page, `/runs/${run.runId}/observations`)).integrity).toBe(
      "valid",
    );
    await info.attach("native-live-target-receipt", {
      contentType: "application/json",
      body: JSON.stringify({
        viewport,
        runId: run.runId,
        operationId: receipt.operationId,
        oneMutation: ended.liveMutationCount,
        exactRetry: requests[0].key === requests[1].key,
        snapshotUnchanged: true,
        scope: "Owned native reference only; no external runtime or equipment",
      }),
    });
  });

  test(`owned live target: a newer observed value preserves the proposal and requires review at ${viewport.width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize(viewport);
    const { controls, run, frozen } = await startPaused(page, info);
    const target = controls.getByRole("region", {
      name: "Live model input",
      exact: true,
    });
    const input = target.getByLabel("Proposed live target");
    await input.fill("101");
    await expect(
      target.getByRole("button", { name: "Apply live target", exact: true }),
    ).toBeDisabled();
    await input.fill("");
    await expect(
      target.getByRole("button", { name: "Apply live target", exact: true }),
    ).toBeDisabled();
    await input.fill("4");
    const response = await post(
      page,
      `/runs/${run.runId}/commands`,
      {
        kind: "set_parameter",
        expectedStateVersion: run.stateVersion,
        parameters: { inputId: "target", expectedValue: 1, value: 2 },
      },
      "second-operator-live",
    );
    expect(response.status()).toBe(202);
    await expect(target).toContainText("Observed target: 2");
    await expect(input).toHaveValue("4");
    const apply = target.getByRole("button", {
      name: "Apply live target",
      exact: true,
    });
    await expect(apply).toBeDisabled();
    const review = target.getByRole("button", {
      name: "Review latest target",
      exact: true,
    });
    await review.focus();
    await page.keyboard.press("Enter");
    await expect(input).toHaveValue("4");
    await expect(apply).toBeEnabled();
    await apply.click();
    await expect(
      controls.locator('[data-control-operation="completed"]'),
    ).toContainText("Requested target: 2 → 4");
    await expect(target).toContainText("Observed target: 4");
    // A later external change must not leave a historical completed receipt blocking new proposals.
    const current = await get(page, `/runs/${run.runId}`);
    const later = await post(
      page,
      `/runs/${run.runId}/commands`,
      {
        kind: "set_parameter",
        expectedStateVersion: current.stateVersion,
        parameters: { inputId: "target", expectedValue: 4, value: 3 },
      },
      "later-operator-live",
    );
    expect(later.status()).toBe(202);
    await expect(target).toContainText("Observed target: 3");
    await expect(input).toBeEnabled();
    await input.fill("5");
    await expect(apply).toBeEnabled();
    await controls.getByRole("button", { name: "Cancel", exact: true }).click();
    await expect(
      controls.locator('[data-control-operation="completed"]'),
    ).toContainText("Cancel request");
    const ended = await get(page, `/runs/${run.runId}`);
    expect(ended.liveMutationCount).toBe(3);
    expect(ended.liveValues).toEqual({ target: 3 });
    expect(await get(page, `/runs/${run.runId}/snapshot`)).toEqual(frozen);
  });
}
