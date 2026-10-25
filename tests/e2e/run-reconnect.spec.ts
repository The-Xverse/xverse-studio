import { test, expect, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";
import { connectStudio } from "./connect-studio";
/** Fault injection cancels only the actual browser GET; no server records or lifecycle are replaced. */
async function installReadDisconnect(page: Page) {
  await page.addInitScript(() => {
    const original = window.fetch.bind(window),
      active = new Set<AbortController>(),
      waiting = new Set<() => void>();
    let paused = false;
    window.addEventListener("studio.test.pause-delivery", () => {
      paused = true;
      for (const controller of active) controller.abort();
      active.clear();
    });
    window.addEventListener("studio.test.resume-delivery", () => {
      paused = false;
      for (const resume of waiting) resume();
      waiting.clear();
    });
    window.fetch = async (input, init) => {
      const url =
        typeof input === "string"
          ? input
          : input instanceof URL
            ? input.href
            : input.url;
      if (url.includes("/events?") && url.includes("streamVersion=1.1")) {
        if (paused)
          await new Promise<void>((resolve, reject) => {
            const cleanup = () => {
              waiting.delete(resume);
              init?.signal?.removeEventListener("abort", abort);
            };
            const resume = () => {
              cleanup();
              resolve();
            };
            const abort = () => {
              cleanup();
              reject(
                new DOMException(
                  "Disposed paused browser delivery",
                  "AbortError",
                ),
              );
            };
            waiting.add(resume);
            init?.signal?.addEventListener("abort", abort, { once: true });
            if (init?.signal?.aborted) abort();
          });
        const controller = new AbortController();
        active.add(controller);
        return original(input, {
          ...init,
          signal: init?.signal
            ? AbortSignal.any([init.signal, controller.signal])
            : controller.signal,
        });
      }
      return original(input, init);
    };
  });
}
async function delivery(page: Page, paused: boolean) {
  await page.evaluate(
    (paused) =>
      window.dispatchEvent(
        new Event(
          paused ? "studio.test.pause-delivery" : "studio.test.resume-delivery",
        ),
      ),
    paused,
  );
}
async function makeProject(page: Page, name: string) {
  return page.evaluate(async (name) => {
    const session = await fetch("/api/v1/session").then((r) => r.json());
    const r = await fetch("/api/v1/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": session.csrfToken,
      },
      body: JSON.stringify({ name }),
    });
    if (!r.ok) throw Error(await r.text());
    return r.json();
  }, name);
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
test("run session: unknown recorded state awaits actual bounded resync and reconnects read-only", async ({
  page,
}, testInfo) => {
  test.setTimeout(90000);
  await installReadDisconnect(page);
  await connectStudio(page, testInfo);
  const project = await makeProject(
    page,
    "Unknown-state stream recovery fixture",
  );
  const fixture = JSON.parse(
    execFileSync(
      path.resolve(".venv/bin/python"),
      [
        "tests/fixtures/evidence/create_stream_recovery_fixture.py",
        "--data-dir",
        process.env.STUDIO_BROWSER_DATA!,
        "--project-id",
        project.projectId,
      ],
      { encoding: "utf8" },
    ),
  );
  await testInfo.attach("recorded-fixture-scope", {
    body: JSON.stringify(fixture),
    contentType: "application/json",
  });
  const writes: string[] = [],
    streams: string[] = [];
  page.on("request", (r) => {
    if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
      writes.push(r.method() + " " + r.url());
    if (r.url().includes(`/runs/${fixture.runId}/events`))
      streams.push(r.url());
  });
  let release!: () => void,
    entered = false;
  let recovery: any;
  const gate = new Promise<void>((resolve) => (release = resolve));
  await page.route(`**/api/v1/runs/${fixture.runId}/resync`, async (route) => {
    const response = await route.fetch();
    recovery = await response.json();
    entered = true;
    await gate;
    try {
      await route.fulfill({ response });
    } catch {
      /* disposed obsolete read */
    }
  });
  try {
    await showRun(page, project.projectId, fixture.runId);
    await expect.poll(() => entered, { timeout: 8000 }).toBe(true);
    await expect(page.locator(".stream-indicator")).toContainText(
      "Resynchronizing",
    );
    await expect(
      page.getByText(/State and retained history resynchronization is pending/),
    ).toBeVisible();
    await expect(
      page.getByText(
        /Current run state and a bounded history tail were resynchronized/,
      ),
    ).toHaveCount(0);
    expect(recovery.history.items.length).toBe(200);
    expect(recovery.history.omittedRecords).toBe(fixture.recordCount - 200);
    expect(recovery.run.state).toBe("unknown");
    release();
    await expect(
      page.getByText(
        /Current run state and a bounded history tail were resynchronized/,
      ),
    ).toBeVisible();
    await expect(
      page.getByText(
        `${fixture.recordCount - 200} presentation record(s) are unavailable in this delivery interval.`,
        { exact: false },
      ),
    ).toBeVisible();
    await expect(page.locator(".stream-indicator")).toHaveText("Connected");
    await page
      .getByRole("tab", { name: "Events & logs", exact: false })
      .click();
    await page
      .getByRole("button", { name: "Live buffer · at most 200", exact: true })
      .click();
    await expect(page.locator(".event-row")).toHaveCount(200);
    await expect(
      page.getByText(
        `${fixture.recordCount - 200} earlier display event(s) omitted or unavailable.`,
        { exact: false },
      ),
    ).toBeVisible();
    const ids = await page
      .locator(".event-row")
      .evaluateAll((els) => els.map((e) => e.getAttribute("data-event-id")));
    expect(new Set(ids).size).toBe(200);
    const before = streams.length;
    await delivery(page, true);
    await expect(page.locator(".stream-indicator")).not.toHaveText("Connected");
    await delivery(page, false);
    await expect.poll(() => streams.length).toBeGreaterThan(before);
    await expect(page.locator(".stream-indicator")).toHaveText("Connected");
    expect(
      streams
        .slice(1)
        .some(
          (url) =>
            new URL(url).searchParams.get("after") === recovery.resumeCursor,
        ),
    ).toBe(true);
    const detail = await page.request
      .get(`/api/v1/runs/${fixture.runId}`)
      .then((r) => r.json());
    expect(detail.state).toBe("unknown");
    expect(detail.capabilities).toEqual([]);
    expect(detail.evidenceScope).toBe("recorded_fixture");
    await testInfo.attach("read-only-stream-requests", {
      body: JSON.stringify({
        streams,
        writes,
        fault:
          "Explicit browser fetch cancellation; all server frames and resync data remain actual native API responses.",
      }),
      contentType: "application/json",
    });
    expect(writes).toEqual([]);
    await page.screenshot({
      path: testInfo.outputPath("unknown-read-only-recovery.png"),
      fullPage: true,
    });
  } finally {
    release();
    await delivery(page, false);
  }
});

