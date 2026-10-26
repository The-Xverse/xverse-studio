import { test, expect, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { connectStudio } from "./connect-studio";
async function ownedRun(page: Page, name: string, target = 1) {
  return page.evaluate(
    async ({ name, target }) => {
      const session = await fetch("/api/v1/session").then((r) => r.json());
      const post = async (
        path: string,
        body: any,
        key?: string,
        revision?: number,
      ) => {
        const response = await fetch("/api/v1" + path, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": session.csrfToken,
            ...(key ? { "Idempotency-Key": key } : {}),
            ...(revision ? { "If-Match": String(revision) } : {}),
          },
          body: JSON.stringify(body),
        });
        if (!response.ok) throw new Error(await response.text());
        return response.json();
      };
      const p = await post("/projects", { name });
      const changed = await post(
        `/projects/${p.projectId}/edits`,
        {
          baseRevision: p.revision,
          edits: [
            { kind: "set_parameter", parameterId: "duration", value: 0.2 },
            { kind: "set_parameter", parameterId: "target", value: target },
          ],
        },
        undefined,
        p.revision,
      );
      const pf = await post(`/projects/${p.projectId}/preflights`, {
        revision: changed.revision,
      });
      const start = await post(
        "/runs",
        { snapshotId: pf.snapshotId, preflightId: pf.preflightId },
        crypto.randomUUID(),
      );
      return { project: changed, runId: start.runId };
    },
    { name, target },
  );
}
async function showRun(page: Page, projectId: string, runId: string) {
  await page.evaluate(
    ({ projectId, runId }) => {
      localStorage.setItem("studio.projectId", projectId);
      localStorage.setItem("studio.lastRun." + projectId, runId);
      localStorage.setItem("studio.lastRun", runId);
    },
    { projectId, runId },
  );
  await page.reload();
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  await expect(
    page.getByRole("heading", { name: /Run results/ }),
  ).toBeVisible();
}
test("evidence filters: native receipt UTC, explicit source window and read-only emitter filtering", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  const made = await ownedRun(page, "Evidence receipt and filters");
  await expect
    .poll(async () =>
      page.evaluate(
        async (id) =>
          (await fetch("/api/v1/runs/" + id).then((r) => r.json())).state,
        made.runId,
      ),
    )
    .toBe("stopped");
  await showRun(page, made.project.projectId, made.runId);
  const posts: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST") posts.push(r.url());
  });
  await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  await expect(page.locator(".event-row").first()).toBeVisible();
  const history = await page.evaluate(
    async (id) =>
      fetch(`/api/v1/runs/${id}/history?limit=200`).then((r) => r.json()),
    made.runId,
  );
  const first = history.items[0];
  await expect(
    page.locator(`[data-event-id="${first.eventId}"] time`),
  ).toHaveAttribute(
    "datetime",
    history.presentation[first.eventId].recordedAtUtc,
  );
  await page
    .getByLabel("Emitter provider", { exact: true })
    .selectOption("studio.reference");
  await page
    .getByRole("button", { name: "Apply evidence filters", exact: true })
    .click();
  await expect(
    page.getByRole("group", { name: "Delivery view", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Time basis", { exact: true }).selectOption("source");
  await page
    .getByLabel("Source clock", { exact: true })
    .selectOption("simulation-time");
  await page.getByLabel("Start tick (inclusive)", { exact: true }).fill("0");
  await page.getByLabel("End tick (exclusive)", { exact: true }).fill("100000");
  await page
    .getByRole("button", { name: "Apply evidence filters", exact: true })
    .click();
  const expected = history.items.filter(
    (event: any) =>
      event.source?.providerId === "studio.reference" &&
      event.sourceTime?.clockDomain === "simulation-time" &&
      /^-?\d+$/.test(event.sourceTime?.tick) &&
      BigInt(event.sourceTime.tick) >= 0n &&
      BigInt(event.sourceTime.tick) < 100000n,
  );
  await expect(page.locator(".event-row")).toHaveCount(expected.length);
  for (const event of expected)
    await expect(
      page.locator(`[data-event-id="${event.eventId}"]`),
    ).toBeVisible();
  expect(posts).toEqual([]);
  await page.screenshot({
    path: testInfo.outputPath("evidence-source-window.png"),
    fullPage: true,
  });
});

test("evidence filters: display fixture never plots missing source time as zero or array index", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  const made = await ownedRun(page, "Missing-time display contract");
  await expect
    .poll(async () =>
      page.evaluate(
        async (id) =>
          (await fetch("/api/v1/runs/" + id).then((r) => r.json())).state,
        made.runId,
      ),
    )
    .toBe("stopped");
  await page.route(
    `**/api/v1/runs/${made.runId}/observations*`,
    async (route) => {
      const response = await route.fetch();
      await route.fulfill({
        response,
        json: {
          projectionVersion: "1.0",
          integrity: "fixture",
          evidenceScope: "browser_response_fixture",
          facets: { clockDomains: ["fixture-clock"] },
          items: [
            {
              eventId: "fixture-missing",
              recordedAt: "2026-01-01T00:00:00Z",
              sourceTime: null,
              tick: null,
              values: { value: 0, enabled: false },
              units: { value: "1" },
            },
            {
              eventId: "fixture-known",
              recordedAt: "2026-02-31T00:00:00Z",
              sourceTime: {
                tick: "9007199254740993",
                clockDomain: "fixture-clock",
              },
              tick: "9007199254740993",
              values: { value: 1 },
              units: { value: "1" },
            },
          ],
          presentation: {
            "fixture-missing": {
              recordedAtUtc: null,
              receiptEncoding: "unavailable",
              sourceTimeStatus: "missing",
            },
          },
          gaps: [],
          tickUnit: "declared-fixture-tick",
        },
      });
    },
  );
  await showRun(page, made.project.projectId, made.runId);
  await expect(
    page.getByText(
      "1 sample(s) with missing or malformed source time are omitted from the plot and retained in the table.",
      { exact: true },
    ),
  ).toBeVisible();
  const points = page
    .getByRole("img", { name: /Recorded observation chart/ })
    .locator("[data-source-tick]");
  await expect(points).toHaveCount(1);
  await expect(points.first()).toHaveAttribute(
    "data-source-tick",
    "9007199254740993",
  );
  await page.getByRole("button", { name: "Table view", exact: true }).click();
  const row = page
    .getByRole("row")
    .filter({ has: page.locator('[data-observation-id="fixture-missing"]') });
  await expect(
    page.locator('[data-observation-id="fixture-missing"]'),
  ).toContainText("Unavailable");
  await expect(
    page.locator('[data-observation-id="fixture-missing"]'),
  ).toContainText("false");
  await expect(
    page.locator('[data-observation-id="fixture-missing"]'),
  ).toContainText("Receipt time unavailable");
  await expect(
    page.locator('[data-observation-id="fixture-known"]'),
  ).toContainText("Receipt time unavailable");
  await page.screenshot({
    path: testInfo.outputPath("missing-time-display-fixture.png"),
    fullPage: true,
  });
});
test("evidence filters: late original-run observations cannot overwrite an explicitly selected rerun", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  const made = await ownedRun(page, "Observation response isolation");
  await expect
    .poll(async () =>
      page.evaluate(
        async (id) =>
          (await fetch("/api/v1/runs/" + id).then((r) => r.json())).state,
        made.runId,
      ),
    )
    .toBe("stopped");
  let release!: () => void, reached!: () => void;
  const gate = new Promise<void>((resolve) => {
      release = resolve;
    }),
    waiting = new Promise<void>((resolve) => {
      reached = resolve;
    });
  await page.route(
    `**/api/v1/runs/${made.runId}/observations*`,
    async (route) => {
      const response = await route.fetch();
      reached();
      await gate;
      try {
        await route.fulfill({ response });
      } catch {
        /* Aborted obsolete browser read is expected. */
      }
    },
  );
  await showRun(page, made.project.projectId, made.runId);
  await waiting;
  await page
    .getByRole("button", { name: "Rerun frozen inputs", exact: true })
    .click();
  await expect
    .poll(() => page.evaluate(() => localStorage.getItem("studio.lastRun")))
    .not.toBe(made.runId);
  const successor = await page.evaluate(() =>
    localStorage.getItem("studio.lastRun"),
  );
  await expect(
    page.getByText("stopped", { exact: true }).first(),
  ).toBeVisible();
  const provenance = page
    .getByRole("heading", {
      name: "Input and evidence provenance",
      exact: true,
    })
    .locator("..");
  await provenance.getByText("Inspect exact data", { exact: true }).click();
  await expect(provenance.locator("pre")).toContainText(successor!);
  release();
  await page.waitForLoadState("networkidle");
  await expect(provenance.locator("pre")).toContainText(successor!);
  await expect(provenance.locator("pre")).not.toContainText(made.runId + ":");
  await testInfo.attach("obsolete-observation-read", {
    body: JSON.stringify({
      oldRunId: made.runId,
      newRunId: successor,
      transition: "explicit owned rerun; no filter triggers lifecycle mutation",
    }),
    contentType: "application/json",
  });
});

