# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline.spec.ts >> scenario timeline: native frozen intent, observed faults and evaluation windows at 1440
- Location: tests/e2e/scenario-timeline.spec.ts:128:7

# Error details

```
Error: expect(locator).toBeFocused() failed

Locator:  getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('heading', { name: 'Selected run timeline', exact: true })
Expected: focused
Received: inactive
Timeout:  10000ms

Call log:
  - Expect "toBeFocused" getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('heading', { name: 'Selected run timeline', exact: true }) with timeout 10000ms
  - waiting for getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('heading', { name: 'Selected run timeline', exact: true })
    24 × locator resolved to <h3 tabindex="-1">Selected run timeline</h3>
       - unexpected value "inactive"

```

```yaml
- heading "Selected run timeline" [level=3]
```

# Test source

```ts
  58  |     resultUnit: "1",
  59  |     expression: structuredClone(definitions[0].expression.left),
  60  |   });
  61  |   project = await request(
  62  |     page,
  63  |     `/projects/${project.projectId}/documents/${docId}`,
  64  |     "PUT",
  65  |     { content: stringify(scenario), format: "yaml" },
  66  |     project.revision,
  67  |   );
  68  |   const pf = await request(
  69  |     page,
  70  |     `/projects/${project.projectId}/preflights`,
  71  |     "POST",
  72  |     { revision: project.revision },
  73  |   );
  74  |   expect(pf.status, JSON.stringify(pf)).toBe("ready");
  75  |   const created = await request(page, "/runs", "POST", {
  76  |     snapshotId: pf.snapshotId,
  77  |     preflightId: pf.preflightId,
  78  |   });
  79  |   await expect
  80  |     .poll(async () => (await request(page, `/runs/${created.runId}`)).state)
  81  |     .toBe("stopped");
  82  |   const run = await request(page, `/runs/${created.runId}`);
  83  |   const snapshot = (await request(page, `/runs/${run.runId}/snapshot`))
  84  |     .snapshot;
  85  |   for (const d of (await request(page, `/runs/${run.runId}/definitions`))
  86  |     .items) {
  87  |     await request(page, `/runs/${run.runId}/evaluations`, "POST", {
  88  |       snapshotId: run.snapshotId,
  89  |       definitionRef: d.definitionRef,
  90  |       definitionDigest: d.definitionDigest,
  91  |       evidenceRefs: [run.runId + ":reference-journal"],
  92  |     });
  93  |   }
  94  |   const timeline = await request(page, `/runs/${run.runId}/timeline?limit=200`);
  95  |   expect(
  96  |     timeline.items.some((r: any) => r.kind === "fault.activation_observed"),
  97  |   ).toBe(true);
  98  |   scenario.spec.steps[0].id = "later-start";
  99  |   project = await request(
  100 |     page,
  101 |     `/projects/${project.projectId}/documents/${docId}`,
  102 |     "PUT",
  103 |     { content: stringify(scenario), format: "yaml" },
  104 |     project.revision,
  105 |   );
  106 |   const runIds = (await request(page, "/runs")).items.map((r: any) => r.runId);
  107 |   await page.evaluate(
  108 |     ({ project, run, snapshot }) => {
  109 |       localStorage.setItem("studio.projectId", project.projectId);
  110 |       localStorage.setItem("studio.lastRun." + project.projectId, run.runId);
  111 |       localStorage.setItem("studio.lastRun", run.runId);
  112 |       localStorage.setItem(
  113 |         "studio.selection." + project.projectId,
  114 |         JSON.stringify({
  115 |           deploymentRef: snapshot.selection.deploymentRef,
  116 |           scenarioRef: snapshot.selection.scenarioRef,
  117 |         }),
  118 |       );
  119 |     },
  120 |     { project, run, snapshot },
  121 |   );
  122 |   await page.reload();
  123 |   await page.getByRole("tab", { name: "Experiments", exact: true }).focus();
  124 |   await page.keyboard.press("Enter");
  125 |   return { project, run, snapshot, timeline, runIds };
  126 | }
  127 | for (const width of [1024, 1440]) {
  128 |   test(`scenario timeline: native frozen intent, observed faults and evaluation windows at ${width}`, async ({
  129 |     page,
  130 |   }, info) => {
  131 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  132 |     await connectStudio(page, info);
  133 |     const made = await prepare(page, width);
  134 |     const writes: string[] = [],
  135 |       errors: string[] = [];
  136 |     page.on("request", (r) => {
  137 |       if (!["GET", "HEAD", "OPTIONS"].includes(r.method()))
  138 |         writes.push(r.method() + " " + new URL(r.url()).pathname);
  139 |     });
  140 |     page.on("pageerror", (e) => errors.push(e.message));
  141 |     await page.getByRole("tab", { name: "Timeline", exact: true }).focus();
  142 |     await page.keyboard.press("Enter");
  143 |     const panel = page.getByRole("region", {
  144 |       name: "Selected run timeline",
  145 |       exact: true,
  146 |     });
  147 |     await panel
  148 |       .getByRole("button", {
  149 |         name: "Inspect selected run timeline",
  150 |         exact: true,
  151 |       })
  152 |       .focus();
  153 |     await page.keyboard.press("Enter");
  154 |     const heading = panel.getByRole("heading", {
  155 |       name: "Selected run timeline",
  156 |       exact: true,
  157 |     });
> 158 |     await expect(heading).toBeFocused();
      |                           ^ Error: expect(locator).toBeFocused() failed
  159 |     await expect(panel).toContainText(made.snapshot.snapshotId);
  160 |     await expect(panel).toContainText(
  161 |       "Current draft differs from the executed revision",
  162 |     );
  163 |     await expect(
  164 |       panel.getByRole("table", { name: "Timeline records", exact: true }),
  165 |     ).toBeVisible();
  166 |     await expect(
  167 |       panel.locator('[data-timeline-id="intent:steps:start-reference"]'),
  168 |     ).toBeVisible();
  169 |     await expect(
  170 |       panel.locator('[data-timeline-id="intent:steps:later-start"]'),
  171 |     ).toHaveCount(0);
  172 |     for (const kind of [
  173 |       "fault.activation_requested",
  174 |       "fault.activation_observed",
  175 |     ]) {
  176 |       const row = panel
  177 |         .locator("tr[data-timeline-id]")
  178 |         .filter({ hasText: kind });
  179 |       await expect(row).toHaveCount(1);
  180 |       await expect(row).toContainText("100000");
  181 |       await expect(row).toContainText("owned_reference");
  182 |     }
  183 |     const assertion = panel
  184 |       .locator("tr[data-timeline-id]")
  185 |       .filter({ hasText: "assertion" });
  186 |     await expect(assertion).toContainText("complete");
  187 |     await expect(assertion).toContainText("pass");
  188 |     await expect(assertion).toContainText("[0, 200000)");
  189 |     const metric = panel
  190 |       .locator("tr[data-timeline-id]")
  191 |       .filter({ hasText: "evaluation · metric" });
  192 |     await expect(metric).toContainText("No verdict");
  193 |     expect(await request(page, `/projects/${made.project.projectId}`)).toEqual(
  194 |       made.project,
  195 |     );
  196 |     expect(
  197 |       (await request(page, `/runs/${made.run.runId}/snapshot`)).snapshot,
  198 |     ).toEqual(made.snapshot);
  199 |     expect((await request(page, `/runs/${made.run.runId}`)).journalDigest).toBe(
  200 |       made.run.journalDigest,
  201 |     );
  202 |     expect(
  203 |       (await request(page, "/runs")).items.map((r: any) => r.runId),
  204 |     ).toEqual(made.runIds);
  205 |     expect(
  206 |       await page.evaluate(
  207 |         () => document.documentElement.scrollWidth > innerWidth + 1,
  208 |       ),
  209 |     ).toBe(false);
  210 |     expect(writes).toEqual([]);
  211 |     expect(errors).toEqual([]);
  212 |     await info.attach("owned-timeline-context", {
  213 |       body: JSON.stringify({
  214 |         runId: made.run.runId,
  215 |         snapshotId: made.snapshot.snapshotId,
  216 |         revision: made.snapshot.revision,
  217 |         projectRevision: made.project.revision,
  218 |         scope: made.timeline.evidenceScope,
  219 |       }),
  220 |       contentType: "application/json",
  221 |     });
  222 |     await page.screenshot({
  223 |       path: info.outputPath("scenario-timeline.png"),
  224 |       fullPage: true,
  225 |     });
  226 |   });
  227 | }
  228 |
  229 | for (const width of [1024, 1440]) {
  230 |   test(`scenario authoring completion: held conditions acknowledgement preserves a reopened draft at ${width}`, async ({
  231 |     page,
  232 |   }, info) => {
  233 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  234 |     await connectStudio(page, info);
  235 |     const made = await prepare(page, width);
  236 |     const open = page.getByRole("button", {
  237 |       name: "Edit initial conditions",
  238 |       exact: true,
  239 |     });
  240 |     await open.focus();
  241 |     await page.keyboard.press("Enter");
  242 |     await page
  243 |       .getByLabel("Scenario acceptance intent", { exact: true })
  244 |       .fill("First committed conditions");
  245 |     let release!: () => void;
  246 |     const released = new Promise<void>((resolve) => (release = resolve));
  247 |     let ready = false,
  248 |       committed: any = null,
  249 |       writes = 0;
  250 |     await page.route(
  251 |       `**/api/v1/projects/${made.project.projectId}/edits`,
  252 |       async (route) => {
  253 |         if (route.request().method() !== "POST") return route.continue();
  254 |         writes++;
  255 |         const response = await route.fetch({ timeout: 30000 });
  256 |         committed = await response.json();
  257 |         ready = true;
  258 |         await released;
```