test("run session: native owned execution survives real replay-window expiry while running without duplicate Start", async ({
  page,
}, testInfo) => {
  const diagnosticStart = Date.now(),
    phases: Record<string, unknown>[] = [],
    requestPhases: Record<string, unknown>[] = [];
  const observe = (phase: string, facts: Record<string, unknown> = {}) => {
    if (phases.length < 128)
      phases.push({ phase, elapsedMs: Date.now() - diagnosticStart, ...facts });
  };
  const tracked = new Map<
    import("@playwright/test").Request,
    Record<string, unknown>
  >();
  const onRequest = (request: import("@playwright/test").Request) => {
    const parsed = new URL(request.url());
    if (
      !parsed.pathname.startsWith("/api/v1/runs") &&
      !parsed.pathname.startsWith("/api/v1/projects")
    )
      return;
    const row = {
      method: request.method(),
      path: parsed.pathname,
      after: parsed.searchParams.get("after"),
      startedMs: Date.now() - diagnosticStart,
    };
    if (requestPhases.length < 256) {
      requestPhases.push(row);
      tracked.set(request, row);
    }
  };
  const onResponse = (response: import("@playwright/test").Response) => {
    const row = tracked.get(response.request());
    if (row)
      Object.assign(row, {
        status: response.status(),
        responseMs: Date.now() - diagnosticStart,
      });
  };
  const onFinished = (request: import("@playwright/test").Request) => {
    const row = tracked.get(request);
    if (row) Object.assign(row, { finishedMs: Date.now() - diagnosticStart });
  };
  const onFailed = (request: import("@playwright/test").Request) => {
    const row = tracked.get(request);
    if (row)
      Object.assign(row, {
        failedMs: Date.now() - diagnosticStart,
        failure: request.failure()?.errorText,
      });
  };
  page.on("request", onRequest);
  page.on("response", onResponse);
  page.on("requestfinished", onFinished);
  page.on("requestfailed", onFailed);
  try {
    test.setTimeout(90000);
    const durationSeconds = 30;
    await installReadDisconnect(page);
    await connectStudio(page, testInfo);
    const project = await makeProject(page, "Owned read-only reconnect");
    const made = await page.evaluate(
      async ({ project, durationSeconds }) => {
        const { csrfToken } = await fetch("/api/v1/session").then((r) =>
          r.json(),
        );
        const post = async (
          path: string,
          body: any,
          revision?: number,
          key?: string,
        ) => {
          const r = await fetch("/api/v1" + path, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": csrfToken,
              ...(revision ? { "If-Match": String(revision) } : {}),
              ...(key ? { "Idempotency-Key": key } : {}),
            },
            body: JSON.stringify(body),
          });
          if (!r.ok) throw Error(await r.text());
          return r.json();
        };
        const changed = await post(
          `/projects/${project.projectId}/edits`,
          {
            baseRevision: project.revision,
            edits: [
              {
                kind: "set_parameter",
                parameterId: "duration",
                value: durationSeconds,
              },
              { kind: "set_parameter", parameterId: "timestep", value: 0.01 },
            ],
          },
          project.revision,
        );
        const pf = await post(`/projects/${project.projectId}/preflights`, {
          revision: changed.revision,
        });
        const key = crypto.randomUUID();
        return {
          start: await post(
            "/runs",
            { snapshotId: pf.snapshotId, preflightId: pf.preflightId },
            undefined,
            key,
          ),
          key,
          snapshotId: pf.snapshotId,
        };
      },
      { project, durationSeconds },
    );
    const acknowledgedAt = Date.now();
    observe("start_acknowledged", {
      runId: made.start.runId,
      durationSeconds,
      expectedSamples: 3000,
    });
    const runId = made.start.runId,
      writes: string[] = [],
      streams: string[] = [];
    page.on("request", (r) => {
      if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
        writes.push(r.method() + " " + r.url());
      if (r.url().includes(`/runs/${runId}/events`)) streams.push(r.url());
    });
    const expiredResponses: any[] = [];
    page.on("response", (response) => {
      if (
        response.url().includes(`/runs/${runId}/events`) &&
        response.status() === 410
      ) {
        const entry: any = { url: response.url(), status: response.status() };
        expiredResponses.push(entry);
        observe("http_410_observed", { url: response.url() });
        void response
          .json()
          .then((body) => {
            entry.code = body.code;
          })
          .catch(() => {
            entry.bodyUnavailable = true;
          });
      }
    });
    const journalPath = path.join(
        process.env.STUDIO_BROWSER_DATA!,
        "runs",
        runId,
        "evidence.jsonl",
      ),
      snapshotPath = path.join(
        process.env.STUDIO_BROWSER_DATA!,
        "snapshots",
        made.snapshotId,
        "snapshot.json",
      );
    const sha = (bytes: Buffer) =>
      createHash("sha256").update(bytes).digest("hex");
    const snapshotHash = sha(readFileSync(snapshotPath));
    const prefixRecoveries: any[] = [];
    await page.route(`**/api/v1/runs/${runId}/resync`, async (route) => {
      const response = await route.fetch();
      const recovery = await response.json();
      observe("resync_response", {
        integrity: recovery.history?.integrity,
        state: recovery.run?.state,
        afterExpiry: expiredResponses.length,
      });
      prefixRecoveries.push({
        integrity: recovery.history?.integrity,
        state: recovery.run?.state,
        resumeCursor: recovery.resumeCursor,
        afterExpiry: expiredResponses.length,
      });
      await route.fulfill({ response });
    });
    observe("loading_run_view");
    await showRun(page, project.projectId, runId);
    observe("run_view_ready");
    await expect(page.locator(".stream-indicator")).toHaveText("Connected");
    await page
      .getByRole("tab", { name: "Events & logs", exact: false })
      .click();
    await page
      .getByRole("button", { name: "Live buffer · at most 200", exact: true })
      .click();
    await expect
      .poll(() => page.locator(".event-row").count())
      .toBeGreaterThan(2);
    const before = await page.request
      .get(`/api/v1/runs/${runId}/history?limit=200`)
      .then((r) => r.json());
    const initialJournal = readFileSync(journalPath),
      prefixBytes = initialJournal.subarray(
        0,
        initialJournal.lastIndexOf(10) + 1,
      ),
      prefixHash = sha(prefixBytes);
    observe("pause_requested", { records: before.counts.totalRecords });
    await delivery(page, true);
    await expect
      .poll(() =>
        prefixRecoveries.some(
          (r) => r.integrity === "verified_prefix" && r.state === "running",
        ),
      )
      .toBe(true);
    await expect(
      page.getByText(/Reader integrity: verified_prefix/),
    ).toBeVisible();
    observe("pause_started_after_initial_recovery");
    await new Promise((resolve) => setTimeout(resolve, 12000));
    observe("pause_completed");
    await delivery(page, false);
    const during = await page.request
      .get(`/api/v1/runs/${runId}/history?limit=200`)
      .then((r) => r.json());
    observe("during_history_received", { records: during.counts.totalRecords });
    expect(
      during.counts.totalRecords - before.counts.totalRecords,
    ).toBeGreaterThan(1000);
    await expect
      .poll(() => expiredResponses.length, { timeout: 4000 })
      .toBeGreaterThan(0);
    await expect
      .poll(
        () =>
          prefixRecoveries.some(
            (r) =>
              r.afterExpiry > 0 &&
              r.integrity === "verified_prefix" &&
              r.state === "running",
          ),
        { timeout: 4000 },
      )
      .toBe(true);
    await expect(
      page.getByText(/Reader integrity: verified_prefix/),
    ).toBeVisible();
    await expect.poll(() => streams.length).toBeGreaterThan(1);
    const remainingHorizonMs = Math.max(
      0,
      acknowledgedAt + durationSeconds * 1000 - Date.now(),
    );
    observe("declared_execution_horizon_wait", { remainingHorizonMs });
    // Wait the requested fixture's execution horizon, then retain the existing 10s terminal assertion budget.
    await new Promise((resolve) => setTimeout(resolve, remainingHorizonMs));
    await expect
      .poll(async () =>
        page.request
          .get(`/api/v1/runs/${runId}`)
          .then((r) => r.json())
          .then((r) => r.state),
      )
      .toBe("stopped");
    await page.reload();
    await page.getByRole("tab", { name: "Results", exact: false }).click();
    await expect(
      page.getByRole("heading", { name: /Run results/ }),
    ).toContainText("stopped");
    await expect(page.locator(".stream-indicator")).toHaveText(
      "Retained history available",
    );
    const list = await page.request.get("/api/v1/runs").then((r) => r.json());
    expect(
      list.items.filter((r: any) => r.projectId === project.projectId),
    ).toHaveLength(1);
    const finalJournal = readFileSync(journalPath);
    const finalObservations = finalJournal
      .toString("utf8")
      .trim()
      .split("\n")
      .map((line) => JSON.parse(line))
      .filter((record) => record.type === "observation.available");
    expect(finalObservations).toHaveLength(3000);
    expect(finalObservations.at(-1).sourceTime.tick).toBe("29990000");
    observe("final_sample_budget_verified", {
      observations: finalObservations.length,
    });
    expect(sha(finalJournal.subarray(0, prefixBytes.length))).toBe(prefixHash);
    expect(sha(readFileSync(snapshotPath))).toBe(snapshotHash);
    const finalRun = await page.request
      .get(`/api/v1/runs/${runId}`)
      .then((r) => r.json());
    expect(finalRun.journalDigest).toBe("sha256:" + sha(finalJournal));
    expect(finalRun.providerId).toBe("studio.reference");
    expect(finalRun.evidenceScope).toBe("owned_reference");
    await testInfo.attach("actual-window-expiry", {
      body: JSON.stringify({
        expiredResponses,
        sourceRecordsBefore: before.counts.totalRecords,
        sourceRecordsDuringPause: during.counts.totalRecords,
        pauseMilliseconds: 12000,
        requestedDurationSeconds: durationSeconds,
        timestepSeconds: 0.01,
        prefixByteLength: prefixBytes.length,
        prefixSha256: prefixHash,
        snapshotSha256: snapshotHash,
        finalJournalSha256: sha(finalJournal),
        readOnly: true,
      }),
      contentType: "application/json",
    });
    await testInfo.attach("active-prefix-recovery", {
      body: JSON.stringify(prefixRecoveries),
      contentType: "application/json",
    });
    expect(writes).toEqual([]);
    expect(
      streams.every(
        (url) => new URL(url).searchParams.get("streamVersion") === "1.1",
      ),
    ).toBe(true);
    expect(
      streams
        .slice(1)
        .some((url) =>
          new URL(url).searchParams.get("after")?.startsWith("st1."),
        ),
    ).toBe(true);
    await page.screenshot({
      path: testInfo.outputPath("owned-run-after-disconnect-refresh.png"),
      fullPage: true,
    });
  } finally {
    page.off("request", onRequest);
    page.off("response", onResponse);
    page.off("requestfinished", onFinished);
    page.off("requestfailed", onFailed);
    await testInfo.attach("native-expiry-phase-diagnostics", {
      body: JSON.stringify({
        scope: "passive native fixture phases; no assertion timeout increase",
        elapsedMs: Date.now() - diagnosticStart,
        phases,
        requests: requestPhases,
      }),
      contentType: "application/json",
    });
  }
});

