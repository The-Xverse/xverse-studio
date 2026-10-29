# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: campaign-workflow.spec.ts >> campaign workflow: retained native children reopen without scheduling at 1024
- Location: tests/e2e/campaign-workflow.spec.ts:36:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('button', { name: 'Refresh campaign history', exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('button', { name: 'Refresh campaign history', exact: true }) with timeout 10000ms
  - waiting for getByRole('button', { name: 'Refresh campaign history', exact: true })

```

```yaml
- link "Skip to workspace":
  - /url: "#main-content"
- banner:
  - button "X-Verse Studio home": X X-VERSE STUDIO
  - text: Local workspace
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
  - heading "Owned campaign history 1024" [level=1]
  - text: Draft Process control terms Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched.
  - 'button "Dependencies: none unresolved"': Dependencies
  - button "Undo" [disabled]
  - button "Redo" [disabled]
  - button "Export"
  - button "Validate"
  - button "Preflight & run"
  - tablist "System workflows":
    - tab "Model"
    - tab "Connections"
    - tab "Deployment"
    - tab "Experiments" [selected]
    - tab "Results"
    - button "XDL source"
  - text: Draft revision
  - code: "2"
  - text: 3 elements · 2 connections Execution scope Owned reference
  - heading "Experiments" [level=2]
  - paragraph: Author bounded intent, inspect actual events, and assess immutable evidence.
  - button "Edit scenario XDL"
  - tablist "Experiment sections":
    - tab "Scenario"
    - tab "Timeline"
    - tab "Assertions"
    - tab "Campaigns" [selected]
  - heading "Bounded parameter campaign" [level=3]
  - paragraph: Each child receives its own immutable snapshot. Concurrency and resource budgets are rechecked by the backend.
  - text: Parameter matrix (JSON)
  - textbox "Parameter matrix (JSON)": "{\"gain\": [0.5, 0.8, 1.2]}"
  - text: Maximum runs
  - spinbutton "Maximum runs": "8"
  - text: Concurrency
  - spinbutton "Concurrency": "1"
  - strong: "3"
  - text: child runs in this matrix Budget 8
  - button "Create campaign"
  - heading "Campaign history" [level=3]
  - heading "No campaign selected" [level=3]
  - text: Preview a finite matrix, create the campaign, and inspect each child independently. Local project · Saved on backend Authoritative XDL · Layout stored separately 1 provider(s) available
```

# Test source

```ts
  1  | import { test, expect, type Page } from "@playwright/test";
  2  | import { parse, stringify } from "yaml";
  3  | import { connectStudio } from "./connect-studio";
  4  |
  5  | async function request(page: Page, path: string, method = "GET", body?: any, revision?: number) {
  6  |   return page.evaluate(async ({ path, method, body, revision }) => {
  7  |     const { csrfToken } = await fetch("/api/v1/session").then(r => r.json());
  8  |     const r = await fetch("/api/v1" + path, { method, headers: {
  9  |       "Content-Type": "application/json", "X-CSRF-Token": csrfToken,
  10 |       ...(revision ? { "If-Match": String(revision) } : {}),
  11 |       ...(method === "POST" ? { "Idempotency-Key": crypto.randomUUID() } : {}),
  12 |     }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  13 |     const v = await r.json();
  14 |     if (!r.ok) throw new Error(`Owned campaign setup ${r.status} ${v.code}`);
  15 |     return v;
  16 |   }, { path, method, body, revision });
  17 | }
  18 | async function prepare(page: Page, width: number) {
  19 |   let project = await request(page, "/projects", "POST", { name: `Owned campaign history ${width}` });
  20 |   const [docId, doc]: any = Object.entries(project.documents).find(([, d]: any) => parse(d.content).kind === "Scenario")!;
  21 |   const source = parse(doc.content);
  22 |   source.extensions["io.xverse.experiment"].parameters.find((p: any) => p.id === "duration").value = .2;
  23 |   project = await request(page, `/projects/${project.projectId}/documents/${docId}`, "PUT", { content: stringify(source), format: "yaml" }, project.revision);
  24 |   const pf = await request(page, `/projects/${project.projectId}/preflights`, "POST", { revision: project.revision });
  25 |   expect(pf.status).toBe("ready");
  26 |   await page.evaluate(({ project, pf }) => {
  27 |     localStorage.setItem("studio.projectId", project.projectId);
  28 |     localStorage.setItem("studio.selection." + project.projectId, JSON.stringify(pf.selection));
  29 |   }, { project, pf });
  30 |   await page.reload();
  31 |   await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  32 |   await page.getByRole("tab", { name: "Campaigns", exact: true }).click();
  33 |   return { project, pf };
  34 | }
  35 | for (const width of [1024, 1440]) {
  36 |   test(`campaign workflow: retained native children reopen without scheduling at ${width}`, async ({ page }, info) => {
  37 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  38 |     await connectStudio(page, info);
  39 |     const { project, pf } = await prepare(page, width);
  40 |     const made = await request(page, "/campaigns", "POST", { snapshotId: pf.snapshotId, matrix: { gain: [.5, .8] }, budget: { maxRuns: 2, maxTotalSeconds: 1 }, concurrency: 1, stopPolicy: "continue" });
  41 |     await expect.poll(async () => (await request(page, `/campaigns/${made.campaignId}`)).status, { timeout: 30000 }).toBe("complete");
  42 |     const before = await request(page, `/campaigns/${made.campaignId}`);
  43 |     const runsBefore = (await request(page, "/runs")).items.map((r: any) => r.runId);
  44 |     const writes: string[] = [];
  45 |     page.on("request", r => { if (!["GET", "HEAD", "OPTIONS"].includes(r.method())) writes.push(r.method() + " " + new URL(r.url()).pathname); });
  46 |     const refresh = page.getByRole("button", { name: "Refresh campaign history", exact: true });
> 47 |     await expect(refresh).toBeVisible();
     |                           ^ Error: expect(locator).toBeVisible() failed
  48 |     await refresh.focus(); await page.keyboard.press("Enter");
  49 |     const open = page.getByRole("button", { name: `Inspect campaign ${made.campaignId}`, exact: true });
  50 |     await expect(open).toBeVisible();
  51 |     await open.focus(); await page.keyboard.press("Enter");
  52 |     const panel = page.getByRole("region", { name: "Selected campaign", exact: true });
  53 |     await expect(panel).toContainText(pf.snapshotId);
  54 |     await expect(panel).toContainText(project.projectId);
  55 |     for (const c of before.children) {
  56 |       await expect(panel).toContainText(c.childKey);
  57 |       await expect(panel).toContainText(c.runId);
  58 |     }
  59 |     await expect(panel).toContainText("complete");
  60 |     expect(await request(page, `/campaigns/${made.campaignId}`)).toEqual(before);
  61 |     expect((await request(page, "/runs")).items.map((r: any) => r.runId)).toEqual(runsBefore);
  62 |     expect(writes).toEqual([]);
  63 |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  64 |     await info.attach("retained-campaign", { contentType: "application/json", body: JSON.stringify({ projectId: project.projectId, campaignId: made.campaignId, snapshotId: pf.snapshotId, children: before.children, noInspectionWrites: true }) });
  65 |   });
  66 | }
  67 |
```
