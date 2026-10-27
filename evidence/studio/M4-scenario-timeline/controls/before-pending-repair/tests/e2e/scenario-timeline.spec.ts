import { test, expect, type Page } from "@playwright/test";
import { parse, stringify } from "yaml";
import { connectStudio } from "./connect-studio";
async function request(
  page: Page,
  path: string,
  method = "GET",
  body?: any,
  revision?: number,
) {
  return page.evaluate(
    async ({ path, method, body, revision }) => {
      const session = await fetch("/api/v1/session").then((r) => r.json());
      const response = await fetch("/api/v1" + path, {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": session.csrfToken,
          ...(revision ? { "If-Match": String(revision) } : {}),
          ...(method === "POST"
            ? { "Idempotency-Key": crypto.randomUUID() }
            : {}),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
      if (!response.ok)
        throw new Error(
          path + ": " + response.status + " " + (await response.text()),
        );
      return response.json();
    },
    { path, method, body, revision },
  );
}
async function prepare(page: Page, width: number, dense = false) {
  let project = await request(page, "/projects", "POST", {
    name: "Owned timeline " + width,
  });
  const [docId, doc]: any = Object.entries(project.documents).find(
    ([, d]: any) => d.path.endsWith("/scenario.xdl.yaml"),
  )!;
  const scenario = parse(doc.content);
  const params = scenario.extensions["io.xverse.experiment"].parameters;
  const duration = dense ? 2.1 : 0.2;
  params.find((p: any) => p.id === "duration").value = duration;
  if (dense) params.find((p: any) => p.id === "timestep").value = 0.01;
  params.find((p: any) => p.id === "fault").value = "stuck-sensor";
  const definitions =
    scenario.extensions["io.xverse.studio.experiments"].definitions;
  definitions.forEach(
    (d: any) => (d.window.endTick = String(Math.round(duration * 1000000))),
  );
  definitions.push({
    ...structuredClone(definitions[0]),
    evaluationId: "timeline-peak",
    name: "Timeline peak",
    kind: "metric",
    resultUnit: "1",
    expression: structuredClone(definitions[0].expression.left),
  });
  project = await request(
    page,
    `/projects/${project.projectId}/documents/${docId}`,
    "PUT",
    { content: stringify(scenario), format: "yaml" },
    project.revision,
  );
  const pf = await request(
    page,
    `/projects/${project.projectId}/preflights`,
    "POST",
    { revision: project.revision },
  );
  expect(pf.status, JSON.stringify(pf)).toBe("ready");
  const created = await request(page, "/runs", "POST", {
    snapshotId: pf.snapshotId,
    preflightId: pf.preflightId,
  });
  await expect
    .poll(async () => (await request(page, `/runs/${created.runId}`)).state)
    .toBe("stopped");
  const run = await request(page, `/runs/${created.runId}`);
  const snapshot = (await request(page, `/runs/${run.runId}/snapshot`))
    .snapshot;
  for (const d of (await request(page, `/runs/${run.runId}/definitions`))
    .items) {
    await request(page, `/runs/${run.runId}/evaluations`, "POST", {
      snapshotId: run.snapshotId,
      definitionRef: d.definitionRef,
      definitionDigest: d.definitionDigest,
      evidenceRefs: [run.runId + ":reference-journal"],
    });
  }
  const timeline = await request(page, `/runs/${run.runId}/timeline?limit=200`);
  expect(
    timeline.items.some((r: any) => r.kind === "fault.activation_observed"),
  ).toBe(true);
  scenario.spec.steps[0].id = "later-start";
  project = await request(
    page,
    `/projects/${project.projectId}/documents/${docId}`,
    "PUT",
    { content: stringify(scenario), format: "yaml" },
    project.revision,
  );
  const runIds = (await request(page, "/runs")).items.map((r: any) => r.runId);
  await page.evaluate(
    ({ project, run, snapshot }) => {
      localStorage.setItem("studio.projectId", project.projectId);
      localStorage.setItem("studio.lastRun." + project.projectId, run.runId);
      localStorage.setItem("studio.lastRun", run.runId);
      localStorage.setItem(
        "studio.selection." + project.projectId,
        JSON.stringify({
          deploymentRef: snapshot.selection.deploymentRef,
          scenarioRef: snapshot.selection.scenarioRef,
        }),
      );
    },
    { project, run, snapshot },
  );
  await page.reload();
  await page.getByRole("tab", { name: "Experiments", exact: true }).focus();
  await page.keyboard.press("Enter");
  return { project, run, snapshot, timeline, runIds };
}
for (const width of [1024, 1440]) {
  test(`scenario timeline: native frozen intent, observed faults and evaluation windows at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const made = await prepare(page, width);
    const writes: string[] = [],
      errors: string[] = [];
    page.on("request", (r) => {
      if (!["GET", "HEAD", "OPTIONS"].includes(r.method()))
        writes.push(r.method() + " " + new URL(r.url()).pathname);
    });
    page.on("pageerror", (e) => errors.push(e.message));
    await page.getByRole("tab", { name: "Timeline", exact: true }).focus();
    await page.keyboard.press("Enter");
    const panel = page.getByRole("region", {
      name: "Selected run timeline",
      exact: true,
    });
    await panel
      .getByRole("button", {
        name: "Inspect selected run timeline",
        exact: true,
      })
      .focus();
    await page.keyboard.press("Enter");
    const heading = panel.getByRole("heading", {
      name: "Selected run timeline",
      exact: true,
    });
    await expect(heading).toBeFocused();
    await expect(panel).toContainText(made.snapshot.snapshotId);
    await expect(panel).toContainText(
      "Current draft differs from the executed revision",
    );
    await expect(
      panel.getByRole("table", { name: "Timeline records", exact: true }),
    ).toBeVisible();
    await expect(
      panel.locator('[data-timeline-id="intent:steps:start-reference"]'),
    ).toBeVisible();
    await expect(
      panel.locator('[data-timeline-id="intent:steps:later-start"]'),
    ).toHaveCount(0);
    for (const kind of [
      "fault.activation_requested",
      "fault.activation_observed",
    ]) {
      const row = panel
        .locator("tr[data-timeline-id]")
        .filter({ hasText: kind });
      await expect(row).toHaveCount(1);
      await expect(row).toContainText("100000");
      await expect(row).toContainText("owned_reference");
    }
    const assertion = panel
      .locator("tr[data-timeline-id]")
      .filter({ hasText: "assertion" });
    await expect(assertion).toContainText("complete");
    await expect(assertion).toContainText("pass");
    await expect(assertion).toContainText("[0, 200000)");
    const metric = panel
      .locator("tr[data-timeline-id]")
      .filter({ hasText: "evaluation · metric" });
    await expect(metric).toContainText("No verdict");
    expect(await request(page, `/projects/${made.project.projectId}`)).toEqual(
      made.project,
    );
    expect(
      (await request(page, `/runs/${made.run.runId}/snapshot`)).snapshot,
    ).toEqual(made.snapshot);
    expect((await request(page, `/runs/${made.run.runId}`)).journalDigest).toBe(
      made.run.journalDigest,
    );
    expect(
      (await request(page, "/runs")).items.map((r: any) => r.runId),
    ).toEqual(made.runIds);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth + 1,
      ),
    ).toBe(false);
    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
    await info.attach("owned-timeline-context", {
      body: JSON.stringify({
        runId: made.run.runId,
        snapshotId: made.snapshot.snapshotId,
        revision: made.snapshot.revision,
        projectRevision: made.project.revision,
        scope: made.timeline.evidenceScope,
      }),
      contentType: "application/json",
    });
    await page.screenshot({
      path: info.outputPath("scenario-timeline.png"),
      fullPage: true,
    });
  });
}

for (const width of [1024, 1440]) {
  test(`scenario authoring completion: held conditions acknowledgement preserves a reopened draft at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const made = await prepare(page, width);
    const open = page.getByRole("button", {
      name: "Edit initial conditions",
      exact: true,
    });
    await open.focus();
    await page.keyboard.press("Enter");
    await page
      .getByLabel("Scenario acceptance intent", { exact: true })
      .fill("First committed conditions");
    let release!: () => void;
    const released = new Promise<void>((resolve) => (release = resolve));
    let ready = false,
      committed: any = null,
      writes = 0;
    await page.route(
      `**/api/v1/projects/${made.project.projectId}/edits`,
      async (route) => {
        if (route.request().method() !== "POST") return route.continue();
        writes++;
        const response = await route.fetch({ timeout: 30000 });
        committed = await response.json();
        ready = true;
        await released;
        await route.fulfill({ response });
      },
    );
    try {
      await page
        .getByRole("button", { name: "Save scenario conditions", exact: true })
        .focus();
      await page.keyboard.press("Enter");
      await expect.poll(() => ready, { timeout: 30000 }).toBe(true);
      await page.keyboard.press("Enter");
      expect(writes).toBe(1);
      await page.keyboard.press("Escape");
      await open.focus();
      await page.keyboard.press("Enter");
      const draft = page.getByLabel("Scenario acceptance intent", {
        exact: true,
      });
      await draft.fill("Keep this newer unsaved draft");
      await draft.focus();
      release();
      await expect
        .poll(
          async () =>
            (await request(page, `/projects/${made.project.projectId}`))
              .revision,
        )
        .toBe(committed.revision);
      // Observe completion from the actual page transport, then preserve the newer form/focus.
      await expect(page.locator(".project-header")).toContainText(
        String(committed.revision),
      );
      await expect(draft).toBeVisible();
      await expect(draft).toHaveValue("Keep this newer unsaved draft");
      await expect(draft).toBeFocused();
      expect(writes).toBe(1);
      expect(
        (await request(page, `/runs/${made.run.runId}/snapshot`)).snapshot,
      ).toEqual(made.snapshot);
      await page.keyboard.press("Escape");
    } finally {
      release();
    }
  });
}

async function openTimeline(page: Page) {
  await page.getByRole("tab", { name: "Timeline", exact: true }).focus();
  await page.keyboard.press("Enter");
  const panel = page.getByRole("region", {
    name: "Selected run timeline",
    exact: true,
  });
  return {
    panel,
    inspect: panel.getByRole("button", {
      name: "Inspect selected run timeline",
      exact: true,
    }),
    heading: panel.getByRole("heading", {
      name: "Selected run timeline",
      exact: true,
    }),
  };
}
for (const width of [1024, 1440]) {
  test(`scenario timeline: malformed transport contracts and HTTP retry stay unknown at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const made = await prepare(page, width);
    const { panel, inspect, heading } = await openTimeline(page);
    const writes: string[] = [];
    page.on("request", (r) => {
      if (!["GET", "HEAD", "OPTIONS"].includes(r.method()))
        writes.push(r.method());
    });
    let mode = "http";
    await page.route(
      `**/api/v1/runs/${made.run.runId}/timeline*`,
      async (route) => {
        if (mode === "real") return route.continue();
        if (mode === "http")
          return route.fulfill({
            status: 503,
            json: {
              code: "LABELLED_TIMELINE_UNAVAILABLE",
              message: "Labelled transport fixture",
            },
          });
        const value = structuredClone(made.timeline);
        if (mode === "snapshot") value.snapshotId = "foreign-snapshot";
        if (mode === "version") value.timelineVersion = "99.0";
        if (mode === "authority") value.readOnly = false;
        if (mode === "clock")
          value.items.find(
            (r: any) => r.position.status === "aligned",
          ).position.clockDomain = "unmapped-device-clock";
        if (mode === "metric")
          value.items.find(
            (r: any) => r.layer === "evaluation" && r.kind === "metric",
          ).verdict = "pass";
        if (mode === "window")
          value.items.find(
            (r: any) => r.layer === "evaluation",
          ).window.endTick = "-1";
        if (mode === "definition-context")
          value.assessmentDefinitions.items[0].definition.scenarioRef =
            "xdl://foreign/scenario/foreign";
        if (mode === "definition-shape")
          value.assessmentDefinitions.items[0].definition.expression =
            "unsupported-string";
        if (mode === "duplicate") {
          value.items[1] = structuredClone(value.items[0]);
        }
        await route.fulfill({ json: value });
      },
    );
    for (const next of [
      "http",
      "snapshot",
      "version",
      "authority",
      "clock",
      "metric",
      "window",
      "duplicate",
      "definition-context",
      "definition-shape",
    ]) {
      mode = next;
      await inspect.focus();
      await page.keyboard.press("Enter");
      await expect(panel.getByRole("alert")).toContainText(
        "Timeline availability is unknown",
      );
      await expect(panel.getByRole("alert")).toBeFocused();
      await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(0);
    }
    mode = "real";
    await inspect.focus();
    await page.keyboard.press("Enter");
    await expect(heading).toBeFocused();
    await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(
      made.timeline.items.length,
    );
    expect(writes).toEqual([]);
    expect(await request(page, `/projects/${made.project.projectId}`)).toEqual(
      made.project,
    );
  });
  test(`scenario timeline: labelled exact large ticks, gaps and unsupported clock remain separate at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const made = await prepare(page, width);
    const { panel, inspect, heading } = await openTimeline(page);
    await page.route(
      `**/api/v1/runs/${made.run.runId}/timeline*`,
      async (route) => {
        const clock =
          new URL(route.request().url()).searchParams.get("clockDomain") ||
          "simulation-time";
        const value = structuredClone(made.timeline),
          sample = made.timeline.items.find(
            (r: any) => r.kind === "observation.available",
          );
        value.evidenceScope = "fixture";
        value.intentClockCodec = null;
        value.clockDomain = clock;
        value.tickUnit = clock === "simulation-time" ? "microsecond" : null;
        value.clockDomains = [
          { id: "simulation-time", declared: true, observed: true },
          { id: "device-time", declared: false, observed: true },
        ];
        value.clockDomainsComplete = false;
        value.items = ["9007199254740993", "9007199254740995"].map(
          (tick, i) => ({
            ...structuredClone(sample),
            id: "recorded:labelled-large-" + i,
            eventId: "labelled-large-" + i,
            evidenceScope: "fixture",
            sourceTime: {
              tick,
              clockDomain: "simulation-time",
              resolution: "microsecond",
              uncertainty: 2,
            },
            position: {
              tick,
              clockDomain: "simulation-time",
              tickUnit: "microsecond",
              status: clock === "simulation-time" ? "aligned" : "unplaced",
              reason: clock === "simulation-time" ? null : "CLOCK_NOT_SELECTED",
            },
          }),
        );
        value.items.push({
          ...structuredClone(sample),
          id: "recorded:labelled-unknown",
          eventId: "labelled-unknown",
          evidenceScope: "fixture",
          sourceTime: {
            tick: "7",
            clockDomain: "device-time",
            resolution: "unknown",
          },
          position: {
            tick: "7",
            clockDomain: "device-time",
            tickUnit: null,
            status: "unplaced",
            reason: "TICK_ENCODING_UNADMITTED",
          },
        });
        value.nextCursor = null;
        value.counts = {
          ...value.counts,
          matchedRows: 3,
          returnedRows: 3,
          unplacedRows: clock === "simulation-time" ? 1 : 3,
          recordedInputs: 3,
          recordedInputsConsidered: 3,
          intentInputs: 0,
          intentInputsConsidered: 0,
          evaluationInputsConsidered: 0,
        };
        value.inputsComplete = {
          recorded: false,
          intents: true,
          evaluations: true,
        };
        value.recorded.collectionStatus = "partial";
        value.recorded.gapCount = 1;
        value.recorded.gapsComplete = true;
        value.recorded.gaps = [
          {
            reason: "Labelled transport fixture gap",
            detailUnavailable: false,
            sourceTime: {},
          },
        ];
        await route.fulfill({ json: value });
      },
    );
    await inspect.focus();
    await page.keyboard.press("Enter");
    await expect(heading).toBeFocused();
    await expect(panel).toContainText("9007199254740993");
    await expect(panel).toContainText("9007199254740995");
    await expect(panel).toContainText("Labelled transport fixture gap");
    await expect(panel).toContainText("recorded evidence incomplete");
    const markers = panel.locator("svg .timeline-marker");
    await expect(markers).toHaveCount(2);
    const xs = await markers.evaluateAll((nodes) =>
      nodes.map((n) => Number(n.querySelector("circle")!.getAttribute("cx"))),
    );
    expect(xs[0]).toBeLessThan(xs[1]);
    await panel
      .getByLabel("Timeline clock", { exact: true })
      .selectOption("device-time");
    await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(0);
    await inspect.focus();
    await page.keyboard.press("Enter");
    await expect(heading).toBeFocused();
    await expect(panel.locator("svg .timeline-marker")).toHaveCount(0);
    await expect(panel).toContainText("TICK_ENCODING_UNADMITTED");
    expect((await request(page, `/runs/${made.run.runId}`)).journalDigest).toBe(
      made.run.journalDigest,
    );
    expect(await request(page, `/projects/${made.project.projectId}`)).toEqual(
      made.project,
    );
    await info.attach("fixture-scope", {
      body: "Labelled transport projection only; original journal and snapshot are unchanged. No device clock support or physical execution claim.",
      contentType: "text/plain",
    });
  });
  test(`scenario timeline: native canonical pages preserve identities and reject changed evaluation cursors at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const made = await prepare(page, width, true);
    const { panel, inspect, heading } = await openTimeline(page);
    await inspect.focus();
    await page.keyboard.press("Enter");
    await expect(heading).toBeFocused();
    const expected: string[] = [],
      seen: string[] = [];
    let canonical = await request(
      page,
      `/runs/${made.run.runId}/timeline?limit=100`,
    );
    while (true) {
      expected.push(...canonical.items.map((r: any) => r.id));
      if (!canonical.nextCursor) break;
      canonical = await request(
        page,
        `/runs/${made.run.runId}/timeline?limit=100&cursor=${encodeURIComponent(canonical.nextCursor)}`,
      );
    }
    expect(expected.length).toBeGreaterThan(200);
    while (true) {
      seen.push(
        ...(await panel
          .locator("tr[data-timeline-id]")
          .evaluateAll((nodes) =>
            nodes.map((n) => n.getAttribute("data-timeline-id")!),
          )),
      );
      const next = panel.getByRole("button", {
        name: "Next timeline page",
        exact: true,
      });
      if (await next.isDisabled()) break;
      await next.focus();
      await page.keyboard.press("Enter");
      await expect(heading).toBeFocused();
    }
    expect(seen).toEqual(expected);
    expect(new Set(seen).size).toBe(expected.length);
    await panel
      .getByRole("button", { name: "Previous timeline page", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(heading).toBeFocused();
    await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(100);
    // A new real immutable evaluation changes the bound cursor identity; it is a deliberate setup mutation.
    const d = (await request(page, `/runs/${made.run.runId}/definitions`))
      .items[0];
    await request(page, `/runs/${made.run.runId}/evaluations`, "POST", {
      snapshotId: made.run.snapshotId,
      definitionRef: d.definitionRef,
      definitionDigest: d.definitionDigest,
      evidenceRefs: [made.run.runId + ":reference-journal"],
    });
    await panel
      .getByRole("button", { name: "Next timeline page", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(panel.getByRole("alert")).toContainText(
      "TIMELINE_CURSOR_STALE",
    );
    await expect(panel.getByRole("alert")).toBeFocused();
    await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(0);
    await inspect.focus();
    await page.keyboard.press("Enter");
    await expect(heading).toBeFocused();
    expect((await request(page, `/runs/${made.run.runId}`)).journalDigest).toBe(
      made.run.journalDigest,
    );
  });
  for (const destination of ["focus", "home"]) {
    test(`scenario timeline: held actual read preserves ${destination} at ${width}`, async ({
      page,
    }, info) => {
      await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
      await connectStudio(page, info);
      const made = await prepare(page, width);
      const { panel, inspect, heading } = await openTimeline(page);
      let release!: () => void,
        ready = false,
        requests = 0;
      const gate = new Promise<void>((resolve) => (release = resolve));
      await page.route(
        `**/api/v1/runs/${made.run.runId}/timeline*`,
        async (route) => {
          requests++;
          const response = await route.fetch({ timeout: 30000 });
          ready = true;
          await gate;
          await route.fulfill({ response });
        },
      );
      try {
        await inspect.focus();
        await page.keyboard.press("Enter");
        await expect.poll(() => ready, { timeout: 30000 }).toBe(true);
        await page.keyboard.press("Enter");
        expect(requests).toBe(1);
        const target = page.getByRole("button", {
          name:
            destination === "home"
              ? "X-Verse Studio home"
              : "Edit scenario XDL",
          exact: true,
        });
        await target.focus();
        if (destination === "home") await page.keyboard.press("Enter");
        release();
        if (destination === "focus") {
          await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(
            made.timeline.items.length,
          );
          await expect(target).toBeFocused();
          await expect(heading).not.toBeFocused();
        } else {
          await expect(panel).toHaveCount(0);
          await expect(
            page.getByRole("heading", {
              name: "Start with an example",
              exact: true,
            }),
          ).toBeVisible();
        }
        expect(requests).toBe(1);
        expect(
          await request(page, `/projects/${made.project.projectId}`),
        ).toEqual(made.project);
      } finally {
        release();
      }
    });
  }
  test(`scenario timeline: draft marker opens the typed form and saves canonical intent at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const made = await prepare(page, width);
    const authored = page.getByRole("region", {
      name: "Authored scenario timeline",
      exact: true,
    });
    await expect(
      authored.getByLabel("Authoring clock", { exact: true }),
    ).toHaveValue("simulation-time");
    await authored
      .getByRole("button", {
        name: "Edit timeline step later-start",
        exact: true,
      })
      .focus();
    await page.keyboard.press("Enter");
    await page.getByLabel("Scheduled at", { exact: true }).fill("0.125");
    await page
      .getByRole("button", { name: "Save scenario item", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    const saved = await request(page, `/projects/${made.project.projectId}`),
      scenario: any = Object.values(saved.documents)
        .map((d: any) => parse(d.content))
        .find((r: any) => r.kind === "Scenario");
    expect(saved.revision).toBe(made.project.revision + 1);
    expect(scenario.spec.steps[0].schedule.at).toBe(0.125);
    expect(
      (await request(page, `/runs/${made.run.runId}/snapshot`)).snapshot,
    ).toEqual(made.snapshot);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth + 1,
      ),
    ).toBe(false);
  });
}

