import { expect, type Page, type TestInfo } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import path from "node:path";

/** Read actual hash-verified retained records, never synthesized browser rows. */
export async function measureHistory(
  page: Page,
  testInfo: TestInfo,
  referenceProjectId?: string,
) {
  const dataRoot = process.env.STUDIO_BROWSER_DATA;
  if (!dataRoot)
    throw new Error(
      "The isolated native browser wrapper must supply STUDIO_BROWSER_DATA.",
    );
  const projectId =
    referenceProjectId ||
    (await page.evaluate(() => localStorage.getItem("studio.projectId")));
  if (!projectId)
    throw new Error(
      "A valid reference project is required before provisioning the retained fixture.",
    );
  const python =
    process.env.STUDIO_PYTHON ||
    path.join(
      process.cwd(),
      ".venv",
      process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
    );
  const fixture = JSON.parse(
    execFileSync(
      python,
      [
        "-I",
        path.join(
          process.cwd(),
          "tests/fixtures/performance/create_recorded_history.py",
        ),
        "--data-dir",
        dataRoot,
        "--project-id",
        projectId,
      ],
      { encoding: "utf8", timeout: 60000, maxBuffer: 1024 * 1024 },
    ),
  );
  expect(fixture.recordCount).toBe(50000);
  expect(fixture.integrity).toBe("valid");
  await page.evaluate(({ projectId, runId }) => {
    localStorage.setItem("studio.projectId", projectId);
    localStorage.setItem("studio.lastRun", runId);
    localStorage.setItem("studio.lastRun." + projectId, runId);
  }, fixture);
  await page.reload();
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  await expect(
    page.getByText("Recorded fixture scope", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Stop", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  await page
    .getByLabel("Event kind", { exact: true })
    .selectOption("log.appended");
  await page.getByLabel("Severity", { exact: true }).selectOption("info");
  const panel = page.getByTestId("retained-history"),
    rows = panel.locator("[data-history-record=true]");
  await expect(panel).toHaveAttribute("aria-busy", "false");
  await expect(rows).toHaveCount(200);
  await expect(panel).toHaveAttribute("data-integrity", "valid");
  await expect(rows.first()).toHaveAttribute(
    "data-event-id",
    fixture.runId + ":record-1",
  );
  await expect(rows.last()).toHaveAttribute(
    "data-event-id",
    fixture.runId + ":record-200",
  );
  const times: number[] = [];
  let warmup = 0;
  for (let repeat = -1; repeat < 30; repeat++) {
    const previous = Number(await panel.getAttribute("data-history-epoch"));
    const begin = await page.evaluate(() => performance.now());
    await page
      .getByRole("button", { name: "Reload retained first page", exact: true })
      .click();
    await expect
      .poll(async () => Number(await panel.getAttribute("data-history-epoch")))
      .toBeGreaterThan(previous);
    await expect(panel).toHaveAttribute("aria-busy", "false");
    await expect(rows).toHaveCount(200);
    await expect(rows.first()).toHaveAttribute("data-sequence", "1");
    await expect(rows.last()).toHaveAttribute("data-sequence", "200");
    await expect(panel).toHaveAttribute("data-integrity", "valid");
    const end = await page.evaluate(
      () =>
        new Promise<number>((resolve) =>
          requestAnimationFrame(() =>
            requestAnimationFrame(() => resolve(performance.now())),
          ),
        ),
    );
    if (repeat < 0) warmup = end - begin;
    else times.push(end - begin);
  }
  const sorted = [...times].sort((a, b) => a - b),
    p95 = sorted[Math.ceil(sorted.length * 0.95) - 1];
  const result = {
    scope:
      "trusted synthetic recorded_fixture retained-history rendering; no runtime or physical observation claim",
    platform: process.platform,
    architecture: process.arch,
    browser: await page.context().browser()?.version(),
    viewport: page.viewportSize(),
    sourceRecords: fixture.recordCount,
    pageSize: 200,
    serverFilters: { type: "log.appended", severity: "info" },
    integrity: fixture.integrity,
    journalDigest: fixture.journalDigest,
    journalBytes: fixture.journalBytes,
    warmups: 1,
    warmupMilliseconds: warmup,
    repetitions: 30,
    milliseconds: times,
    p95,
    threshold: 2000,
    passed: p95 <= 2000,
    limitations: [
      "Provisioning and cold initial journal verification are excluded from the warmed 30-repetition profile.",
      "Native Windows and other browser engines NOT_RUN.",
      "This fixture has no process authority, provider control capability, or claim of observed simulator/device behaviour.",
    ],
  };
  writeFileSync(
    testInfo.outputPath("history-performance.json"),
    JSON.stringify(result, null, 2),
  );
  await page.screenshot({
    path: testInfo.outputPath("history-performance.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Next retained page", exact: true })
    .click();
  await expect(rows).toHaveCount(200);
  await expect(rows.first()).toHaveAttribute("data-sequence", "201");
  await expect(rows.last()).toHaveAttribute("data-sequence", "400");
  await page
    .getByRole("button", { name: "Previous retained page", exact: true })
    .click();
  await expect(rows).toHaveCount(200);
  await expect(rows.first()).toHaveAttribute("data-sequence", "1");
  const after = await page.evaluate(async (runId) => {
    const response = await fetch("/api/v1/runs/" + runId + "/evidence");
    return response.json();
  }, fixture.runId);
  expect(after.integrity).toBe("valid");
  expect(after.items[0].digest).toBe(fixture.journalDigest);
  expect(after.items[0].recordCount).toBe(50000);
  expect(result.passed).toBe(true);
}