test("evidence filters: sealed recorded fixture exact clocks, whole-run facets and bounded read-only pages at both viewports", async ({
  page,
}, testInfo) => {
  test.setTimeout(120000);
  await connectStudio(page, testInfo);
  const project = await page.evaluate(async () => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const r = await fetch("/api/v1/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({
        name: "Sealed recorded evidence filtering fixture",
      }),
    });
    if (!r.ok) throw Error(await r.text());
    return r.json();
  });
  const fixture = JSON.parse(
    execFileSync(
      path.resolve(".venv/bin/python"),
      [
        "tests/fixtures/evidence/create_recorded_evidence.py",
        "--data-dir",
        process.env.STUDIO_BROWSER_DATA!,
        "--project-id",
        project.projectId,
      ],
      { encoding: "utf8" },
    ),
  );
  await testInfo.attach("fixture-scope", {
    body: JSON.stringify(fixture),
    contentType: "application/json",
  });
  await showRun(page, project.projectId, fixture.runId);
  const writes: string[] = [];
  page.on("request", (r) => {
    if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
      writes.push(r.method() + " " + r.url());
  });
  const apply = () =>
    page
      .getByRole("button", { name: "Apply evidence filters", exact: true })
      .click();
  const reset = () =>
    page
      .getByRole("button", { name: "Reset evidence filters", exact: true })
      .click();
  for (const width of [1440, 1024]) {
    await page.setViewportSize({ width, height: width === 1440 ? 900 : 768 });
    await expect(
      page.getByText("Select one original source clock to plot", {
        exact: true,
      }),
    ).toBeVisible();
    await expect(page.locator("[data-observation-id]")).toHaveCount(200);
    await expect(
      page.getByLabel("Evidence read quality", { exact: true }),
    ).toContainText("Reader integrity: valid");
    await expect(
      page.getByText(/The reader reports collection gaps/),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Next observation page", exact: true })
      .click();
    await expect(
      page.locator(`[data-observation-id="${fixture.events.late}"]`),
    ).toBeVisible();
    expect(
      await page.locator("[data-observation-id]").count(),
    ).toBeLessThanOrEqual(200);
    await page
      .getByRole("button", { name: "Previous observation page", exact: true })
      .click();
    await expect(page.locator("[data-observation-id]")).toHaveCount(200);
    // Facets cover the whole run: selected exists only after 205 unrelated observations.
    await page
      .getByLabel("Observation field", { exact: true })
      .selectOption("selected");
    await apply();
    await expect(page.locator("[data-observation-id]")).toHaveCount(1);
    await expect(
      page.locator(`[data-observation-id="${fixture.events.late}"]`),
    ).toContainText("false");
    await reset();
    await expect(page.locator("[data-observation-id]")).toHaveCount(200);
    await page.getByLabel("Time basis", { exact: true }).selectOption("source");
    await page
      .getByLabel("Source clock", { exact: true })
      .selectOption("clock-alpha");
    await page
      .getByLabel("Start tick (inclusive)", { exact: true })
      .fill(fixture.ticks.start);
    await page
      .getByLabel("End tick (exclusive)", { exact: true })
      .fill(fixture.ticks.end);
    await page
      .getByRole("button", { name: "Apply evidence filters", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("img", { name: /Recorded observation chart/ }),
    ).toBeVisible();
    const points = page
      .getByRole("img", { name: /Recorded observation chart/ })
      .locator("[data-source-tick]");
    await expect(points).toHaveCount(1);
    await expect(points.first()).toHaveAttribute(
      "data-source-tick",
      fixture.ticks.start,
    );
    await page.getByRole("button", { name: "Table view", exact: true }).click();
    await expect(page.locator("[data-observation-id]")).toHaveCount(1);
    await expect(
      page.locator(`[data-observation-id="${fixture.events.hugeInside}"]`),
    ).toContainText(fixture.ticks.start);
    await page.getByLabel("Start tick (inclusive)", { exact: true }).fill("-2");
    await page.getByLabel("End tick (exclusive)", { exact: true }).fill("1");
    await apply();
    await expect(page.locator("[data-observation-id]")).toHaveCount(2);
    await expect(
      page.locator(`[data-observation-id="${fixture.events.negative}"]`),
    ).toBeVisible();
    await expect(
      page.locator(`[data-observation-id="${fixture.events.zero}"]`),
    ).toContainText("false");
    await reset();
    await expect(page.locator("[data-observation-id]")).toHaveCount(200);
    await page
      .getByLabel("Emitter provider", { exact: true })
      .selectOption("fixture.beta");
    await page
      .getByLabel("Observer", { exact: true })
      .selectOption("external-observer");
    await apply();
    await expect(page.locator("[data-observation-id]")).toHaveCount(1);
    await expect(
      page.locator(`[data-observation-id="${fixture.events.otherClock}"]`),
    ).toContainText("clock-beta");
    await reset();
    await expect(page.locator("[data-observation-id]")).toHaveCount(200);
    const element = await page
      .getByLabel("Element reference", { exact: true })
      .locator("option")
      .evaluateAll(
        (opts) =>
          (opts as HTMLOptionElement[]).find((o) => o.value.endsWith("#plant"))
            ?.value,
      );
    expect(element).toBeTruthy();
    await page
      .getByLabel("Element reference", { exact: true })
      .selectOption(element!);
    await apply();
    await expect(page.getByText(/Selected element:/)).toBeVisible();
    await reset();
    await expect(page.locator("[data-observation-id]")).toHaveCount(200);
    await page
      .getByLabel("Time basis", { exact: true })
      .selectOption("recorded");
    await page
      .getByLabel("Receipt from (inclusive)", { exact: true })
      .fill("2026-02-31T00:00:00Z");
    await page
      .getByLabel("Receipt until (exclusive)", { exact: true })
      .fill("2026-03-04T00:00:00Z");
    await apply();
    await expect(
      page.getByRole("alert").filter({ hasText: "Supply RFC3339" }),
    ).toBeVisible();
    await page
      .getByLabel("Receipt from (inclusive)", { exact: true })
      .fill("2026-01-01T00:00:00.1234567Z");
    await apply();
    await expect(
      page.getByRole("alert").filter({ hasText: "Supply RFC3339" }),
    ).toBeVisible();
    await page
      .getByLabel("Receipt from (inclusive)", { exact: true })
      .fill("2026-01-01T00:00:00Z");
    await page
      .getByLabel("Receipt until (exclusive)", { exact: true })
      .fill("2026-01-01T00:00:02Z");
    await apply();
    await expect(page.locator("[data-observation-id]")).toHaveCount(2);
    await expect(
      page.locator(`[data-observation-id="${fixture.events.hugeBefore}"]`),
    ).toContainText("2026-01-01T00:00:00.250000Z");
    await expect(
      page.locator(`[data-observation-id="${fixture.events.hugeInside}"]`),
    ).toBeVisible();
    const numericReceipt = page.locator(
      `[data-observation-id="${fixture.events.hugeBefore}"]`,
    );
    await numericReceipt.getByText("Original receipt", { exact: true }).click();
    await expect(numericReceipt.locator("pre")).toContainText("1767225600.25");
    await numericReceipt.getByText("Original receipt", { exact: true }).click();
    const tableRegion = page.getByRole("region", {
      name: "Exact observation table scroll region",
      exact: true,
    });
    await tableRegion.focus();
    await expect(tableRegion).toBeFocused();
    const scrollSize = await tableRegion.evaluate((el) => ({
      width: el.clientWidth,
      content: el.scrollWidth,
    }));
    if (scrollSize.content > scrollSize.width) {
      await page.keyboard.press("ArrowRight");
      await expect
        .poll(() => tableRegion.evaluate((el) => el.scrollLeft))
        .toBeGreaterThan(0);
    }
    await testInfo.attach(`table-keyboard-${width}`, {
      body: JSON.stringify({
        viewport: width,
        ...scrollSize,
        focused: true,
        scrollLeft: await tableRegion.evaluate((el) => el.scrollLeft),
      }),
      contentType: "application/json",
    });
    await page.screenshot({
      path: testInfo.outputPath(`recorded-filter-${width}.png`),
      fullPage: true,
    });
    await reset();
    await page
      .getByRole("tab", { name: "Events & logs", exact: false })
      .click();
    await expect(page.locator(".event-row")).toHaveCount(200);
    await expect(
      page.locator(`[data-event-id="${fixture.events.hugeBefore}"] time`),
    ).toHaveAttribute("datetime", "2026-01-01T00:00:00.250000Z");
    await expect(
      page.locator(`[data-event-id="${fixture.events.unknownReceipt}"] time`),
    ).not.toHaveAttribute("datetime");
    await expect(
      page.locator(`[data-event-id="${fixture.events.unknownReceipt}"] time`),
    ).toContainText("Receipt time unavailable");
    await page
      .getByLabel("Emitter provider", { exact: true })
      .selectOption("fixture.late");
    await page.getByLabel("Severity", { exact: true }).selectOption("error");
    await apply();
    await expect(page.locator(".event-row")).toHaveCount(1);
    await expect(
      page.locator(`[data-event-id="${fixture.events.lateLog}"]`),
    ).toBeVisible();
    await page.getByLabel("Severity", { exact: true }).selectOption("");
    await reset();
    await expect(page.locator(".event-row")).toHaveCount(200);
    await page.getByRole("tab", { name: "Observations", exact: false }).click();
    if (
      await page.getByRole("button", { name: "Plot view", exact: true }).count()
    )
      await page
        .getByRole("button", { name: "Plot view", exact: true })
        .click();
  }
  expect(writes).toEqual([]);
  const detail = await page.evaluate(
    async (id) => fetch(`/api/v1/runs/${id}`).then((r) => r.json()),
    fixture.runId,
  );
  expect(detail.evidenceScope).toBe("recorded_fixture");
  expect(detail.capabilities).toEqual([]);
});