test("run session: UI metadata fixture updates evidence at the same lifecycle version without altering evidence", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await makeProject(
    page,
    "Same-version evidence UI metadata fixture",
  );
  const fixture = JSON.parse(
    execFileSync(
      path.resolve(".venv/bin/python"),
      [
        "tests/fixtures/evidence/create_stream_recovery_fixture.py",
        "--data-dir",
        process.env.STUDIO_BROWSER_DATA!,
        "--project-id",
        project.projectId,
        "--noise",
        "1000",
      ],
      { encoding: "utf8" },
    ),
  );
  const journalPath = path.join(
      process.env.STUDIO_BROWSER_DATA!,
      "runs",
      fixture.runId,
      "evidence.jsonl",
    ),
    snapshotPath = path.join(
      process.env.STUDIO_BROWSER_DATA!,
      "snapshots",
      fixture.snapshotId,
      "snapshot.json",
    ),
    sha = (p: string) =>
      createHash("sha256").update(readFileSync(p)).digest("hex");
  const journalHash = sha(journalPath),
    snapshotHash = sha(snapshotPath);
  let facet = "partial";
  const versions: number[] = [],
    writes: string[] = [];
  await page.route(`**/api/v1/runs/${fixture.runId}`, async (route) => {
    const response = await route.fetch(),
      metadata = await response.json();
    versions.push(metadata.stateVersion);
    await route.fulfill({ response, json: { ...metadata, evidence: facet } });
  });
  page.on("request", (r) => {
    if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
      writes.push(r.method() + " " + r.url());
  });
  await showRun(page, project.projectId, fixture.runId);
  await expect(page.locator(".stream-indicator")).toHaveText("Connected");
  const evidence = page
      .locator(".status-card")
      .filter({ has: page.getByText("Evidence", { exact: true }) }),
    execution = page
      .locator(".status-card")
      .filter({ has: page.getByText("Execution", { exact: true }) });
  await expect(evidence).toContainText(/partial/i);
  await expect(execution).toContainText(/unknown/i);
  facet = "invalid";
  await expect(evidence).toContainText(/invalid/i, { timeout: 8000 });
  await expect(execution).toContainText(/unknown/i);
  facet = "unavailable";
  await expect(evidence).toContainText(/unavailable/i, { timeout: 8000 });
  await expect(execution).toContainText(/unknown/i);
  expect(new Set(versions).size).toBe(1);
  expect(sha(journalPath)).toBe(journalHash);
  expect(sha(snapshotPath)).toBe(snapshotHash);
  const actual = await page.request
    .get(`/api/v1/runs/${fixture.runId}`)
    .then((r) => r.json());
  expect(actual.evidence).toBe("partial");
  expect(actual.stateVersion).toBe(versions[0]);
  expect(writes).toEqual([]);
  await testInfo.attach("same-version-ui-negative-scope", {
    body: JSON.stringify({
      scope:
        "controlled HTTP metadata UI negative only; source journal and snapshot unchanged",
      evidenceScope: fixture.evidenceScope,
      requestedStates: ["partial", "invalid", "unavailable"],
      stateVersions: versions,
      journalSha256: journalHash,
      snapshotSha256: snapshotHash,
      backendEvidence: actual.evidence,
      mutations: writes,
    }),
    contentType: "application/json",
  });
  await page.screenshot({
    path: testInfo.outputPath(
      "same-version-evidence-unavailable-ui-fixture.png",
    ),
    fullPage: true,
  });
});
