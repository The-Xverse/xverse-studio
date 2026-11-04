import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { parse, stringify } from "yaml";
import { connectStudio } from "../e2e/connect-studio";

test("Actual complete Autoverse assessments preserve results, clocks and immutable inputs", async ({
  page,
}, info) => {
  const project = JSON.parse(
    readFileSync(
      path.join(
        process.env.STUDIO_BROWSER_DATA!,
        "fault-authoring-project.private.json",
      ),
      "utf8",
    ),
  );
  await connectStudio(page, info);
  await page.evaluate((p) => {
    localStorage.setItem("studio.projectId", p.projectId);
    localStorage.setItem("studio.lastRun." + p.projectId, p._runId);
  }, project);
  await page.reload();
  const open = async () => {
    await page.getByRole("tab", { name: "Experiments", exact: true }).click();
    await page.getByRole("tab", { name: "Assertions", exact: true }).click();
    const panel = page.getByRole("region", {
      name: "Frozen assertions and metrics",
      exact: true,
    });
    await expect(panel).toContainText("bridge loss acknowledged", {
      ignoreCase: true,
    });
    return panel;
  };
  let panel = await open();
  const route = `/api/v1/runs/${project._runId}`;
  const support = await page.request
    .get(route + "/assessment-support")
    .then((r) => r.json());
  expect(support.status).toBe("supported");
  expect(support.mapping.coverageScope).toBe("recorded-events-only");
  expect(support.evidenceId).toBe(project._runId + ":provider-journal");
  const expected: Record<string, [string, string | null]> = {
    "bridge-loss-acknowledged": ["complete", "pass"],
    "two-recoveries-before-ten-seconds": ["complete", "fail"],
    "recovery-through-thirty-seconds": ["complete", "indeterminate"],
    "recorded-activation-count": ["complete", null],
    "unadmitted-count-unit": ["error", null],
    "unmapped-simulation-clock": ["complete", "indeterminate"],
  };
  const keys: string[] = [];
  let firstId = "",
    lost = false;
  await page.route("**/api/v1/runs/*/evaluations", async (request) => {
    if (request.request().method() !== "POST") {
      await request.continue();
      return;
    }
    keys.push(request.request().headers()["idempotency-key"]);
    if (!lost) {
      lost = true;
      const response = await request.fetch();
      expect(response.status()).toBe(202);
      firstId = (await response.json()).evaluationId;
      await request.abort("failed");
    } else await request.continue();
  });
  for (const [definition, [status, verdict]] of Object.entries(expected)) {
    await panel
      .getByRole("combobox", {
        name: "Snapshot definition reference",
        exact: true,
      })
      .selectOption(definition);
    await panel
      .getByRole("button", { name: "Evaluate assertion", exact: true })
      .click();
    if (definition === "bridge-loss-acknowledged") {
      await expect(
        page.getByRole("alert").filter({ hasText: /fetch|network/i }),
      ).toBeVisible();
      await panel
        .getByRole("button", { name: "Evaluate assertion", exact: true })
        .click();
    }
    const card = panel
      .locator(".evaluation-card")
      .filter({
        has: page.getByRole("heading", { name: definition, exact: true }),
      });
    await expect(card).toBeVisible();
    await expect(card).toContainText(
      verdict ??
        (status === "error" ? "Evaluation error" : "Evaluation complete"),
    );
  }
  expect(keys[0]).toBe(keys[1]);
  const jobs = await page.request
    .get(route + "/evaluations")
    .then((r) => r.json());
  expect(jobs.items).toHaveLength(6);
  expect(
    jobs.items.find((e: any) => e.definitionRef === "bridge-loss-acknowledged")
      .evaluationId,
  ).toBe(firstId);
  const evidence = await page.request
    .get(route + "/evidence")
    .then((r) => r.json());
  for (const job of jobs.items) {
    expect([job.status, job.verdict]).toEqual(expected[job.definitionRef]);
    expect(job.evidenceReader).toBe("studio.hash-chain-v1");
    expect(job.evidenceMapping.mapping.mappingId).toBe(
      support.mapping.mappingId,
    );
    expect(job.inputEvidenceDigests).toEqual([evidence.items[0].digest]);
    expect(job.evidenceDigests).toEqual([evidence.items[0].digest]);
  }
  expect(
    jobs.items.find(
      (e: any) => e.definitionRef === "recorded-activation-count",
    ),
  ).toMatchObject({ value: 1, unit: "1", verdict: null });
  expect(
    jobs.items.find(
      (e: any) => e.definitionRef === "recovery-through-thirty-seconds",
    ).reasons,
  ).toContain("COVERAGE_INCOMPLETE");
  expect(
    jobs.items.find((e: any) => e.definitionRef === "unmapped-simulation-clock")
      .reasons,
  ).toContain("CLOCK_MAPPING_UNAVAILABLE");
  const timeline = await page.request
    .get(
      route +
        `/timeline?formatVersion=1.1&snapshotId=${project._snapshotId}&limit=200`,
    )
    .then((r) => r.json());
  expect(
    timeline.items.filter(
      (r: any) => r.layer === "evaluation" && r.position.status === "aligned",
    ),
  ).toHaveLength(5);
  for (const width of [1024, 1440]) {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await panel
      .getByRole("button", { name: "Inspect frozen assessments", exact: true })
      .focus();
    await page.keyboard.press("Enter");
    await expect(panel.locator(".evaluation-card")).toHaveCount(6);
    await page.screenshot({
      path: info.outputPath(`actual-assessments-${width}.png`),
      fullPage: true,
    });
  }
  // A real source edit is separate from the selected frozen assessment inputs.
  const original = await page.request
    .get(`/api/v1/projects/${project.projectId}`)
    .then((r) => r.json());
  const [id, doc]: any = Object.entries(original.documents).find(([, d]: any) =>
    d.path.endsWith("scenario.xdl.yaml"),
  )!;
  const scenario = parse(doc.content);
  scenario.extensions[
    "io.xverse.studio.experiments"
  ].definitions[0].window.endTick = "1000000";
  const changed = await page.evaluate(
    async ({ projectId, id, revision, content }) => {
      const session = await fetch("/api/v1/session").then((r) => r.json());
      const r = await fetch(`/api/v1/projects/${projectId}/documents/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": session.csrfToken,
          "If-Match": String(revision),
        },
        body: JSON.stringify({ content, format: "yaml" }),
      });
      if (!r.ok) throw Error("Controlled draft save failed: " + r.status);
      return r.json();
    },
    {
      projectId: project.projectId,
      id,
      revision: original.revision,
      content: stringify(scenario),
    },
  );
  expect(changed.revision).toBeGreaterThan(original.revision);
  await page.reload();
  panel = await open();
  await expect(panel.locator(".evaluation-card")).toHaveCount(6);
  expect(
    await page.request.get(route + "/evaluations").then((r) => r.json()),
  ).toEqual(jobs);
  await page.evaluate(
    async ({ projectId, revision, restore }) => {
      const session = await fetch("/api/v1/session").then((r) => r.json());
      const r = await fetch(
        `/api/v1/projects/${projectId}/revisions/${restore}/restore`,
        {
          method: "POST",
          headers: {
            "X-CSRF-Token": session.csrfToken,
            "If-Match": String(revision),
          },
        },
      );
      if (!r.ok)
        throw Error("Controlled draft restoration failed: " + r.status);
    },
    {
      projectId: project.projectId,
      revision: changed.revision,
      restore: original.revision,
    },
  );
  const restored = await page.request
    .get(`/api/v1/projects/${project.projectId}`)
    .then((r) => r.json());
  expect(restored.documents).toEqual(original.documents);
  await info.attach("actual-assessment-results", {
    body: JSON.stringify({
      scope: "recorded bridge acknowledgement events only",
      runId: project._runId,
      jobs: jobs.items,
      lostAcknowledgementRetriedSameKey: true,
    }),
    contentType: "application/json",
  });
});
