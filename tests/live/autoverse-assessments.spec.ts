import { test, expect, type Page, type TestInfo } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
import { assessmentReport } from "../../apps/studio-web/src/features/experiments/FrozenAssessments";

const saved = () =>
  JSON.parse(
    readFileSync(
      path.join(
        process.env.STUDIO_BROWSER_DATA!,
        "assessment-recording.private.json",
      ),
      "utf8",
    ),
  );
async function open(page: Page, info: TestInfo) {
  const data = saved();
  await connectStudio(page, info);
  await page.evaluate((data) => {
    localStorage.setItem("studio.projectId", data.projectId);
    localStorage.setItem("studio.lastRun." + data.projectId, data.runId);
  }, data);
  await page.reload();
  await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  await page.getByRole("tab", { name: "Assertions", exact: true }).click();
  return page.locator(
    'section[aria-label="Frozen assertions and metrics"], .connection-layout',
  );
}

for (const width of [1024, 1440]) {
  test(`Actual recorded Autoverse has no admitted assessments at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    const writes: string[] = [];
    page.on("request", (r) => {
      if (r.method() !== "GET") writes.push(r.url());
    });
    const panel = await open(page, info);
    await expect(panel).toContainText(
      "No admitted assessment definitions in this frozen snapshot",
    );
    await expect(panel).toContainText(saved().snapshotId);
    await expect(
      panel.getByRole("button", { name: "Evaluate assertion", exact: true }),
    ).toBeDisabled();
    await panel
      .getByRole("button", { name: "Inspect frozen assessments", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(panel).toContainText(
      "No admitted assessment definitions in this frozen snapshot",
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(
      writes.filter((url) => /\/(runs|evaluations|commands)(\/|$)/.test(url)),
    ).toEqual([]);
    await page.screenshot({
      path: info.outputPath(`recorded-assessments-${width}.png`),
      fullPage: true,
    });
  });
}

test("A failed definition read is unknown and can be retried", async ({
  page,
}, info) => {
  await page.route("**/api/v1/runs/*/definitions", (route) =>
    route.fulfill({
      status: 503,
      json: {
        code: "TEST_DEFINITION_READ_UNAVAILABLE",
        message: "Controlled definition read failure",
      },
    }),
  );
  const panel = await open(page, info);
  await expect(panel.getByRole("alert")).toContainText(
    "Assessment availability is unknown",
  );
  await expect(
    panel.getByText("No admitted assessment definitions", { exact: false }),
  ).toHaveCount(0);
  await expect(
    panel.getByRole("button", { name: "Evaluate assertion", exact: true }),
  ).toHaveCount(0);
  await page.unroute("**/api/v1/runs/*/definitions");
  await panel
    .getByRole("button", { name: "Inspect frozen assessments", exact: true })
    .click();
  await expect(panel).toContainText(
    "No admitted assessment definitions in this frozen snapshot",
  );
});

test("A departed read cannot replace a newer failed inspection", async ({
  page,
}, info) => {
  let release!: () => void, seen!: () => void, finish!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const started = new Promise<void>((resolve) => {
    seen = resolve;
  });
  const finished = new Promise<void>((resolve) => {
    finish = resolve;
  });
  let count = 0;
  await page.route("**/api/v1/runs/*/definitions", async (route) => {
    if (++count === 1) {
      const response = await route.fetch();
      seen();
      await gate;
      try {
        await route.fulfill({ response });
      } finally {
        finish();
      }
    } else
      await route.fulfill({
        status: 503,
        json: { message: "Controlled newer read failure" },
      });
  });
  const panel = await open(page, info);
  await started;
  await page.getByRole("tab", { name: "Timeline", exact: true }).click();
  await page.getByRole("tab", { name: "Assertions", exact: true }).click();
  await expect(panel.getByRole("alert")).toContainText(
    "Controlled newer read failure",
  );
  release();
  // The first request may already be aborted by the mounted component's cleanup.
  await finished;
  await page.unroute("**/api/v1/runs/*/definitions");
  await expect(panel.getByRole("alert")).toContainText(
    "Controlled newer read failure",
  );
  await expect(
    panel.getByText("No admitted assessment definitions", { exact: false }),
  ).toHaveCount(0);
});

test("A failed read cancels its other pending assessment reads", async ({
  page,
}, info) => {
  const panel = await open(page, info);
  await expect(panel).toContainText(
    "No admitted assessment definitions in this frozen snapshot",
  );
  // Intercept only this explicit refresh; initial header snapshot reads have ended.
  let release!: () => void, seen!: () => void, finish!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const started = new Promise<void>((resolve) => {
    seen = resolve;
  });
  const finished = new Promise<void>((resolve) => {
    finish = resolve;
  });
  let aborted = 0;
  page.on("requestfailed", (request) => {
    if (request.url().endsWith("/snapshot")) aborted++;
  });
  await page.route("**/api/v1/runs/*/snapshot", async (route) => {
    try {
      const response = await route.fetch();
      seen();
      await gate;
      if (!route.request().failure()) await route.fulfill({ response });
    } finally {
      finish();
    }
  });
  await page.route("**/api/v1/runs/*/definitions", async (route) => {
    await started;
    await route.fulfill({
      status: 503,
      json: { message: "Controlled sibling cancellation failure" },
    });
  });
  try {
    await panel
      .getByRole("button", { name: "Inspect frozen assessments", exact: true })
      .click();
    await expect(panel.getByRole("alert")).toContainText(
      "Controlled sibling cancellation failure",
    );
    await expect.poll(() => aborted, { timeout: 5000 }).toBeGreaterThan(0);
  } finally {
    release();
    await finished;
    await page.unroute("**/api/v1/runs/*/snapshot");
    await page.unroute("**/api/v1/runs/*/definitions");
  }
});

test("Labelled display fixture keeps metric, indeterminate and error states separate", async ({
  page,
}, info) => {
  info.annotations.push({
    type: "scope",
    description:
      "Synthetic display rows over the recorded Autoverse UI; no provider/evaluator admission or actual verdict claim.",
  });
  const data = saved(),
    hash = "sha256:" + "0".repeat(64);
  const definitions = ["metric", "indeterminate", "error"].map((kind) => ({
    definitionRef: "display-only-" + kind,
    definitionDigest: hash,
    schemaDigest: hash,
    profileNamespace: "io.xverse.studio.experiments",
    profileVersion: "1.0.0",
    definition: {
      evaluationId: "display-only-" + kind,
      name: "Display fixture " + kind,
      version: "1.0",
      kind: kind === "metric" ? "metric" : "assertion",
      coveragePolicy: "complete",
      systemRef: data.snapshotResponse.snapshot.selection.systemRef,
      scenarioRef: data.snapshotResponse.snapshot.selection.scenarioRef,
      window: {
        clockDomainRef: "display-only-clock",
        startTick: "0",
        endTick: "1000",
      },
    },
  }));
  const rows = definitions.map((entry, index) => ({
    evaluationId: "display-only-job-" + index,
    runId: data.runId,
    snapshotId: data.snapshotId,
    definitionRef: entry.definitionRef,
    definitionDigest: hash,
    status: index === 2 ? "error" : "complete",
    verdict: index === 1 ? "indeterminate" : null,
    value: index === 0 ? 0 : null,
    unit: "1",
    coverage: index === 0 ? "complete" : "incomplete",
    partial: index !== 0,
    reasons:
      index === 1
        ? ["CLOCK_MAPPING_UNSUPPORTED"]
        : index === 2
          ? ["EVALUATION_INTERRUPTED"]
          : [],
    evaluatorIdentity: {
      version: "display-fixture-v1",
      implementationDigest: hash,
    },
    inputEvidenceDigests: [hash],
    evidenceDigests: [hash],
  }));
  await page.route("**/api/v1/runs/*/definitions", (route) =>
    route.fulfill({ json: { items: definitions, nextCursor: null } }),
  );
  await page.route("**/api/v1/runs/*/evaluations?*", (route) =>
    route.fulfill({ json: { items: rows, nextCursor: null } }),
  );
  const panel = await open(page, info);
  await expect(panel.locator(".evaluation-card")).toHaveCount(3);
  const metric = panel
    .locator(".evaluation-card")
    .filter({ hasText: "display-only-metric" });
  await expect(
    metric.getByText("Evaluation complete", { exact: true }),
  ).toBeVisible();
  await expect(metric.getByText("Not evaluated", { exact: true })).toHaveCount(
    0,
  );
  await expect(
    metric
      .locator(".key-values div")
      .filter({ has: page.locator("dt", { hasText: /^Value$/ }) })
      .locator("dd"),
  ).toHaveText("0");
  await expect(
    panel
      .locator(".evaluation-card")
      .filter({ hasText: "display-only-indeterminate" }),
  ).toContainText("CLOCK_MAPPING_UNSUPPORTED");
  await expect(
    panel
      .locator(".evaluation-card")
      .filter({ hasText: "display-only-error" })
      .getByText("Evaluation error", { exact: true }),
  ).toBeVisible();
  for (const width of [1024, 1440]) {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
});

test("Actual Autoverse evidence cannot enter the reference evaluator", async ({
  page,
}, info) => {
  const panel = await open(page, info),
    data = saved();
  const support = await page.request.get(
    `/api/v1/runs/${data.runId}/assessment-support`,
  );
  expect(support.status()).toBe(200);
  const body = await support.json();
  expect(body).toMatchObject({
    formatVersion: "1.0",
    runId: data.runId,
    snapshotId: data.snapshotId,
    projectId: data.projectId,
    status: "unsupported",
    reasons: ["EVALUATION_EVIDENCE_UNSUPPORTED"],
    evidenceId: data.runId + ":provider-journal",
    evidenceReader: "studio.hash-chain-v1",
  });
  const refused = await page.evaluate(async (data) => {
    const session = await fetch("/api/v1/session").then((r) => r.json());
    const response = await fetch(`/api/v1/runs/${data.runId}/evaluations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": session.csrfToken,
        "Idempotency-Key": "unsupported-autoverse-assessment",
      },
      body: JSON.stringify({
        snapshotId: data.snapshotId,
        definitionRef: "unadmitted-definition",
        definitionDigest: "sha256:" + "0".repeat(64),
        evidenceRefs: [data.runId + ":provider-journal"],
      }),
    });
    return { status: response.status, body: await response.json() };
  }, data);
  expect(refused.status).toBe(422);
  expect(refused.body.code).toBe("EVALUATION_EVIDENCE_UNSUPPORTED");
  await expect(panel).toContainText(
    "No admitted assessment definitions in this frozen snapshot",
  );
});

