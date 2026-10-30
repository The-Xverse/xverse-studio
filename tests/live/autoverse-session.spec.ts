import { test, expect, type BrowserContext, type Page } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";

/** Modify only delivery of original SSE frames, never their canonical contents. */
async function observeDelivery(context: BrowserContext) {
  await context.addInitScript(() => {
    const original = window.fetch.bind(window);
    const active = new Set<AbortController>(), waiting = new Set<() => void>();
    const d: any = { paused: false, mode: "none", blockedUrl: "", duplicates: [], reordered: [], recoveries: [], expired: [] };
    (window as any).__autoverseDelivery = d;
    window.addEventListener("autoverse.delivery", (e: any) => {
      d.mode = e.detail.mode || "none";
      d.paused = Boolean(e.detail.paused);
      if (d.paused) {
        for (const c of active) c.abort();
        active.clear();
      } else for (const resume of Array.from(waiting)) resume();
    });
    window.fetch = async (input, init) => {
      const address = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      const url = new URL(address, location.href);
      if (url.pathname.endsWith("/resync")) {
        const response = await original(input, init);
        if (response.ok) void response.clone().json().then(v => {
          d.recoveries.push({ runId: v.runId, snapshotId: v.snapshotId, watermark: v.watermark, resumeCursor: v.resumeCursor, omittedRecords: v.history.omittedRecords, retained: v.history.items.length, integrity: v.history.integrity });
          if (d.recoveries.length > 32) d.recoveries.shift();
        });
        return response;
      }
      if (!url.pathname.endsWith("/events") || url.searchParams.get("streamVersion") !== "1.1") return original(input, init);
      if (d.paused) {
        d.blockedUrl = url.href;
        await new Promise<void>((resolve, reject) => {
          const cleanup = () => { waiting.delete(resume); init?.signal?.removeEventListener("abort", abort); };
          const resume = () => { cleanup(); resolve(); };
          const abort = () => { cleanup(); reject(new DOMException("Disposed delivery hold", "AbortError")); };
          waiting.add(resume); init?.signal?.addEventListener("abort", abort, { once: true });
          if (init?.signal?.aborted) abort();
        });
      }
      const controller = new AbortController();
      active.add(controller);
      const response = await original(input, { ...init, signal: init?.signal ? AbortSignal.any([init.signal, controller.signal]) : controller.signal });
      if (response.status === 410) {
        void response.clone().json().then(v => d.expired.push(v));
        active.delete(controller); return response;
      }
      if (!response.ok || !response.body) { active.delete(controller); return response; }
      const reader = response.body.getReader(), decoder = new TextDecoder("utf-8", { fatal: true }), encoder = new TextEncoder();
      let buffer = "", held = "";
      const identity = (frame: string) => JSON.parse(frame.split("\n").find(v => v.startsWith("data: "))!.slice(6)).eventId;
      const body = new ReadableStream<Uint8Array>({
        async pull(output) {
          try {
            while (true) {
              const part = await reader.read();
              if (part.done) {
                if (held) output.enqueue(encoder.encode(held));
                if (buffer) output.enqueue(encoder.encode(buffer));
                output.close(); active.delete(controller); return;
              }
              buffer += decoder.decode(part.value, { stream: true });
              if (encoder.encode(buffer).length > 1048576) throw Error("Test delivery frame bound exceeded");
              let next: number, ready = "";
              while ((next = buffer.indexOf("\n\n")) >= 0) {
                const frame = buffer.slice(0, next + 2); buffer = buffer.slice(next + 2);
                const canonical = frame.startsWith("id: ");
                if (canonical && d.mode === "duplicate") {
                  d.duplicates.push(identity(frame)); d.mode = "none"; ready += frame + frame;
                } else if (canonical && d.mode === "reverse") {
                  if (!held) held = frame;
                  else { d.reordered.push([identity(held), identity(frame)]); d.mode = "none"; ready += frame + held; held = ""; }
                } else ready += frame;
              }
              if (ready) { output.enqueue(encoder.encode(ready)); return; }
            }
          } catch (e) { active.delete(controller); output.error(e); }
        },
        async cancel() { active.delete(controller); await reader.cancel().catch(() => {}); },
      });
      return new Response(body, { status: response.status, headers: response.headers });
    };
  });
}

