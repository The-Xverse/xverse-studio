# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: accessibility.spec.ts >> operability: keyboard, focus, textual status and reference workloads at 1440x900
- Location: tests/e2e/accessibility.spec.ts:30:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Recorded fixture scope', { exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('Recorded fixture scope', { exact: true }) with timeout 10000ms
  - waiting for getByText('Recorded fixture scope', { exact: true })

```

```yaml
- link "Skip to workspace":
  - /url: "#main-content"
- banner:
  - button "X-Verse Studio home": X X-VERSE STUDIO
  - text: Local workspace REFERENCE PREVIEW
  - button "Environment"
  - text: LO
- navigation "Main navigation":
  - button "Workspace"
  - button "Catalog"
  - button "Laboratory": Lab
  - button "Compatibility and environment": Settings
  - text: v0.1
- main:
  - button "Workspace"
  - text: System
  - heading "Process control reference" [level=1]
  - text: Draft Process control terms Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched. rev 2
  - 'button "Dependencies: none unresolved"': Dependencies
  - button "Undo"
  - button "Redo" [disabled]
  - button "Export"
  - button "Validate"
  - button "Preflight & run"
  - tablist "System workflows":
    - tab "Model"
    - tab "Connections"
    - tab "Deployment"
    - tab "Experiments"
    - tab "Results" [selected]
    - button "XDL source"
  - text: Draft revision
  - code: "2"
  - text: 3 elements · 2 connections Execution scope Owned reference
  - heading "Your evidence starts with a run" [level=3]
  - text: Validate the draft and run preflight to create an immutable input snapshot.
  - button "Preflight & run"
  - text: Local project · Saved on backend Authoritative XDL · Layout stored separately 1 provider(s) available
