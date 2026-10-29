import { test, expect, type Page } from "@playwright/test";
import { connectStudio } from "./connect-studio";

// Presentation fixtures only. A separate approved live check verifies native/Argus updates.
async function setup(page: Page, info: Parameters<typeof connectStudio>[1]) {
  await connectStudio(page, info);
  await page.getByRole("button", { name: "X-Verse Studio home", exact: true }).click();
  await page.locator(".example-grid").getByRole("button").first().click();
  await page.getByRole("button", { name: "Preflight & run", exact: true }).click();
  await page.getByRole("button", { name: "Start frozen snapshot", exact: true }).click();
  await expect.poll(() => page.evaluate(() => localStorage.getItem("studio.lastRun"))).toBeTruthy();
  const runId = (await page.evaluate(() => localStorage.getItem("studio.lastRun")))!;
  const state = { fresh: 0, fail: false, hold: false, release: () => {}, requests: [] as URL[] };
  await page.route(`**/api/v1/runs/${runId}/platform?*`, async route => {
    const url = new URL(route.request().url());
    state.requests.push(url);
    const snapshot = url.searchParams.get("snapshot") || `fixture-${++state.fresh}`;
    const ordinal = Number(snapshot.split("-").at(-1));
    if (!url.searchParams.has("snapshot") && state.hold) {
      state.hold = false;
      await new Promise<void>(resolve => { state.release = resolve; });
    }
    if (!url.searchParams.has("snapshot") && state.fail) {
      state.fail = false;
      return route.fulfill({ status: 503, json: { message: "Controlled evidence outage" } });
    }
    const sourceRef = { sourceId: "presentation-fixture", runId, eventId: "fixture", ingestionOrdinal: 1 };
    const rows = Array.from({ length: 70 }, (_, index) => ({
      eventId: `fixture-${ordinal}-record-${index}`, ingestionOrdinal: ordinal * 1000 + index,
      eventKind: "observation", producerId: "presentation-fixture", sourceRef,
      correlationId: "fixture-correlation", causationId: "fixture-original-input",
      clocks: { source: { domain: "fixture-unmapped", unit: "ns", value: ordinal * 1000 + index } },
      communication: { routeId: "fixture-route", endpointId: "fixture-endpoint", schemaId: "fixture-scalar",
        counters: { coalesced: ordinal }, payload: { policy: "fixture-only", value: String(ordinal) } },
    }));
    if (url.searchParams.get("order") === "newest") rows.reverse();
    const filtered = url.searchParams.has("eventId") ? [{ ...rows[0], eventId: "fixture-original-input",
      communication: undefined, input: { routeId: "fixture-route", endpointId: "fixture-endpoint", upstreamCausationId: null } }] : rows;
    const offset = url.searchParams.has("cursor") ? 50 : 0;
    await route.fulfill({ json: {
      snapshotId: snapshot, sourceId: "presentation-fixture", sourceWitness: `fixture-witness-${ordinal}`,
      capturedAt: Date.now() / 1000, expiresInSeconds: 300, identity: { runId },
      identityVerified: { runAndPlan: false, maestroInputs: false, installation: "fixture" },
      evidence: { recorded: "incomplete", assessed: "incomplete", recordedReasons: [], assessedReasons: [] },
      diagnostics: [], policy: { scope: "presentation-only" }, order: url.searchParams.get("order"),
      counts: { orchestration: 0, communications: 70, retained: 70 }, matchedCount: filtered.length,
      offset, nextCursor: offset === 0 && filtered.length > 50 ? "fixture-next" : null,
      items: filtered.slice(offset, offset + 50),
    } }).catch(() => {}); // A deliberately aborted held response may already be disposed.
  });
  await page.getByRole("tab", { name: "Communications", exact: true }).click();
  const panel = page.getByRole("region", { name: "Linked platform views", exact: true });
  await expect(panel.getByText("Scalar: 1", { exact: true }).first()).toBeVisible();
  await page.clock.install({ time: new Date() });
  await page.clock.pauseAt(new Date(Date.now() + 1000));
  const begin = async () => {
    await panel.getByRole("checkbox", { name: "Follow live", exact: true }).check();
    await expect(panel.getByText(`Scalar: ${state.fresh}`, { exact: true }).first()).toBeVisible();
    await expect(panel.getByText("Reading platform evidence…", { exact: true })).toHaveCount(0);
  };
  const finish = async () => {
    state.release();
    const actual = await (await page.request.get(`/api/v1/runs/${runId}`)).json();
    if (["accepted", "preparing", "running"].includes(actual.state)) {
      const session = await (await page.request.get("/api/v1/session")).json();
      await page.request.post(`/api/v1/runs/${runId}/commands`, {
        headers: { Origin: new URL(page.url()).origin, "X-CSRF-Token": session.csrfToken,
          "Idempotency-Key": `fixture-cleanup-${runId}` },
        data: { kind: "stop", expectedStateVersion: actual.stateVersion },
      });
    }
  };
  return { state, panel, begin, finish };
}

