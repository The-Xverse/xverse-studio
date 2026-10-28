import { test, expect, type Page, type Locator } from "@playwright/test";
import { connectStudio } from "./connect-studio";

async function keyboard(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 220; i++) {
    if (await target.evaluate((node) => node === document.activeElement)) break;
    await page.keyboard.press("Tab");
  }
  await expect(target).toBeFocused();
  await page.keyboard.press("Enter");
}

for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  test(`owned optional controls: keyboard Pause, reload, Resume and Stop at ${viewport.width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const project = await page.evaluate(async () => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      };
      const response = await fetch("/api/v1/projects", {
        method: "POST",
        headers,
        body: JSON.stringify({ name: "Owned optional controls" }),
      });
      if (response.status !== 201) throw Error("Project creation failed");
      const created = await response.json();
      const edited = await fetch(
        `/api/v1/projects/${created.projectId}/edits`,
        {
          method: "POST",
          headers: { ...headers, "If-Match": String(created.revision) },
          body: JSON.stringify({
            baseRevision: created.revision,
            edits: [
              { kind: "set_parameter", parameterId: "duration", value: 10 },
            ],
          }),
        },
      );
      if (edited.status !== 200) throw Error("Owned parameter setup failed");
      const result = await edited.json();
      localStorage.setItem("studio.projectId", result.projectId);
      return result;
    });
    await page.reload();
    await expect(
      page.getByRole("heading", { name: project.name, exact: true }),
    ).toBeVisible();
    await keyboard(
      page,
      page.getByRole("button", { name: "Preflight & run", exact: true }),
    );
    await keyboard(
      page,
      page
        .getByRole("dialog", { name: "Execution preflight" })
        .getByRole("button", { name: "Start frozen snapshot", exact: true }),
    );
    const controls = page.getByRole("region", {
      name: "Run controls",
      exact: true,
    });
    await expect(
      controls.getByRole("button", { name: "Pause", exact: true }),
    ).toBeEnabled();
    await expect(
      controls.getByRole("button", { name: "Resume", exact: true }),
    ).toBeDisabled();
    await expect(controls).toContainText("30 wall seconds");
    await keyboard(
      page,
      controls.getByRole("button", { name: "Pause", exact: true }),
    );
    await expect(
      controls.locator('[data-control-operation="completed"]'),
    ).toContainText("Pause request");
    const runs = (
      await (
        await page.request.get(`/api/v1/runs?projectId=${project.projectId}`)
      ).json()
    ).items;
    expect(runs).toHaveLength(1);
    const run = runs[0];
    expect(run.state).toBe("paused");
    const frozen = await (
      await page.request.get(`/api/v1/runs/${run.runId}/snapshot`)
    ).json();
    expect(frozen.integrity).toBe("valid");
    const observations = async () =>
      await (
        await page.request.get(`/api/v1/runs/${run.runId}/observations`)
      ).json();
    const before = await observations();
    await page.waitForTimeout(350);
    expect((await observations()).items).toEqual(before.items);
    const saved = await page.evaluate(
      (id) =>
        JSON.parse(
          localStorage.getItem("studio.pendingCommand." + id) || "null",
        ),
      run.runId,
    );
    expect(saved.kind).toBe("pause");
    expect(saved.status).toBe("completed");
    await page.reload();
    await keyboard(page, page.getByRole("tab", { name: /^Results/ }));
    await expect(
      controls.locator('[data-control-operation="completed"]'),
    ).toContainText("Pause request");
    await expect(
      controls.getByRole("button", { name: "Pause", exact: true }),
    ).toBeDisabled();
    await expect(
      controls.getByRole("button", { name: "Resume", exact: true }),
    ).toBeEnabled();
    await expect(page.locator(".run-identity")).toContainText(run.runId);
    await expect(page.locator(".run-identity")).toContainText(
      run.snapshotId.slice(0, 18),
    );
    const inputs = page.getByRole("button", {
      name: "Frozen inputs",
      exact: true,
    });
    await keyboard(page, inputs);
    const inputDialog = page.getByRole("dialog", {
      name: "Frozen run inputs · read-only",
      exact: true,
    });
    await expect(inputDialog).toContainText(run.snapshotId);
    await expect(inputDialog).toContainText(frozen.snapshot.planDigest);
    await expect(inputDialog).toContainText(frozen.snapshot.semanticDigest);
    await page.keyboard.press("Escape");
    await expect(inputDialog).toBeHidden();
    await expect(inputs).toBeFocused();
    await keyboard(
      page,
      controls.getByRole("button", { name: "Resume", exact: true }),
    );
    await expect(
      controls.locator('[data-control-operation="completed"]'),
    ).toContainText("Resume request");
    await expect
      .poll(async () => (await observations()).items.length)
      .toBeGreaterThan(before.items.length);
    await keyboard(
      page,
      controls.getByRole("button", { name: "Stop", exact: true }),
    );
    await expect(
      controls.locator('[data-control-operation="completed"]'),
    ).toContainText("Stop request");
    const ended = await (
      await page.request.get(`/api/v1/runs/${run.runId}`)
    ).json();
    expect(ended.state).toBe("stopped");
    expect(ended.cleanup).toBe("complete");
    expect(ended.evidence).toBe("complete");
    expect(ended.verdict).toBeNull();
    expect(ended.effectivePlanDigest).toBe(frozen.snapshot.planDigest);
    expect(ended.effectiveSemanticDigest).toBe(frozen.snapshot.semanticDigest);
    expect((await observations()).integrity).toBe("valid");
    expect(
      await (
        await page.request.get(`/api/v1/runs/${run.runId}/snapshot`)
      ).json(),
    ).toEqual(frozen);
    expect(
      await (
        await page.request.get(`/api/v1/projects/${project.projectId}`)
      ).json(),
    ).toEqual(project);
    expect(
      (
        await (
          await page.request.get(`/api/v1/runs?projectId=${project.projectId}`)
        ).json()
      ).items,
    ).toHaveLength(1);
    await info.attach("owned-optional-control-scope", {
      body: JSON.stringify({
        scope:
          "Actual owned native model and authenticated browser controls; no physical equipment",
        viewport,
        runId: run.runId,
        snapshotId: run.snapshotId,
        savedPauseOperation: saved.operationId,
        pausedSamples: before.items.length,
        finalState: ended.state,
      }),
      contentType: "application/json",
    });
  });
}