```

# Test source

```ts
  1   | import { expect, type Page, type TestInfo } from "@playwright/test";
  2   | import { execFileSync } from "node:child_process";
  3   | import { writeFileSync } from "node:fs";
  4   | import path from "node:path";
  5   |
  6   | /** Read actual hash-verified retained records, never synthesized browser rows. */
  7   | export async function measureHistory(
  8   |   page: Page,
  9   |   testInfo: TestInfo,
  10  |   referenceProjectId?: string,
  11  | ) {
  12  |   const dataRoot = process.env.STUDIO_BROWSER_DATA;
  13  |   if (!dataRoot)
  14  |     throw new Error(
  15  |       "The isolated native browser wrapper must supply STUDIO_BROWSER_DATA.",
  16  |     );
  17  |   const projectId =
  18  |     referenceProjectId ||
  19  |     (await page.evaluate(() => localStorage.getItem("studio.projectId")));
  20  |   if (!projectId)
  21  |     throw new Error(
  22  |       "A valid reference project is required before provisioning the retained fixture.",
  23  |     );
  24  |   const python =
  25  |     process.env.STUDIO_PYTHON ||
  26  |     path.join(
  27  |       process.cwd(),
  28  |       ".venv",
  29  |       process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
  30  |     );
  31  |   const fixture = JSON.parse(
  32  |     execFileSync(
  33  |       python,
  34  |       [
  35  |         "-I",
  36  |         path.join(
  37  |           process.cwd(),
  38  |           "tests/fixtures/performance/create_recorded_history.py",
  39  |         ),
  40  |         "--data-dir",
  41  |         dataRoot,
  42  |         "--project-id",
  43  |         projectId,
  44  |       ],
  45  |       { encoding: "utf8", timeout: 60000, maxBuffer: 1024 * 1024 },
  46  |     ),
  47  |   );
  48  |   expect(fixture.recordCount).toBe(50000);
  49  |   expect(fixture.integrity).toBe("valid");
  50  |   await page.evaluate(({ projectId, runId }) => {
  51  |     localStorage.setItem("studio.projectId", projectId);
  52  |     localStorage.setItem("studio.lastRun", runId);
  53  |     localStorage.setItem("studio.lastRun." + projectId, runId);
  54  |   }, fixture);
  55  |   await page.reload();
  56  |   await page.getByRole("tab", { name: "Results", exact: false }).click();
  57  |   await expect(
  58  |     page.getByText("Recorded fixture scope", { exact: true }),
> 59  |   ).toBeVisible();
      |     ^ Error: expect(locator).toBeVisible() failed
  60  |   await expect(
  61  |     page.getByRole("button", { name: "Stop", exact: true }),
  62  |   ).toHaveCount(0);
  63  |   await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  64  |   await page
  65  |     .getByLabel("Event kind", { exact: true })
  66  |     .selectOption("log.appended");
  67  |   await page.getByLabel("Severity", { exact: true }).selectOption("info");
  68  |   const panel = page.getByTestId("retained-history"),
  69  |     rows = panel.locator("[data-history-record=true]");
  70  |   await expect(panel).toHaveAttribute("aria-busy", "false");
  71  |   await expect(rows).toHaveCount(200);
  72  |   await expect(panel).toHaveAttribute("data-integrity", "valid");
  73  |   await expect(rows.first()).toHaveAttribute(
  74  |     "data-event-id",
  75  |     fixture.runId + ":record-1",
  76  |   );
  77  |   await expect(rows.last()).toHaveAttribute(
  78  |     "data-event-id",
  79  |     fixture.runId + ":record-200",
  80  |   );
  81  |   const times: number[] = [];
  82  |   let warmup = 0;
  83  |   for (let repeat = -1; repeat < 30; repeat++) {
  84  |     const previous = Number(await panel.getAttribute("data-history-epoch"));
  85  |     const begin = await page.evaluate(() => performance.now());
  86  |     await page
  87  |       .getByRole("button", { name: "Reload retained first page", exact: true })
  88  |       .click();
  89  |     await expect
  90  |       .poll(async () => Number(await panel.getAttribute("data-history-epoch")))
  91  |       .toBeGreaterThan(previous);
  92  |     await expect(panel).toHaveAttribute("aria-busy", "false");
  93  |     await expect(rows).toHaveCount(200);
  94  |     await expect(rows.first()).toHaveAttribute("data-sequence", "1");
  95  |     await expect(rows.last()).toHaveAttribute("data-sequence", "200");
  96  |     await expect(panel).toHaveAttribute("data-integrity", "valid");
  97  |     const end = await page.evaluate(
  98  |       () =>
  99  |         new Promise<number>((resolve) =>
  100 |           requestAnimationFrame(() =>
  101 |             requestAnimationFrame(() => resolve(performance.now())),
  102 |           ),
  103 |         ),
  104 |     );
  105 |     if (repeat < 0) warmup = end - begin;
  106 |     else times.push(end - begin);
  107 |   }
  108 |   const sorted = [...times].sort((a, b) => a - b),
  109 |     p95 = sorted[Math.ceil(sorted.length * 0.95) - 1];
  110 |   const result = {
  111 |     scope:
  112 |       "trusted synthetic recorded_fixture retained-history rendering; no runtime or physical observation claim",
  113 |     platform: process.platform,
  114 |     architecture: process.arch,
  115 |     browser: await page.context().browser()?.version(),
  116 |     viewport: page.viewportSize(),
  117 |     sourceRecords: fixture.recordCount,
  118 |     pageSize: 200,
  119 |     serverFilters: { type: "log.appended", severity: "info" },
  120 |     integrity: fixture.integrity,
  121 |     journalDigest: fixture.journalDigest,
  122 |     journalBytes: fixture.journalBytes,
  123 |     warmups: 1,
  124 |     warmupMilliseconds: warmup,
  125 |     repetitions: 30,
  126 |     milliseconds: times,
  127 |     p95,
  128 |     threshold: 2000,
  129 |     passed: p95 <= 2000,
  130 |     limitations: [
  131 |       "Provisioning and cold initial journal verification are excluded from the warmed 30-repetition profile.",
  132 |       "Native Windows and other browser engines NOT_RUN.",
  133 |       "This fixture has no process authority, provider control capability, or claim of observed simulator/device behaviour.",
  134 |     ],
  135 |   };
  136 |   writeFileSync(
  137 |     testInfo.outputPath("history-performance.json"),
  138 |     JSON.stringify(result, null, 2),
  139 |   );
  140 |   await page.screenshot({
  141 |     path: testInfo.outputPath("history-performance.png"),
  142 |     fullPage: true,
  143 |   });
  144 |   await page
  145 |     .getByRole("button", { name: "Next retained page", exact: true })
  146 |     .click();
  147 |   await expect(rows).toHaveCount(200);
  148 |   await expect(rows.first()).toHaveAttribute("data-sequence", "201");
  149 |   await expect(rows.last()).toHaveAttribute("data-sequence", "400");
  150 |   await page
  151 |     .getByRole("button", { name: "Previous retained page", exact: true })
  152 |     .click();
  153 |   await expect(rows).toHaveCount(200);
  154 |   await expect(rows.first()).toHaveAttribute("data-sequence", "1");
  155 |   const after = await page.evaluate(async (runId) => {
  156 |     const response = await fetch("/api/v1/runs/" + runId + "/evidence");
  157 |     return response.json();
  158 |   }, fixture.runId);
  159 |   expect(after.integrity).toBe("valid");
```
