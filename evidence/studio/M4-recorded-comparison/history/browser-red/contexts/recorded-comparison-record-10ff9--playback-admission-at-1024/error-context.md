# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: recorded-comparison.spec.ts >> recorded comparison: immutable provenance, unequal windows and playback admission at 1024
- Location: tests/e2e/recorded-comparison.spec.ts:43:7

# Error details

```
TimeoutError: locator.click: Timeout 15000ms exceeded.
Call log:
  - waiting for getByRole('tab', { name: 'Results', exact: true })

```

# Page snapshot

```yaml
- generic [ref=f1e3]:
  - link "Skip to workspace" [ref=f1e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=f1e5]:
    - button "X-Verse Studio home" [ref=f1e6] [cursor=pointer]:
      - generic [ref=f1e7]: X
      - generic [ref=f1e8]: X-VERSE STUDIO
    - generic [ref=f1e10]: Local workspace
    - button "Environment" [ref=f1e12] [cursor=pointer]
    - generic "Local operator" [ref=f1e19]: LO
  - generic [ref=f1e20]:
    - navigation "Main navigation" [ref=f1e21]:
      - button "Workspace" [ref=f1e22] [cursor=pointer]
      - button "Catalog" [ref=f1e29] [cursor=pointer]
      - button "Laboratory" [ref=f1e36] [cursor=pointer]:
        - generic [ref=f1e40]: Lab
      - button "Compatibility and environment" [ref=f1e41] [cursor=pointer]:
        - generic [ref=f1e47]: Settings
      - generic [ref=f1e48]: v0.1
    - main [ref=f1e49]:
      - generic [ref=f1e50]:
        - generic [ref=f1e51]:
          - generic [ref=f1e52]:
            - button "Workspace" [ref=f1e53] [cursor=pointer]
            - generic [ref=f1e56]: System
          - generic [ref=f1e57]:
            - heading "Recorded comparison 1024" [level=1] [ref=f1e64]
            - generic [ref=f1e65]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e66]: Process control terms
        - generic [ref=f1e69]:
          - 'button "Dependencies: none unresolved" [ref=f1e70] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f1e71]
          - button "Redo" [disabled] [ref=f1e72]
          - button "Export" [ref=f1e73] [cursor=pointer]
          - button "Validate" [ref=f1e76] [cursor=pointer]
          - button "Preflight & run" [ref=f1e79] [cursor=pointer]
      - tablist "System workflows" [ref=f1e82]:
        - tab "Model" [selected] [ref=f1e83] [cursor=pointer]
        - tab "Connections" [ref=f1e89] [cursor=pointer]
        - tab "Deployment" [ref=f1e94] [cursor=pointer]
        - tab "Experiments" [ref=f1e97] [cursor=pointer]
        - tab "Results 1" [ref=f1e100] [cursor=pointer]:
          - text: Results
          - generic [ref=f1e103]: "1"
        - button "XDL source" [ref=f1e105] [cursor=pointer]
      - generic [ref=f1e108]:
        - generic [ref=f1e109]:
          - text: Draft revision
          - code [ref=f1e111]: "4"
        - generic [ref=f1e112]: 3 elements · 2 connections
        - generic [ref=f1e113]:
          - text: Run snapshot
          - code [ref=f1e114]: snap-68ebe43
          - generic [ref=f1e115]: stopped
          - button "Draft differs from run inputs (1 document, 0 elements, 1 parameter)" [ref=f1e116] [cursor=pointer]
      - generic [ref=f1e117]:
        - complementary "Structured model navigation" [ref=f1e118]:
          - generic [ref=f1e119]:
            - heading "Process explorer" [level=2] [ref=f1e120]
            - button "View XDL source" [ref=f1e121] [cursor=pointer]
          - textbox "Search elements" [ref=f1e128]:
            - /placeholder: Find an element…
          - generic [ref=f1e129]:
            - strong [ref=f1e135]: reference-loop
            - generic [ref=f1e136]: "3"
            - button "Group by node" [ref=f1e137] [cursor=pointer]
          - generic [ref=f1e138]:
            - button "controller controller" [ref=f1e139] [cursor=pointer]:
              - generic [ref=f1e145]: controller
              - generic [ref=f1e146]: controller
            - button "plant plant" [ref=f1e147] [cursor=pointer]:
              - generic [ref=f1e153]: plant
              - generic [ref=f1e154]: plant
            - button "observer-node observer" [ref=f1e155] [cursor=pointer]:
              - generic [ref=f1e158]: observer-node
              - generic [ref=f1e159]: observer
          - generic [ref=f1e160]:
            - generic [ref=f1e161]: RESOURCES
            - button "reference-controller Component" [ref=f1e162] [cursor=pointer]:
              - generic [ref=f1e165]: reference-controller
              - generic [ref=f1e166]: Component
            - button "reference-plant Component" [ref=f1e167] [cursor=pointer]:
              - generic [ref=f1e170]: reference-plant
              - generic [ref=f1e171]: Component
            - button "reference-loop System" [ref=f1e172] [cursor=pointer]:
              - generic [ref=f1e175]: reference-loop
              - generic [ref=f1e176]: System
            - button "local-reference Deployment" [ref=f1e177] [cursor=pointer]:
              - generic [ref=f1e180]: local-reference
              - generic [ref=f1e181]: Deployment
            - button "reference-response Scenario" [ref=f1e182] [cursor=pointer]:
              - generic [ref=f1e185]: reference-response
              - generic [ref=f1e186]: Scenario
            - button "experiment-lite Profile" [ref=f1e187] [cursor=pointer]:
              - generic [ref=f1e190]: experiment-lite
              - generic [ref=f1e191]: Profile
            - button "studio-experiments Profile" [ref=f1e192] [cursor=pointer]:
              - generic [ref=f1e195]: studio-experiments
              - generic [ref=f1e196]: Profile
          - button "Add element" [ref=f1e198] [cursor=pointer]
        - region "Model canvas" [ref=f1e201]:
          - generic:
            - generic [ref=f1e202]:
              - generic [ref=f1e203]: LOGICAL MODEL
              - generic [ref=f1e204]: 1.0.0
            - generic [ref=f1e205]:
              - button "Table view" [ref=f1e206] [cursor=pointer]
              - button "Auto layout" [ref=f1e207] [cursor=pointer]
              - button "Save layout" [ref=f1e208] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f1e209]:
            - generic [ref=f1e211]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=f1e212] [cursor=pointer]:
                      - generic [ref=f1e215]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=f1e217] [cursor=pointer]:
                      - generic [ref=f1e220]: state-flow
                - generic:
                  - group [ref=f1e222]:
                    - generic [ref=f1e223]:
                      - generic [ref=f1e225]: controller
                      - strong [ref=f1e234]: controller
                      - code [ref=f1e235]: controller
                      - list "Named ports" [ref=f1e236]:
                        - listitem [ref=f1e237]:
                          - generic [aria-hidden] [ref=f1e238]: ←
                          - code [ref=f1e239]: controller-out
                          - generic [ref=f1e240]: output
                      - generic [ref=f1e241]:
                        - generic [ref=f1e242]: Logical element
                        - generic [ref=f1e243]: 1 ports
                  - group [ref=f1e245]:
                    - generic [ref=f1e246]:
                      - generic [ref=f1e248]: plant
                      - strong [ref=f1e257]: plant
                      - code [ref=f1e258]: plant
                      - list "Named ports" [ref=f1e259]:
                        - listitem [ref=f1e260]:
                          - generic [aria-hidden] [ref=f1e261]: →
                          - code [ref=f1e262]: plant-in
                          - generic [ref=f1e263]: input
                        - listitem [ref=f1e264]:
                          - generic [aria-hidden] [ref=f1e265]: ←
                          - code [ref=f1e266]: plant-out
                          - generic [ref=f1e267]: output
                      - generic [ref=f1e268]:
                        - generic [ref=f1e269]: Logical element
                        - generic [ref=f1e270]: 2 ports
                  - group [ref=f1e272]:
                    - generic [ref=f1e273]:
                      - generic [ref=f1e275]: observer
                      - strong [ref=f1e281]: observer-node
                      - code [ref=f1e282]: observer-node
                      - list "Named ports" [ref=f1e283]:
                        - listitem [ref=f1e284]:
                          - generic [aria-hidden] [ref=f1e285]: →
                          - code [ref=f1e286]: observer-in
                          - generic [ref=f1e287]: input
                      - generic [ref=f1e288]:
                        - generic [ref=f1e289]: Logical element
                        - generic [ref=f1e290]: 1 ports
            - generic "Control Panel" [ref=f1e292]:
              - button "Zoom In" [ref=f1e293] [cursor=pointer]
              - button "Zoom Out" [ref=f1e296] [cursor=pointer]
              - button "Fit View" [ref=f1e299] [cursor=pointer]
            - img "Mini Map" [ref=f1e303]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f1e308]:
          - heading "System inspector" [level=2] [ref=f1e310]
          - generic [ref=f1e316]:
            - heading "reference-loop" [level=3] [ref=f1e320]
            - paragraph [ref=f1e321]: Authoritative XDL System
            - generic [ref=f1e322]: Draft model
          - navigation "Model location" [ref=f1e323]:
            - button "reference-loop" [ref=f1e324] [cursor=pointer]
          - generic [ref=f1e325]:
            - button "Properties" [ref=f1e326] [cursor=pointer]
            - button "Parameters" [ref=f1e327] [cursor=pointer]
          - generic [ref=f1e328]:
            - paragraph [ref=f1e329]: Select an element in the graph or explorer to inspect its stable identity, role, realization, and placement.
            - generic [ref=f1e330]:
              - generic [ref=f1e331]:
                - term [ref=f1e332]: Namespace
                - definition [ref=f1e333]: org.xverse.studio.process-control
              - generic [ref=f1e334]:
                - term [ref=f1e335]: XDL version
                - definition [ref=f1e336]: xverse.io/xdl/v1alpha1
              - generic [ref=f1e337]:
                - term [ref=f1e338]: Resources
                - definition [ref=f1e339]: "7"
              - generic [ref=f1e340]:
                - term [ref=f1e341]: Evidence scope
                - definition [ref=f1e342]: Owned reference only
            - heading "Reference parameters" [level=4] [ref=f1e343]
            - generic [ref=f1e344]:
              - group "Setpoint and response" [ref=f1e345]:
                - generic [ref=f1e347]:
                  - generic [ref=f1e348]:
                    - text: Target
                    - generic [ref=f1e349]: "1"
                    - spinbutton "Target 1" [ref=f1e350]: "1"
                  - paragraph [ref=f1e351]: Normalized reference setpoint, dimensionless.
                  - generic [ref=f1e352]:
                    - generic [ref=f1e353]: Scenario XDL extension · default 1
                    - button "Apply" [disabled] [ref=f1e354]
                - generic [ref=f1e355]:
                  - generic [ref=f1e356]:
                    - text: Response gain
                    - generic [ref=f1e357]: "1"
                    - spinbutton "Response gain 1" [ref=f1e358]: "0.8"
                  - paragraph [ref=f1e359]: First-order response coefficient; gain × timestep must be at most one.
                  - generic [ref=f1e360]:
                    - generic [ref=f1e361]: Scenario XDL extension · default 0.8
                    - button "Apply" [disabled] [ref=f1e362]
                - generic [ref=f1e363]:
                  - generic [ref=f1e364]:
                    - text: Initial state
                    - generic [ref=f1e365]: "1"
                    - spinbutton "Initial state 1" [ref=f1e366]: "0"
                  - paragraph [ref=f1e367]: Initial normalized scalar state.
                  - generic [ref=f1e368]:
                    - generic [ref=f1e369]: Scenario XDL extension · default 0
                    - button "Apply" [disabled] [ref=f1e370]
              - group "Run horizon" [ref=f1e371]:
                - generic [ref=f1e373]:
                  - generic [ref=f1e374]:
                    - text: Duration
                    - generic [ref=f1e375]: s
                    - spinbutton "Duration s" [ref=f1e376]: "0.9"
                  - paragraph [ref=f1e377]: Requested simulation horizon, in seconds; at most 3,000 samples.
                  - generic [ref=f1e378]:
                    - generic [ref=f1e379]: Scenario XDL extension · default 5
                    - button "Apply" [disabled] [ref=f1e380]
                - generic [ref=f1e381]:
                  - generic [ref=f1e382]:
                    - text: Time step
                    - generic [ref=f1e383]: s
                    - spinbutton "Time step s" [ref=f1e384]: "0.1"
                  - paragraph [ref=f1e385]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                  - generic [ref=f1e386]:
                    - generic [ref=f1e387]: Scenario XDL extension · default 0.1
                    - button "Apply" [disabled] [ref=f1e388]
              - group "Instrument faults" [ref=f1e389]:
                - generic [ref=f1e391]:
                  - generic [ref=f1e392]:
                    - text: Reference fault
                    - generic [ref=f1e393]: "1"
                    - combobox "Reference fault 1" [ref=f1e394]:
                      - option "none" [selected]
                      - option "stuck-sensor"
                  - paragraph [ref=f1e395]: Owned model fault only; stuck-sensor freezes the reported observation.
                  - generic [ref=f1e396]:
                    - generic [ref=f1e397]: Scenario XDL extension · default none
                    - button "Apply" [disabled] [ref=f1e398]
          - generic [ref=f1e399]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f1e404]:
        - generic [ref=f1e405]: Local project · Saved on backend
        - generic [ref=f1e408]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e409]: 1 provider(s) available
```