for (const change of [
  "snapshot",
  "project",
  "integrity",
  "definition-page",
  "result-page",
  "cursor",
  "result-owner",
  "partial-pass",
  "support-owner",
  "support-identity",
  "support-claims-missing-evidence",
  "support-missing-reason",
]) {
  test(`Recorded Autoverse display rejects ${change} counterexample`, () => {
    const data = saved();
    const support = structuredClone(data.supportResponse);
    const snapshot = structuredClone(data.snapshotResponse),
      definitions = { items: [] as any[], nextCursor: null as string | null },
      results = { items: [] as any[], nextCursor: null as string | null };
    if (change === "support-owner") support.runId = "another-run";
    if (change === "support-identity")
      support.snapshotDigest = "sha256:" + "0".repeat(64);
    if (change === "support-claims-missing-evidence")
      Object.assign(support, {
        status: "supported",
        evidenceId: null,
        reasons: [],
      });
    if (change === "support-missing-reason") support.reasons = [];
    if (change === "snapshot")
      snapshot.snapshot.snapshotId = "another-snapshot";
    if (change === "project") snapshot.snapshot.projectId = "another-project";
    if (change === "integrity") snapshot.integrity = "invalid";
    if (change === "definition-page") definitions.nextCursor = "32";
    if (change === "result-page") results.items = Array(101).fill({});
    if (change === "cursor") results.nextCursor = "opaque-unsupported";
    if (["result-owner", "partial-pass"].includes(change)) {
      // Controlled display-only negative; this is never admitted or evaluated.
      const digest = "sha256:" + "0".repeat(64);
      definitions.items.push({
        definitionRef: "display-negative",
        definitionDigest: digest,
        schemaDigest: digest,
        profileNamespace: "io.xverse.studio.experiments",
        profileVersion: "1.0.0",
        definition: {
          version: "1.0",
          coveragePolicy: "complete",
          systemRef: snapshot.snapshot.selection.systemRef,
          scenarioRef: snapshot.snapshot.selection.scenarioRef,
          evaluationId: "display-negative",
          name: "Display negative",
          kind: "assertion",
          window: {
            clockDomainRef: "host-runtime",
            startTick: "0",
            endTick: "1",
          },
        },
      });
      results.items.push({
        evaluationId: "display-negative-job",
        runId: change === "result-owner" ? "another-run" : data.runId,
        snapshotId: data.snapshotId,
        definitionRef: "display-negative",
        definitionDigest: digest,
        status: "complete",
        verdict: "pass",
        coverage: change === "result-owner" ? "complete" : "incomplete",
        partial: change !== "result-owner",
      });
    }
    expect(() =>
      assessmentReport(
        snapshot,
        definitions,
        results,
        {
          runId: data.runId,
          snapshotId: data.snapshotId,
          projectId: data.projectId,
          stateVersion: 1,
        },
        data.projectId,
        support,
      ),
    ).toThrow();
  });
}