test("evidence filters: incompatible time resolution and numeric units remain table-only", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  const made = await ownedRun(page, "Incompatible display metadata fixture");
  await expect
    .poll(async () =>
      page.evaluate(
        async (id) =>
          (await fetch(`/api/v1/runs/${id}`).then((r) => r.json())).state,
        made.runId,
      ),
    )
    .toBe("stopped");
  let mismatch: "resolution" | "units" = "resolution";
  await page.route(
    `**/api/v1/runs/${made.runId}/observations*`,
    async (route) => {
      const response = await route.fetch();
      await route.fulfill({
        response,
        json: {
          projectionVersion: "1.0",
          integrity: "fixture",
          evidenceScope: "browser_response_fixture",
          facets: { clockDomains: ["fixture-clock"] },
          items: [
            {
              eventId: "fixture-a",
              sourceTime: {
                tick: "1",
                clockDomain: "fixture-clock",
                resolution: "nanosecond",
              },
              values: { value: 0 },
              units: { value: "V" },
            },
            {
              eventId: "fixture-b",
              sourceTime: {
                tick: "2",
                clockDomain: "fixture-clock",
                resolution:
                  mismatch === "resolution" ? "microsecond" : "nanosecond",
              },
              values: { value: 1 },
              units: { value: mismatch === "units" ? "mV" : "V" },
            },
          ],
          gaps: [],
        },
      });
    },
  );
  await showRun(page, made.project.projectId, made.runId);
  await expect(
    page.getByText(
      "Original source resolutions differ; no alignment is assumed",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("img", { name: /Recorded observation chart/ }),
  ).toHaveCount(0);
  await expect(page.locator("[data-observation-id]")).toHaveCount(2);
  mismatch = "units";
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(
    page.getByText("Numeric quantity units differ; use the exact table", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("img", { name: /Recorded observation chart/ }),
  ).toHaveCount(0);
  await expect(page.locator("[data-observation-id]")).toHaveCount(2);
});

test("evidence filters: live buffer remains filterable after an aborted retained read", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  const made = await ownedRun(page, "Live delivery read isolation");
  await expect
    .poll(async () =>
      page.evaluate(
        async (id) =>
          (await fetch(`/api/v1/runs/${id}`).then((r) => r.json())).state,
        made.runId,
      ),
    )
    .toBe("stopped");
  let release!: () => void, reached!: () => void;
  const gate = new Promise<void>((r) => (release = r)),
    waiting = new Promise<void>((r) => (reached = r));
  await page.route(`**/api/v1/runs/${made.runId}/history*`, async (route) => {
    const response = await route.fetch();
    reached();
    await gate;
    try {
      await route.fulfill({ response });
    } catch {
      /* cancelled obsolete retained read */
    }
  });
  await showRun(page, made.project.projectId, made.runId);
  await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  await waiting;
  await page
    .getByRole("button", { name: "Live buffer · at most 200", exact: true })
    .click();
  try {
    await expect(
      page.getByRole("button", { name: "Apply evidence filters", exact: true }),
    ).toBeEnabled();
    await page
      .getByLabel("Emitter provider", { exact: true })
      .selectOption("studio.reference");
    await page
      .getByRole("button", { name: "Apply evidence filters", exact: true })
      .click();
    await expect(
      page.getByRole("button", {
        name: "Live buffer · at most 200",
        exact: true,
      }),
    ).toHaveAttribute("aria-pressed", "true");
  } finally {
    release();
  }
});
