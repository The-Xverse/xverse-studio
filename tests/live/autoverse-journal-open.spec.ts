import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";

test("actual Autoverse journal-opening failure exposes known startup and separate integrity", async ({ page, context }, info) => {
  const data = process.env.STUDIO_BROWSER_DATA;
  if (!data) throw Error("Explicit native journal-opening controller required");
  const original = JSON.parse(readFileSync(path.join(data, "journal-open-browser.private.json"), "utf8"));
  await context.addInitScript(({ projectId, runId }) => {
    localStorage.setItem("studio.projectId", projectId);
    localStorage.setItem("studio.lastRun." + projectId, runId);
    localStorage.setItem("studio.lastRun", runId);
  }, original);
  const mutations: string[] = [];
  page.on("request", r => { if (r.method() === "POST" && new URL(r.url()).pathname.startsWith("/api/v1/runs")) mutations.push(r.url()); });
  await connectStudio(page, info);
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  await expect(page.locator(".run-identity code").first()).toHaveText(original.runId);
  const startup = page.getByRole("region", { name: "Reported startup", exact: true });
  await expect(startup.getByText("Startup rejected", { exact: true })).toBeVisible();
  await expect(startup).toContainText("could not create its canonical evidence journal and did not start the workload");
  await expect(startup).toContainText("check local storage access and capacity");
  await expect(startup.getByText("EVIDENCE_OPEN_FAILED", { exact: true })).toBeVisible();
  await expect(page.locator(".stream-indicator")).toHaveText("Retained history available");
  const evidence = page.locator(".result-status-grid > *").filter({ has: page.getByText("Evidence", { exact: true }) });
  await expect(evidence.getByText("invalid", { exact: true })).toBeVisible();
  const run = await page.request.get(`/api/v1/runs/${original.runId}`).then(r => r.json());
  expect(run.state).toBe("failed"); expect(run.cleanup).toBe("complete"); expect(run.evidence).toBe("invalid"); expect(run.verdict).toBeNull();
  const operation = await page.request.get(`/api/v1/operations/${original.operationId}`).then(r => r.json());
  expect(operation.status).toBe("failed"); expect(operation.kind).toBe("start"); expect(mutations).toEqual([]);
  await info.attach("actual-journal-opening-refusal", { body: JSON.stringify({ ...original, reportedReason: run.reason, lifecycle: run.state, cleanup: run.cleanup,
    originalReaderIntegrity: run.evidence, functionalVerdict: run.verdict, originalStartStatus: operation.status,
    startupRejectionAndStorageRecoveryVisible: true, canonicalFailureEventInvented: false, browserRunMutations: 0 }), contentType: "application/json" });
});