for (const width of [1024, 1440]) {
  test(`scenario authoring completion: a newer item draft survives its earlier actual save at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const made = await prepare(page, width);
    await page
      .getByRole("button", {
        name: "Edit timeline step later-start",
        exact: true,
      })
      .focus();
    await page.keyboard.press("Enter");
    const at = page.getByLabel("Scheduled at", { exact: true });
    await at.fill("0.125");
    let release!: () => void,
      ready = false,
      committed: any;
    const gate = new Promise<void>((resolve) => (release = resolve));
    await page.route(
      `**/api/v1/projects/${made.project.projectId}/edits`,
      async (route) => {
        const response = await route.fetch({ timeout: 30000 });
        committed = await response.json();
        ready = true;
        await gate;
        await route.fulfill({ response });
      },
    );
    try {
      await page
        .getByRole("button", { name: "Save scenario item", exact: true })
        .focus();
      await page.keyboard.press("Enter");
      await expect.poll(() => ready, { timeout: 30000 }).toBe(true);
      await at.fill("0.175");
      await at.focus();
      release();
      await expect(page.locator(".project-header .revision")).toHaveText(
        "rev " + committed.revision,
      );
      await expect(at).toHaveValue("0.175");
      await expect(at).toBeFocused();
      const saved = await request(page, `/projects/${made.project.projectId}`),
        source: any = Object.values(saved.documents)
          .map((d: any) => parse(d.content))
          .find((r: any) => r.kind === "Scenario");
      expect(source.spec.steps[0].schedule.at).toBe(0.125);
      expect(
        (await request(page, `/runs/${made.run.runId}/snapshot`)).snapshot,
      ).toEqual(made.snapshot);
      await page.keyboard.press("Escape");
    } finally {
      release();
    }
  });
  test(`scenario authoring completion: real stale revision refuses without discarding the form at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const made = await prepare(page, width);
    await page
      .getByRole("button", { name: "Edit initial conditions", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    const field = page.getByLabel("Scenario acceptance intent", {
      exact: true,
    });
    await field.fill("Keep this refused draft");
    const external = await request(
      page,
      `/projects/${made.project.projectId}/edits`,
      "POST",
      {
        baseRevision: made.project.revision,
        edits: [{ kind: "set_parameter", parameterId: "gain", value: 0.7 }],
      },
      made.project.revision,
    );
    const refused = page.waitForResponse(
      (r) =>
        r.url().endsWith(`/projects/${made.project.projectId}/edits`) &&
        r.request().method() === "POST" &&
        r.status() === 412,
    );
    await page
      .getByRole("button", { name: "Save scenario conditions", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    expect((await refused).status()).toBe(412);
    await expect(page.getByRole("dialog").getByRole("alert")).toBeVisible();
    await expect(field).toHaveValue("Keep this refused draft");
    expect(await request(page, `/projects/${made.project.projectId}`)).toEqual(
      external,
    );
    expect(
      (await request(page, `/runs/${made.run.runId}/snapshot`)).snapshot,
    ).toEqual(made.snapshot);
    await page.keyboard.press("Escape");
  });
  test(`scenario authoring completion: a removed fault acknowledgement preserves a newer removal dialog at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const made = await prepare(page, width);
    const [docId, doc]: any = Object.entries(made.project.documents).find(
      ([, d]: any) => parse(d.content).kind === "Scenario",
    )!;
    const source = parse(doc.content),
      ref = `xdl://${source.metadata.namespace}/scenario/${source.metadata.name}`;
    const edited = await request(
      page,
      `/projects/${made.project.projectId}/edits`,
      "POST",
      {
        baseRevision: made.project.revision,
        edits: ["one", "two"].map((id) => ({
          kind: "add_scenario_item",
          documentId: docId,
          elementRef: ref,
          itemKind: "fault",
          itemId: "removal-" + id,
          properties: {
            targetRef: source.spec.steps[0].targetRef,
            faultKind: "provider-defined",
            activation: "Opaque intent only",
            recovery: "Opaque intent only",
            maturity: "prototype",
          },
        })),
      },
      made.project.revision,
    );
    await page.reload();
    await page.getByRole("tab", { name: "Experiments", exact: true }).focus();
    await page.keyboard.press("Enter");
    let release!: () => void,
      ready = false,
      committed: any;
    const gate = new Promise<void>((resolve) => (release = resolve));
    await page.route(
      `**/api/v1/projects/${made.project.projectId}/edits`,
      async (route) => {
        const response = await route.fetch({ timeout: 30000 });
        committed = await response.json();
        ready = true;
        await gate;
        await route.fulfill({ response });
      },
    );
    try {
      await page
        .getByRole("button", { name: "Remove fault removal-one", exact: true })
        .focus();
      await page.keyboard.press("Enter");
      await page
        .getByRole("button", { name: "Remove draft item", exact: true })
        .focus();
      await page.keyboard.press("Enter");
      await expect.poll(() => ready, { timeout: 30000 }).toBe(true);
      await page.keyboard.press("Escape");
      await page
        .getByRole("button", { name: "Remove fault removal-two", exact: true })
        .focus();
      await page.keyboard.press("Enter");
      const keep = page.getByRole("button", { name: "Keep item", exact: true });
      await keep.focus();
      release();
      await expect(page.locator(".project-header .revision")).toHaveText(
        "rev " + committed.revision,
      );
      await expect(page.getByRole("dialog")).toContainText("#removal-two");
      await expect(keep).toBeFocused();
      expect(committed.revision).toBe(edited.revision + 1);
      const saved = await request(page, `/projects/${made.project.projectId}`),
        actual = parse(saved.documents[docId].content);
      expect(actual.spec.faults.map((f: any) => f.id)).toEqual(["removal-two"]);
      expect(
        (await request(page, `/runs/${made.run.runId}/snapshot`)).snapshot,
      ).toEqual(made.snapshot);
      await page.keyboard.press("Escape");
    } finally {
      release();
    }
  });
}
