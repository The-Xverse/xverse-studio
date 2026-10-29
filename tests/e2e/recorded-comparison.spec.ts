import { test, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "./connect-studio";

async function request(
  page: Page,
  endpoint: string,
  method = "GET",
  body?: any,
  revision?: number,
) {
  return page.evaluate(
    async ({ endpoint, method, body, revision }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const response = await fetch("/api/v1" + endpoint, {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
          ...(revision === undefined ? {} : { "If-Match": String(revision) }),
          ...(method === "POST"
            ? { "Idempotency-Key": crypto.randomUUID() }
            : {}),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
      const value = await response.json();
      if (!response.ok)
        throw new Error(
          `Owned comparison setup ${response.status} ${value.code}`,
        );
      return value;
    },
    { endpoint, method, body, revision },
  );
}
async function setup(page: Page, width: number) {
  let project = await request(page, "/projects", "POST", {
    name: `Recorded comparison ${width}`,
    blueprintRef: "reference-process-control",
  });
  const runs: any[] = [];
  for (const [gain, duration] of [
    [0.5, 0.6],
    [0.8, 0.6],
    [0.8, 0.9],
  ]) {
    project = await request(
      page,
      `/projects/${project.projectId}/edits`,
      "POST",
      {
        baseRevision: project.revision,
        edits: [
          { kind: "set_parameter", parameterId: "gain", value: gain },
          { kind: "set_parameter", parameterId: "duration", value: duration },
        ],
      },
      project.revision,
    );
    const pf = await request(
      page,
      `/projects/${project.projectId}/preflights`,
      "POST",
      { revision: project.revision },
    );
    expect(pf.status).toBe("ready");
    const accepted = await request(page, "/runs", "POST", {
      snapshotId: pf.snapshotId,
      preflightId: pf.preflightId,
    });
    await expect
      .poll(
        async () => (await request(page, "/runs/" + accepted.runId)).state,
        { timeout: 20000 },
      )
      .toBe("stopped");
    const run = await request(page, "/runs/" + accepted.runId);
    expect(run.evidence).toBe("complete");
    expect(run.cleanup).toBe("complete");
    runs.push(run);
  }
  await page.evaluate(
    ({ project, run }) => {
      localStorage.setItem("studio.projectId", project.projectId);
      localStorage.setItem("studio.lastRun", run.runId);
      localStorage.setItem("studio.lastRun." + project.projectId, run.runId);
    },
    { project, run: runs[1] },
  );
  await page.reload();
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  await expect(page.getByLabel("Recorded run", { exact: true })).toHaveValue(
    runs[1].runId,
  );
  await page.getByRole("tab", { name: "Compare", exact: true }).click();
  return { project, runs };
}
const report = (page: Page) =>
  page.getByRole("region", { name: "Recorded comparison report", exact: true });
for (const width of [1024, 1440]) {
  test(`recorded comparison: immutable provenance, unequal windows and playback admission at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const { project, runs } = await setup(page, width);
    const baseline = page.getByLabel("Baseline run", { exact: true });
    await baseline.selectOption(runs[0].runId);
    const writes: string[] = [];
    page.on("request", (r) => {
      if (r.method() !== "GET" && r.url().includes("/api/v1/"))
        writes.push(new URL(r.url()).pathname);
    });
    await page
      .getByRole("button", { name: "Inspect compatibility", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Comparison report", exact: true }),
    ).toBeVisible();
    await expect(report(page)).toContainText("Compatible recorded windows");
    await expect(report(page)).toContainText(runs[0].snapshotId);
    await expect(report(page)).toContainText(runs[1].snapshotId);
    const parameters = report(page)
      .getByRole("table", { name: "Frozen configuration differences" })
      .getByRole("row", { name: /^Parameters/ });
    await expect(parameters).toContainText("different");
    await expect(parameters).toContainText("0.5");
    await expect(parameters).toContainText("0.8");
    await expect(
      report(page).getByRole("table", { name: "Recorded field results" }),
    ).toContainText("600000");
    await baseline.selectOption(runs[2].runId);
    await expect(report(page)).toHaveCount(0);
    await page
      .getByRole("button", { name: "Inspect compatibility", exact: true })
      .click();
    await expect(report(page)).toContainText("Pairing blocked");
    await expect(report(page)).toContainText("OBSERVATION_WINDOW_INCOMPATIBLE");
    await expect(report(page)).toContainText("900000");
    expect(writes).toEqual(["/api/v1/comparisons", "/api/v1/comparisons"]);
    await page.screenshot({
      path: info.outputPath("recorded-comparison.png"),
      fullPage: true,
    });
    expect(await request(page, "/projects/" + project.projectId)).toEqual(
      project,
    );
    await page
      .getByRole("button", { name: "Open recorded playback", exact: true })
      .click();
    await expect(
      page.getByRole("tab", { name: "Observations", exact: true }),
    ).toHaveAttribute("aria-selected", "true");
    const playback = page.getByRole("button", {
      name: "Replay observations",
      exact: true,
    });
    await expect(playback).toBeEnabled();
    await playback.click();
    expect(writes).toEqual(["/api/v1/comparisons", "/api/v1/comparisons"]);
    await expect(page.getByLabel("Recorded run", { exact: true })).toHaveValue(
      runs[1].runId,
    );
    await page.getByRole("tab", { name: "Compare", exact: true }).click();
    const pfResponse = page.waitForResponse(
      (r) =>
        r.request().method() === "POST" &&
        r.url().endsWith(`/projects/${project.projectId}/preflights`),
    );
    await page
      .getByRole("button", { name: "Preflight a new run", exact: true })
      .click();
    const pf = await (await pfResponse).json();
    expect(pf.status).toBe("ready");
    expect(pf.snapshotId).not.toBe(runs[1].snapshotId);
    await expect(
      page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
    ).toBeEnabled();
    const root = process.env.STUDIO_BROWSER_DATA!;
    const frozen = JSON.parse(
      readFileSync(
        path.join(root, "snapshots", pf.snapshotId, "snapshot.json"),
        "utf8",
      ),
    );
    expect(frozen.configuration.duration).toBe(0.9);
    const old = JSON.parse(
      readFileSync(
        path.join(root, "snapshots", runs[1].snapshotId, "snapshot.json"),
        "utf8",
      ),
    );
    expect(old.configuration.duration).toBe(0.6);
    expect(
      (await request(page, "/runs")).items.filter(
        (r: any) => r.projectId === project.projectId,
      ),
    ).toHaveLength(3);
    expect(writes).toEqual([
      "/api/v1/comparisons",
      "/api/v1/comparisons",
      `/api/v1/projects/${project.projectId}/preflights`,
    ]);
    await page
      .getByRole("button", { name: "Back to draft", exact: true })
      .click();
    await info.attach("recorded-comparison-boundaries.json", {
      contentType: "application/json",
      body: JSON.stringify({
        viewport: width,
        runIds: runs.map((r) => r.runId),
        snapshotIds: runs.map((r) => r.snapshotId),
        actualNativeRuns: 3,
        comparisonAndPlaybackCreatedNoRuns: true,
        freshDraftPreflightOnly: pf.snapshotId,
        explicitStartStillRequired: true,
        canonicalProjectUnchanged: true,
      }),
    });
  });
}

for (const width of [1024, 1440]) {
  for (const departure of ["newer baseline", "Home", "deliberate focus"]) {
    test(`comparison completion: held real report preserves ${departure} at ${width}`, async ({
      page,
    }, info) => {
      await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
      await connectStudio(page, info);
      const { project, runs } = await setup(page, width);
      const baseline = page.getByLabel("Baseline run", { exact: true });
      await baseline.selectOption(runs[0].runId);
      let release!: () => void,
        ready!: () => void,
        delivered = false,
        count = 0;
      const gate = new Promise<void>((r) => (release = r)),
        observed = new Promise<void>((r) => (ready = r));
      await page.route("**/api/v1/comparisons", async (route) => {
        count++;
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        ready();
        await gate;
        try {
          await route.fulfill({ response });
        } catch {
          /* Departure can cancel the original read. */
        } finally {
          delivered = true;
        }
      });
      try {
        await page
          .getByRole("button", { name: "Inspect compatibility", exact: true })
          .focus();
        await page.keyboard.press("Enter");
        await observed;
        if (departure === "newer baseline") {
          await baseline.selectOption(runs[2].runId);
          await baseline.focus();
        } else if (departure === "Home") {
          await page
            .getByRole("button", { name: "X-Verse Studio home", exact: true })
            .click();
          await page
            .getByRole("button", { name: "X-Verse Studio home", exact: true })
            .focus();
        } else {
          await page
            .getByRole("button", { name: "Refresh recorded runs", exact: true })
            .focus();
        }
        release();
        await expect.poll(() => delivered).toBe(true);
        if (departure === "newer baseline") {
          await expect(baseline).toHaveValue(runs[2].runId);
          await expect(baseline).toBeFocused();
          await expect(report(page)).toHaveCount(0);
        } else if (departure === "Home") {
          await expect(
            page.getByRole("tab", { name: "Compare", exact: true }),
          ).not.toBeVisible();
          await expect(
            page.getByRole("button", {
              name: "X-Verse Studio home",
              exact: true,
            }),
          ).toBeFocused();
        } else {
          await expect(report(page)).toContainText(runs[0].snapshotId);
          await expect(
            page.getByRole("button", {
              name: "Refresh recorded runs",
              exact: true,
            }),
          ).toBeFocused();
        }
        expect(count).toBe(1);
        expect(await request(page, "/projects/" + project.projectId)).toEqual(
          project,
        );
        expect(
          (await request(page, "/runs")).items.filter(
            (r: any) => r.projectId === project.projectId,
          ),
        ).toHaveLength(3);
      } finally {
        release();
        await page.unroute("**/api/v1/comparisons");
      }
      await info.attach("comparison-held-real-read.json", {
        contentType: "application/json",
        body: JSON.stringify({
          viewport: width,
          departure,
          actualNativeRuns: 3,
          actualHttp200Held: true,
          requests: count,
          canonicalProjectUnchanged: true,
          noRunCreatedByComparison: true,
        }),
      });
    });
  }
  for (const mode of [
    "wrong identity",
    "unknown version",
    "deep metadata",
    "contradictory summary",
  ]) {
    test(`comparison response guards: ${mode} fixture is rejected and actual retry succeeds at ${width}`, async ({
      page,
    }, info) => {
      await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
      await connectStudio(page, info);
      const { runs } = await setup(page, width);
      await page
        .getByLabel("Baseline run", { exact: true })
        .selectOption(runs[0].runId);
      await page.route("**/api/v1/comparisons", async (route) => {
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        const value = await response.json();
        if (mode === "wrong identity") value.leftRunId = "fixture-wrong-run";
        else if (mode === "unknown version")
          value.comparisonVersion = "future-fixture";
        else if (mode === "contradictory summary")
          value.fields[0].left.summary.status = "unavailable";
        else {
          let nested: any = 1;
          for (let i = 0; i < 1000; i++) nested = { nested };
          value.configuration.find((r: any) => r.field === "parameters").left =
            nested;
        }
        await route.fulfill({
          response,
          body: JSON.stringify(value),
          contentType: "application/json",
        });
      });
      try {
        await page
          .getByRole("button", { name: "Inspect compatibility", exact: true })
          .focus();
        await page.keyboard.press("Enter");
        await expect(page.getByRole("alert")).toContainText(
          "comparison response is malformed",
        );
        await expect(page.getByRole("alert")).toBeFocused();
        await expect(report(page)).toHaveCount(0);
        await expect(
          page.getByLabel("Baseline run", { exact: true }),
        ).toHaveValue(runs[0].runId);
      } finally {
        await page.unroute("**/api/v1/comparisons");
      }
      await page
        .getByRole("button", { name: "Inspect compatibility", exact: true })
        .click();
      await expect(report(page)).toContainText("Compatible recorded windows");
      await expect(
        page.getByRole("heading", { name: "Comparison report", exact: true }),
      ).toBeFocused();
      await info.attach("comparison-transport-fixture.json", {
        contentType: "application/json",
        body: JSON.stringify({
          scope:
            "Labelled modified transport reply derived from actual HTTP200; no new provider or live identity admission.",
          mode,
          viewport: width,
          actualRetrySucceeded: true,
        }),
      });
    });
  }
}

for (const width of [1024, 1440]) {
  test(`comparison history: bounded paging, empty and unavailable transport fixtures at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const { project, runs } = await setup(page, width);
    let mode = "paged";
    const writes: string[] = [];
    page.on("request", (r) => {
      if (r.method() !== "GET" && r.url().includes("/api/v1/"))
        writes.push(r.method() + " " + new URL(r.url()).pathname);
    });
    const pattern = /\/api\/v1\/runs\?/;
    await page.route(pattern, async (route) => {
      if (mode === "error")
        return route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({
            code: "FIXTURE_HISTORY_UNAVAILABLE",
            message: "Labelled unavailable recorded history fixture.",
          }),
        });
      const offset = Number(
        new URL(route.request().url()).searchParams.get("cursor") || 0,
      );
      const items =
        mode === "empty"
          ? []
          : Array.from({ length: offset ? 1 : 20 }, (_, i) => ({
              runId: "fixture-record-" + (offset + i),
              snapshotId: runs[0].snapshotId,
              projectId: project.projectId,
              state: "stopped",
            }));
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items,
          nextCursor: mode === "paged" && !offset ? "20" : null,
        }),
      });
    });
    try {
      await page
        .getByRole("button", { name: "Refresh recorded runs", exact: true })
        .click();
      await expect(
        page.getByLabel("Baseline run", { exact: true }).locator("option"),
      ).toHaveCount(21);
      await page
        .getByRole("button", { name: "Next runs page", exact: true })
        .click();
      await expect(
        page.getByLabel("Baseline run", { exact: true }).locator("option"),
      ).toHaveCount(2);
      await expect(
        page.getByLabel("Baseline run", { exact: true }),
      ).toContainText("fixture-record-20");
      await page
        .getByRole("button", { name: "Previous runs page", exact: true })
        .click();
      await expect(
        page.getByLabel("Baseline run", { exact: true }).locator("option"),
      ).toHaveCount(21);
      mode = "empty";
      await page
        .getByRole("button", { name: "Refresh recorded runs", exact: true })
        .click();
      await expect(
        page.getByText(
          "No other recorded runs on this page. Refresh or choose another page.",
          { exact: true },
        ),
      ).toBeVisible();
      mode = "error";
      await page
        .getByRole("button", { name: "Refresh recorded runs", exact: true })
        .focus();
      await page.keyboard.press("Enter");
      await expect(page.getByRole("alert")).toContainText(
        "FIXTURE_HISTORY_UNAVAILABLE",
      );
      await expect(page.getByRole("alert")).toContainText(
        "Previous history observations have not been refreshed",
      );
      await expect(page.getByRole("alert")).toBeFocused();
      expect(writes).toEqual([]);
    } finally {
      await page.unroute(pattern);
    }
    expect(await request(page, "/projects/" + project.projectId)).toEqual(
      project,
    );
    expect(
      (await request(page, "/runs")).items.filter(
        (r: any) => r.projectId === project.projectId,
      ),
    ).toHaveLength(3);
    await info.attach("comparison-history-fixture.json", {
      contentType: "application/json",
      body: JSON.stringify({
        scope:
          "Labelled 21-row/empty/HTTP503 transport fixtures derived from one real run. Not21 native runs or provider evidence.",
        viewport: width,
        actualNativeRuns: 3,
        historyMutationRequests: writes.length,
        canonicalProjectUnchanged: true,
      }),
    });
  });
}