async function delivery(page: Page, mode = "none", paused = false) {
  await page.evaluate(({ mode, paused }) => window.dispatchEvent(new CustomEvent("autoverse.delivery", { detail: { mode, paused } })), { mode, paused });
}

async function rows(page: Page) {
  return page.locator('.event-list[aria-label="Bounded live event buffer"] .event-row').evaluateAll(nodes => nodes.map(n => ({ id: n.getAttribute("data-event-id"), q: n.getAttribute("data-sequence")! })));
}

test("actual Autoverse browser receipts, delivery ordering and retained recovery", async ({ page, context }, info) => {
  const data = process.env.STUDIO_BROWSER_DATA!, mode = process.env.STUDIO_AUTOVERSE_RECONNECT_CASE;
  if (!data || !["session-short", "session-expiry"].includes(String(mode))) throw Error("Explicit native Autoverse session controller required");
  test.setTimeout(mode === "session-expiry" ? 2400000 : 720000);
  const progress = (stage: string, detail: any = {}) => {
    writeFileSync(path.join(data, "browser-progress.private.json"), JSON.stringify({ stage, at: Date.now(), ...detail }), { mode: 0o600 });
    console.log("AUTOVERSE_SESSION", stage, JSON.stringify(detail));
  };
  const checkpoint = async (stage: string) => {
    writeFileSync(path.join(data, "browser-checkpoint.private.json"), JSON.stringify({ stage }), { mode: 0o600 });
    await expect.poll(() => {
      try { return JSON.parse(readFileSync(path.join(data, "native-checkpoint.private.json"), "utf8")).stage; } catch { return ""; }
    }).toBe(stage);
  };
  await observeDelivery(context);
  await connectStudio(page, info);
  const sources = JSON.parse(readFileSync(path.join(data, "author-inputs.private.json"), "utf8"));
  const project = await page.evaluate(async (sources: Record<string, string>) => {
    const session = await fetch("/api/v1/session").then(r => r.json());
    const headers = { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken };
    const response = await fetch("/api/v1/projects", { method: "POST", headers, body: JSON.stringify({ name: "Autoverse browser recovery", blueprintRef: "autoverse-classic" }) });
    if (response.status !== 201) throw Error("Actual Autoverse project unavailable");
    let p = await response.json();
    for (const [id, doc] of Object.entries(p.documents) as [string, { path: string; content: string }][]) {
      const content = sources[doc.path.split("/").at(-1)!];
      if (content !== doc.content) {
        const saved = await fetch(`/api/v1/projects/${p.projectId}/documents/${id}`, { method: "PUT", headers: { ...headers, "If-Match": String(p.revision) }, body: JSON.stringify({ content, format: "yaml" }) });
        if (!saved.ok) throw Error("Supported source authoring failed");
        p = await saved.json();
      }
    }
    localStorage.setItem("studio.projectId", p.projectId);
    return p;
  }, sources);
  await page.reload();
  await expect(page.locator(".project-header h1")).toHaveText(project.name);
  const starts: { key: string; body: string }[] = [];
  const record = (tab: Page) => tab.on("request", r => {
    if (r.method() === "POST" && new URL(r.url()).pathname === "/api/v1/runs") starts.push({ key: r.headers()["idempotency-key"], body: r.postData()! });
  });
  record(page);
  let dropped = false, accepted: any;
  let retryCount = 0, releaseRetries!: () => void;
  const retriesReady = new Promise<void>(resolve => { releaseRetries = resolve; });
  await context.route("**/api/v1/runs", async route => {
    if (route.request().method() !== "POST") return route.fallback();
    const response = await route.fetch();
    if (!dropped) {
      dropped = true;
      expect(response.status()).toBe(202);
      accepted = await response.json();
      const payload = route.request().postDataJSON();
      writeFileSync(path.join(data, "browser-run.private.json"), JSON.stringify({ ...accepted, projectId: project.projectId, snapshotId: payload.snapshotId }), { mode: 0o600, flag: "wx" });
      await route.abort("connectionreset");
    } else {
      // Hold only real acknowledgements until both tabs have sent their retry.
      if (retryCount < 2) {
        retryCount++;
        if (retryCount === 2) releaseRetries();
        await retriesReady;
      }
      await route.fulfill({ response });
    }
  });
  await page.getByRole("button", { name: "Preflight & run", exact: true }).click();
  await expect(page.getByLabel("Execution provider", { exact: true })).toHaveValue("autoverse.demo");
  await page.getByRole("button", { name: "Start frozen snapshot", exact: true }).dblclick();
  await expect(page.getByText("REQUEST_UNAVAILABLE")).toBeVisible();
  await page.reload();
  await expect(page.locator("[data-pending-start]")).toHaveAttribute("data-pending-start", "unacknowledged");
  const second = await context.newPage(); record(second); await second.goto("/");
  await expect(second.getByRole("button", { name: "Retry same Start", exact: true })).toBeVisible();
  await Promise.all([page, second].map(tab => tab.getByRole("button", { name: "Retry same Start", exact: true }).click()));
  for (const tab of [page, second]) {
    await expect(tab.getByRole("heading", { name: /Run results/ })).toBeVisible();
    await expect(tab.locator(".run-identity code").first()).toHaveText(accepted.runId);
  }
  expect(starts).toHaveLength(3);
  expect(new Set(starts.map(v => v.key)).size).toBe(1);
  expect(new Set(starts.map(v => v.body)).size).toBe(1);
  const conflict = await page.evaluate(async ({ key, payload }) => {
    const s = await fetch("/api/v1/session").then(r => r.json());
    const r = await fetch("/api/v1/runs", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": s.csrfToken, "Idempotency-Key": key }, body: JSON.stringify({ ...payload, snapshotId: "different-snapshot" }) });
    return { status: r.status, body: await r.json() };
  }, { key: starts[0].key, payload: JSON.parse(starts[0].body) });
  expect(conflict.status).toBe(409); expect(conflict.body.code).toBe("IDEMPOTENCY_CONFLICT");
  await second.close();
  const route = `/api/v1/runs/${accepted.runId}`;
  const getRun = async () => page.request.get(route).then(r => r.json());
  await expect.poll(async () => (await getRun()).state, { timeout: 540000 }).toBe("running");
  const live = await getRun();
  expect(live.runtimeStatus.components.android).toBe("booted_apk_started");
  expect(live.inputTelemetry.items.speed.status).toBe("observed");
  await checkpoint("two-tab-original-worker"); progress("running", { runId: accepted.runId });
  await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  await page.getByRole("button", { name: "Live buffer · at most 200", exact: true }).click();
  await expect(page.locator(".stream-indicator")).toHaveText("Connected");
  const recoveriesBefore = await page.evaluate(() => (window as any).__autoverseDelivery.recoveries.length);
  await delivery(page, "duplicate");
  await expect.poll(() => page.evaluate(() => (window as any).__autoverseDelivery.duplicates.length), { timeout: 10000 }).toBe(1);
  const duplicate = await page.evaluate(() => (window as any).__autoverseDelivery.duplicates[0]);
  await expect(page.locator(`.event-list[aria-label="Bounded live event buffer"] .event-row[data-event-id="${duplicate}"]`)).toHaveCount(1);
  expect(await page.evaluate(() => (window as any).__autoverseDelivery.recoveries.length)).toBe(recoveriesBefore);
  await delivery(page, "reverse");
  await expect.poll(() => page.evaluate(() => (window as any).__autoverseDelivery.reordered.length), { timeout: 10000 }).toBe(1);
  await expect.poll(() => page.evaluate(() => (window as any).__autoverseDelivery.recoveries.length)).toBeGreaterThan(recoveriesBefore);
  await expect(page.locator(".stream-indicator")).toHaveText("Connected");
  const ordered = await rows(page);
  expect(new Set(ordered.map(v => v.id)).size).toBe(ordered.length);
  expect(ordered.every((v, i) => i === 0 || BigInt(v.q) > BigInt(ordered[i - 1].q))).toBe(true);
  await checkpoint("delivery-order-original-worker"); progress("delivery-order-verified");
  const beforeLoss = await page.request.get(`${route}/history?limit=1`).then(r => r.json());
  await page.close();
  await expect.poll(async () => (await context.request.get(`${route}/history?limit=1`).then(r => r.json())).counts.totalRecords).toBeGreaterThan(beforeLoss.counts.totalRecords);
  await checkpoint("all-ui-pages-closed-original-worker");
  const reopened = await context.newPage();
  const reopenedStarts: string[] = [];
  reopened.on("request", r => { if (r.method() === "POST" && new URL(r.url()).pathname === "/api/v1/runs") reopenedStarts.push(r.url()); });
  await reopened.goto("/");
  await reopened.getByRole("tab", { name: "Results", exact: false }).click();
  await expect(reopened.locator(".run-identity code").first()).toHaveText(accepted.runId);
  await expect(reopened.locator(".stream-indicator")).toHaveText("Connected");
  expect(reopenedStarts).toEqual([]);
  await checkpoint("reopened-original-worker"); progress("all-ui-loss-recovered");
  let expiryProof: any = null;
  if (mode === "session-expiry") {
    const journal = path.join(data, "runs", accepted.runId, "evidence.jsonl");
    const raw = readFileSync(journal), prefix = raw.subarray(0, raw.lastIndexOf(10) + 1);
    const prefixDigest = createHash("sha256").update(prefix).digest("hex");
    await delivery(reopened, "none", true);
    await expect.poll(() => reopened.evaluate(() => (window as any).__autoverseDelivery.blockedUrl), { timeout: 15000 }).toContain("after=st1.");
    const blocked = await reopened.evaluate(() => (window as any).__autoverseDelivery.blockedUrl);
    const token = new URL(blocked).searchParams.get("after")!;
    const cursor = JSON.parse(Buffer.from(token.slice(4), "base64url").toString());
    // Ordinary admitted controls; never exceed the256 per-run discrete budget.
    const published = await reopened.evaluate(async ({ route }) => {
      const s = await fetch("/api/v1/session").then(r => r.json());
      const headers = { "Content-Type": "application/json", "X-CSRF-Token": s.csrfToken };
      const post = async (suffix: string, value: unknown) => {
        const r = await fetch(route + "/input/" + suffix, { method: "POST", headers, body: JSON.stringify(value) });
        if (!r.ok) throw Error(`Admitted input ${suffix} failed ${r.status}`);
        return r.json();
      };
      const lease = await post("acquire", {});
      const auth = { leaseToken: lease.leaseToken, generation: lease.generation };
      let last = 0;
      for (let n = 1; n <= 256; n++) {
        const deadline = performance.now() + 700;
        while (last && (await fetch(route).then(r => r.json())).inputTelemetry.lastPublishedSequence < last) {
          if (performance.now() > deadline) throw Error("Original native publication acknowledgement missed lease bound");
          await new Promise(r => setTimeout(r, 50));
        }
        const response = await post("frame", { ...auth, frame: { sequence: n, throttle: 0, brake: 1, steer: 0, cruise: false } });
        if (response.status !== "staged") throw Error("Discrete request was not staged");
        last = response.publicationSequence;
        await new Promise(r => setTimeout(r, 60));
      }
      const finalDeadline = performance.now() + 700;
      while ((await fetch(route).then(r => r.json())).inputTelemetry.lastPublishedSequence < last) {
        if (performance.now() > finalDeadline) throw Error("Final native publication acknowledgement missed lease bound");
        await new Promise(r => setTimeout(r, 50));
      }
      await post("release", auth);
      return { count: 256, lastPublication: last };
    }, { route });
    progress("waiting-real-replay-boundary", { acknowledged: cursor.q, requiredRecords: Number(cursor.q) + 1001, published });
    await expect.poll(async () => {
      const run = await reopened.request.get(route, { maxRetries: 2 }).then(r => r.json());
      expect(run.state).toBe("running");
      const h = await reopened.request.get(`${route}/history?limit=1`, { maxRetries: 2 }).then(r => r.json());
      return h.counts.totalRecords;
    }, { timeout: 1100000, intervals: [5000] }).toBeGreaterThan(Number(cursor.q) + 1000);
    await checkpoint("expired-cursor-original-worker");
    await delivery(reopened);
    await expect.poll(() => reopened.evaluate(() => (window as any).__autoverseDelivery.expired.length), { timeout: 15000 }).toBeGreaterThan(0);
    await expect(reopened.locator(".stream-indicator")).toHaveText("Connected", { timeout: 15000 });
    expiryProof = await reopened.evaluate(() => {
      const d = (window as any).__autoverseDelivery;
      return { expired: d.expired[0], recovery: d.recoveries.at(-1) };
    });
    expect(expiryProof.expired.code).toBe("CURSOR_EXPIRED");
    expect(expiryProof.expired.missingCount).toBeGreaterThan(0);
    expect(expiryProof.recovery.runId).toBe(accepted.runId);
    expect(expiryProof.recovery.retained).toBeLessThanOrEqual(200);
    expect(expiryProof.recovery.omittedRecords).toBeGreaterThan(0);
    expect(createHash("sha256").update(readFileSync(journal).subarray(0, prefix.length)).digest("hex")).toBe(prefixDigest);
    progress("default1000-replay-recovered", { missing: expiryProof.expired.missingCount, watermark: expiryProof.recovery.watermark });
  }
  const finalRun = await reopened.request.get(route).then(r => r.json());
  expect(finalRun.state).toBe("running");
  expect(finalRun.snapshotId).toBe(live.snapshotId);
  let stopDropped = false, stopReceipt: any;
  const stops: { key: string; body: string; receipt: unknown }[] = [];
  await reopened.route(`**${route}/commands`, async r => {
    if (r.request().method() !== "POST") return r.fallback();
    const response = await r.fetch(); expect(response.status()).toBe(202);
    const receipt = await response.json();
    stops.push({ key: r.request().headers()["idempotency-key"], body: r.request().postData()!, receipt });
    if (!stopDropped) {
      stopDropped = true; stopReceipt = receipt;
      await r.abort("connectionreset");
    } else await r.fulfill({ response });
  });
  await reopened.getByRole("button", { name: "Stop", exact: true }).click();
  await expect(reopened.locator('[data-control-operation="unacknowledged"]')).toBeVisible();
  await reopened.getByRole("button", { name: "Retry same request", exact: true }).click();
  await expect.poll(async () => (await reopened.request.get(route).then(r => r.json())).state, { timeout: 90000 }).toBe("stopped");
  await expect.poll(async () => (await reopened.request.get(`/api/v1/operations/${stopReceipt.operationId}`).then(r => r.json())).status).toBe("completed");
  expect(stops).toHaveLength(2);
  expect(stops[1]).toEqual(stops[0]);
  const allRuns = await reopened.request.get("/api/v1/runs").then(r => r.json());
  expect(allRuns.items).toHaveLength(1); expect(allRuns.items[0].runId).toBe(accepted.runId);
  expect(reopenedStarts).toEqual([]);
  progress("stopped-and-reconciled", { runId: accepted.runId });
  await info.attach("actual-native-autoverse-session", { body: JSON.stringify({ scope: "Actual native complete Autoverse; delivery faults alter only original frame delivery", mode, runId: accepted.runId, snapshotId: live.snapshotId, startDeliveriesBeforeConflict: 3, sameStartKey: true, twoActualTabs: true, changedBodyConflict: true, exactDuplicateSuppressed: true, originalFrameReorderingResynchronized: true, originalWorkerNativeCheckpoints: true, allUiPagesClosedAndReopenedWithoutStart: true, stopReceiptLostAndRetried: stopReceipt.operationId, sameStopKeyBodyAndReceipt: true, expiryProof }), contentType: "application/json" });
});