test("platform live follow refreshes newest samples and pins causal navigation", async ({ page }, info) => {
  const { state, panel, begin, finish } = await setup(page, info);
  try {
    await begin();
    const first = state.fresh;
    await page.clock.runFor(2200);
    await expect.poll(() => state.fresh).toBe(first + 1);
    await expect(panel.getByText(`Scalar: ${first + 1}`, { exact: true }).first()).toBeVisible();
    expect(state.requests.at(-1)?.searchParams.get("order")).toBe("newest");
    const pinned = state.requests.at(-1)?.searchParams.get("snapshot") || `fixture-${state.fresh}`;
    await panel.getByRole("button", { name: "Original cause", exact: true }).first().click();
    await expect(panel.getByRole("heading", { name: "Evidence · X-Verse platform", exact: true })).toBeFocused();
    await expect(panel.getByRole("checkbox", { name: "Follow live", exact: true })).not.toBeChecked();
    expect(state.requests.at(-1)?.searchParams.get("snapshot")).toBe(pinned);
    await page.clock.runFor(7000);
    expect(state.fresh).toBe(first + 1);
  } finally { await finish(); }
});

test("platform live follow retains data on error and pauses off tab or hidden", async ({ page }, info) => {
  const { state, panel, begin, finish } = await setup(page, info);
  try {
    await begin();
    const current = state.fresh;
    state.fail = true;
    await page.clock.runFor(2200);
    await expect(panel.getByRole("alert")).toHaveText("Controlled evidence outage");
    await expect(panel.getByText(`Scalar: ${current}`, { exact: true }).first()).toBeVisible();
    await page.clock.runFor(2200);
    await expect(panel.getByText(`Scalar: ${current + 2}`, { exact: true }).first()).toBeVisible();
    await page.evaluate(() => { Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" }); document.dispatchEvent(new Event("visibilitychange")); });
    const before = state.fresh;
    await page.clock.runFor(8000);
    expect(state.fresh).toBe(before);
    await page.evaluate(() => { Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" }); document.dispatchEvent(new Event("visibilitychange")); });
    await page.clock.runFor(2200);
    await expect.poll(() => state.fresh).toBe(before + 1);
    await expect(panel.getByText("Reading platform evidence…", { exact: true })).toHaveCount(0);
    await page.getByRole("tab", { name: "Observations", exact: true }).click();
    await page.clock.runFor(8000);
    expect(state.fresh).toBe(before + 1);
  } finally { await finish(); }
});

test("platform live follow serializes slow reads and rejects a late reply after pause", async ({ page }, info) => {
  const { state, panel, begin, finish } = await setup(page, info);
  try {
    await begin();
    const pinned = state.fresh;
    state.hold = true;
    await page.clock.runFor(2200);
    await expect.poll(() => state.fresh).toBe(pinned + 1);
    await page.clock.runFor(5000);
    expect(state.fresh).toBe(pinned + 1);
    await expect(panel.getByText(`Scalar: ${pinned}`, { exact: true }).first()).toBeVisible();
    await panel.getByRole("checkbox", { name: "Follow live", exact: true }).uncheck();
    state.release();
    await page.clock.runFor(5000);
    await expect(panel.getByText(`Scalar: ${pinned}`, { exact: true }).first()).toBeVisible();
    expect(state.fresh).toBe(pinned + 1);
  } finally { await finish(); }
});

test("platform live follow bounds a stalled read and retries without losing the last capture", async ({ page }, info) => {
  const { state, panel, begin, finish } = await setup(page, info);
  try {
    await begin();
    const pinned = state.fresh;
    state.hold = true;
    await page.clock.runFor(2200);
    await expect.poll(() => state.fresh).toBe(pinned + 1);
    await page.clock.runFor(10100);
    await expect(panel.getByRole("alert")).toContainText("read timed out");
    await expect(panel.getByText(`Scalar: ${pinned}`, { exact: true }).first()).toBeVisible();
    state.release();
    await page.clock.runFor(2200);
    await expect(panel.getByText(`Scalar: ${pinned + 2}`, { exact: true }).first()).toBeVisible();
  } finally { await finish(); }
});

test("platform live follow captures the terminal state once then stops polling", async ({ page }, info) => {
  const { state, panel, begin, finish } = await setup(page, info);
  try {
    await begin();
    const before = state.fresh;
    await page.getByRole("region", { name: "Run controls", exact: true }).getByRole("button", { name: "Stop", exact: true }).click();
    await page.clock.runFor(2400);
    await expect(panel.getByRole("checkbox", { name: "Follow live", exact: true })).toBeDisabled();
    await expect.poll(() => state.fresh).toBeGreaterThan(before);
    await expect(panel.getByText("Reading platform evidence…", { exact: true })).toHaveCount(0);
    const terminal = state.fresh;
    await page.clock.runFor(8000);
    expect(state.fresh).toBe(terminal);
    await expect(panel.getByRole("checkbox", { name: "Follow live", exact: true })).not.toBeChecked();
  } finally { await finish(); }
});