# Test source

```ts
  1  | import { test, expect, type Page } from "@playwright/test";
  2  | import { readFileSync } from "node:fs";
  3  | import path from "node:path";
  4  | import { connectStudio } from "./connect-studio";
  5  |
  6  | async function request(page: Page, endpoint: string, method = "GET", body?: any, revision?: number) {
  7  |   return page.evaluate(async ({ endpoint, method, body, revision }) => {
  8  |     const { csrfToken } = await fetch('/api/v1/session').then(r => r.json());
  9  |     const response = await fetch('/api/v1' + endpoint, { method, headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken,
  10 |       ...(revision === undefined ? {} : { 'If-Match': String(revision) }), ...(method === 'POST' ? { 'Idempotency-Key': crypto.randomUUID() } : {}) },
  11 |       ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  12 |     const value = await response.json();
  13 |     if (!response.ok) throw new Error(`Owned comparison setup ${response.status} ${value.code}`);
  14 |     return value;
  15 |   }, { endpoint, method, body, revision });
  16 | }
  17 | async function setup(page: Page, width: number) {
  18 |   let project = await request(page, '/projects', 'POST', { name: `Recorded comparison ${width}`, blueprintRef: 'reference-process-control' });
  19 |   const runs: any[] = [];
  20 |   for (const [gain, duration] of [[.5, .6], [.8, .6], [.8, .9]]) {
  21 |     project = await request(page, `/projects/${project.projectId}/edits`, 'POST', { baseRevision: project.revision, edits: [
  22 |       { kind: 'set_parameter', parameterId: 'gain', value: gain }, { kind: 'set_parameter', parameterId: 'duration', value: duration }] }, project.revision);
  23 |     const pf = await request(page, `/projects/${project.projectId}/preflights`, 'POST', { revision: project.revision });
  24 |     expect(pf.status).toBe('ready');
  25 |     const accepted = await request(page, '/runs', 'POST', { snapshotId: pf.snapshotId, preflightId: pf.preflightId });
  26 |     await expect.poll(async () => (await request(page, '/runs/' + accepted.runId)).state, { timeout: 20000 }).toBe('stopped');
  27 |     const run = await request(page, '/runs/' + accepted.runId);
  28 |     expect(run.evidence).toBe('complete'); expect(run.cleanup).toBe('complete'); runs.push(run);
  29 |   }
  30 |   await page.evaluate(({ project, run }) => {
  31 |     localStorage.setItem('studio.projectId', project.projectId);
  32 |     localStorage.setItem('studio.lastRun', run.runId);
  33 |     localStorage.setItem('studio.lastRun.' + project.projectId, run.runId);
  34 |   }, { project, run: runs[1] });
  35 |   await page.reload();
> 36 |   await page.getByRole('tab', { name: 'Results', exact: true }).click();
     |                                                                 ^ TimeoutError: locator.click: Timeout 15000ms exceeded.
  37 |   await expect(page.getByLabel('Recorded run', { exact: true })).toHaveValue(runs[1].runId);
  38 |   await page.getByRole('tab', { name: 'Compare', exact: true }).click();
  39 |   return { project, runs };
  40 | }
  41 | const report = (page: Page) => page.getByRole('region', { name: 'Recorded comparison report', exact: true });
  42 | for (const width of [1024, 1440]) {
  43 |   test(`recorded comparison: immutable provenance, unequal windows and playback admission at ${width}`, async ({ page }, info) => {
  44 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  45 |     await connectStudio(page, info);
  46 |     const { project, runs } = await setup(page, width);
  47 |     const baseline = page.getByLabel('Baseline run', { exact: true });
  48 |     await baseline.selectOption(runs[0].runId);
  49 |     const writes: string[] = [];
  50 |     page.on('request', r => { if (r.method() !== 'GET' && r.url().includes('/api/v1/')) writes.push(new URL(r.url()).pathname); });
  51 |     await page.getByRole('button', { name: 'Inspect compatibility', exact: true }).click();
  52 |     await expect(page.getByRole('heading', { name: 'Comparison report', exact: true })).toBeVisible();
  53 |     await expect(report(page)).toContainText('Compatible recorded windows');
  54 |     await expect(report(page)).toContainText(runs[0].snapshotId);
  55 |     await expect(report(page)).toContainText(runs[1].snapshotId);
  56 |     const parameters = report(page).getByRole('table', { name: 'Frozen configuration differences' }).getByRole('row', { name: /^Parameters/ });
  57 |     await expect(parameters).toContainText('different');
  58 |     await expect(parameters).toContainText('0.5'); await expect(parameters).toContainText('0.8');
  59 |     await expect(report(page).getByRole('table', { name: 'Recorded field results' })).toContainText('600000');
  60 |     await baseline.selectOption(runs[2].runId);
  61 |     await expect(report(page)).toHaveCount(0);
  62 |     await page.getByRole('button', { name: 'Inspect compatibility', exact: true }).click();
  63 |     await expect(report(page)).toContainText('Pairing blocked');
  64 |     await expect(report(page)).toContainText('OBSERVATION_WINDOW_INCOMPATIBLE');
  65 |     await expect(report(page)).toContainText('900000');
  66 |     expect(writes).toEqual(['/api/v1/comparisons', '/api/v1/comparisons']);
  67 |     await page.screenshot({ path: info.outputPath('recorded-comparison.png'), fullPage: true });
  68 |     expect(await request(page, '/projects/' + project.projectId)).toEqual(project);
  69 |     await page.getByRole('button', { name: 'Open recorded playback', exact: true }).click();
  70 |     await expect(page.getByRole('tab', { name: 'Observations', exact: true })).toHaveAttribute('aria-selected', 'true');
  71 |     const playback = page.getByRole('button', { name: 'Replay observations', exact: true });
  72 |     await expect(playback).toBeEnabled(); await playback.click();
  73 |     expect(writes).toEqual(['/api/v1/comparisons', '/api/v1/comparisons']);
  74 |     await expect(page.getByLabel('Recorded run', { exact: true })).toHaveValue(runs[1].runId);
  75 |     await page.getByRole('tab', { name: 'Compare', exact: true }).click();
  76 |     const pfResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/projects/${project.projectId}/preflights`));
  77 |     await page.getByRole('button', { name: 'Preflight a new run', exact: true }).click();
  78 |     const pf = await (await pfResponse).json(); expect(pf.status).toBe('ready');
  79 |     expect(pf.snapshotId).not.toBe(runs[1].snapshotId);
  80 |     await expect(page.getByRole('button', { name: 'Start frozen snapshot', exact: true })).toBeEnabled();
  81 |     const root = process.env.STUDIO_BROWSER_DATA!;
  82 |     const frozen = JSON.parse(readFileSync(path.join(root, 'snapshots', pf.snapshotId, 'snapshot.json'), 'utf8'));
  83 |     expect(frozen.configuration.duration).toBe(.9);
  84 |     const old = JSON.parse(readFileSync(path.join(root, 'snapshots', runs[1].snapshotId, 'snapshot.json'), 'utf8'));
  85 |     expect(old.configuration.duration).toBe(.6);
  86 |     expect((await request(page, '/runs')).items.filter((r: any) => r.projectId === project.projectId)).toHaveLength(3);
  87 |     expect(writes).toEqual(['/api/v1/comparisons', '/api/v1/comparisons', `/api/v1/projects/${project.projectId}/preflights`]);
  88 |     await page.getByRole('button', { name: 'Back to draft', exact: true }).click();
  89 |     await info.attach('recorded-comparison-boundaries.json', { contentType: 'application/json', body: JSON.stringify({ viewport: width, runIds: runs.map(r => r.runId), snapshotIds: runs.map(r => r.snapshotId), actualNativeRuns: 3, comparisonAndPlaybackCreatedNoRuns: true, freshDraftPreflightOnly: pf.snapshotId, explicitStartStillRequired: true, canonicalProjectUnchanged: true }) });
  90 |   });
  91 | }
  92 |
```
