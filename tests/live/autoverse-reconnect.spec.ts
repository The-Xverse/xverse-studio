import { test, expect } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";

const mode = process.env.STUDIO_AUTOVERSE_RECONNECT_CASE;
test(`actual Autoverse ${mode}: Start acceptance and execution outcomes remain distinct`, async ({ page }, info) => {
  const data = process.env.STUDIO_BROWSER_DATA;
  if (!data || !["startup-failure", "runtime-failure"].includes(String(mode)))
    throw Error("Explicit native Autoverse failure controller required");
  if (mode === "runtime-failure") test.setTimeout(720000);
  await connectStudio(page, info);
  const sources = JSON.parse(readFileSync(path.join(data, "author-inputs.private.json"), "utf8"));
  const made = await page.evaluate(async (sources: Record<string, string>) => {
    const session = await fetch("/api/v1/session").then(r => r.json());
    const headers = { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken };
    const post = async (url: string, body: unknown, key?: string) => {
      const response = await fetch("/api/v1" + url, { method: "POST", headers: { ...headers, ...(key ? { "Idempotency-Key": key } : {}) }, body: JSON.stringify(body) });
      if (!response.ok) throw Error(`${url}: ${response.status}`);
      return { status: response.status, value: await response.json() };
    };
    let project = (await post("/projects", { name: "Autoverse accepted Start failure", blueprintRef: "autoverse-classic" })).value;
    for (const [id, document] of Object.entries(project.documents) as [string, {path: string; content: string}][]) {
      const content = sources[document.path.split("/").at(-1)!];
      if (content !== document.content) {
        const response = await fetch(`/api/v1/projects/${project.projectId}/documents/${id}`, { method: "PUT", headers: { ...headers, "If-Match": String(project.revision) }, body: JSON.stringify({ content, format: "yaml" }) });
        if (!response.ok) throw Error("Supported Autoverse source variant could not be saved");
        project = await response.json();
      }
    }
    const pf = (await post(`/projects/${project.projectId}/preflights`, { revision: project.revision, providerId: "autoverse.demo" })).value;
    if (pf.status !== "ready") throw Error("Actual Autoverse preflight unavailable");
    const key = crypto.randomUUID();
    const start = await post("/runs", { snapshotId: pf.snapshotId, preflightId: pf.preflightId }, key);
    localStorage.setItem("studio.projectId", project.projectId);
    localStorage.setItem("studio.lastRun." + project.projectId, start.value.runId);
    localStorage.setItem("studio.lastRun", start.value.runId);
    return { projectId: project.projectId, snapshotId: pf.snapshotId, runId: start.value.runId, operationId: start.value.operationId, startStatus: start.status };
  }, sources);
  expect(made.startStatus).toBe(202);
  writeFileSync(path.join(data, "browser-run.private.json"), JSON.stringify(made), { mode: 0o600, flag: "wx" });
  await page.reload();
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  await expect(page.getByRole("heading", { name: /Run results/ })).toBeVisible();
  const route = `/api/v1/runs/${made.runId}`;
  if (mode === "runtime-failure") {
    await expect.poll(async () => (await page.request.get(route).then(r => r.json())).state, { timeout: 540000 }).toBe("running");
    const running = await page.request.get(route).then(r => r.json());
    expect(running.runtimeStatus.components.android).toBe("booted_apk_started");
    expect(running.inputTelemetry.items.speed.status).toBe("observed");
    expect((await page.request.get(`/api/v1/operations/${made.operationId}`).then(r => r.json())).status).toBe("completed");
    writeFileSync(path.join(data, "browser-observed-running.private.json"), JSON.stringify({ runId: made.runId, state: "running" }), { mode: 0o600, flag: "wx" });
  }
  await expect.poll(async () => (await page.request.get(route).then(r => r.json())).state, { timeout: 90000 }).toBe("failed");
  const run = await page.request.get(route).then(r => r.json());
  const operation = await page.request.get(`/api/v1/operations/${made.operationId}`).then(r => r.json());
  expect(operation.kind).toBe("start");
  expect(operation.status).toBe(mode === "startup-failure" ? "failed" : "completed");
  expect(run.cleanup).toBe("complete");
  expect(run.evidence).toBe("partial");
  expect(run.reason).toBe(mode === "startup-failure" ? "AUTOVERSE_CARLA_NOT_READY" : "AUTOVERSE_COMPONENT_EXITED_carla");
  expect(run.verdict).toBeNull();
  const history = await page.request.get(`${route}/history?type=command.failed&limit=200`).then(r => r.json());
  expect(history.integrity).toBe("valid");
  if (mode === "runtime-failure") {
    expect(history.items).toHaveLength(0);
    await expect(page.locator(".stream-indicator")).toHaveText("Retained history available");
    await info.attach("actual-autoverse-runtime-failure", { body: JSON.stringify({ scope: "Actual complete native Autoverse reaches running before original component loss", ...made, lifecycle: run.state, cleanup: run.cleanup, evidence: run.evidence, functionalVerdict: run.verdict, originalStartStatus: operation.status, noRetroactiveStartFailureEvent: true }), contentType: "application/json" });
    return;
  }
  expect(history.items).toHaveLength(1);
  const event = history.items[0];
  expect(event.runId).toBe(made.runId);
  expect(event.snapshotId).toBe(made.snapshotId);
  expect(event.payload.operationId).toBe(made.operationId);
  expect(event.payload.kind).toBe("start");
  expect(event.payload.code).toBe(run.reason);
  expect(event.source.providerId).toBe("autoverse.demo");
  expect(event.sourceTime).toBeNull();
  // Finite terminal SSE reads preserve the same original event identity/proof.
  const response = await page.request.get(`${route}/events?streamVersion=1.1`);
  expect(response.status()).toBe(200);
  const frames = (await response.text()).split("\n\n").filter(frame => frame.includes("event: command.failed\n"));
  expect(frames).toHaveLength(1);
  const delivered = JSON.parse(frames[0].split("\n").find(line => line.startsWith("data: "))!.slice(6));
  expect(delivered).toEqual(expect.objectContaining({ eventId: event.eventId, digest: event.digest, previousDigest: event.previousDigest, sequence: event.sequence }));
  await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  await page.getByLabel("Event kind", { exact: true }).selectOption("command.failed");
  await expect(page.locator(`.event-row[data-event-id="${event.eventId}"]`).getByText("command.failed", { exact: true })).toBeVisible();
  await expect(page.locator(".stream-indicator")).toHaveText("Retained history available");
  await info.attach("actual-autoverse-start-failure", { body: JSON.stringify({ scope: "Actual native Autoverse partial startup failure; not complete-demo success", ...made, lifecycle: run.state, cleanup: run.cleanup, evidence: run.evidence, functionalVerdict: run.verdict, eventId: event.eventId, operationStatus: operation.status, originalCanonicalSseProofMatchesHistory: true }), contentType: "application/json" });
});
