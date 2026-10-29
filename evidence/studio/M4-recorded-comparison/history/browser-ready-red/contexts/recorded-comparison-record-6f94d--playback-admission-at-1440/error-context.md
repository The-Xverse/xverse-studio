# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: recorded-comparison.spec.ts >> recorded comparison: immutable provenance, unequal windows and playback admission at 1440
- Location: tests/e2e/recorded-comparison.spec.ts:43:7

# Error details

```
TimeoutError: locator.selectOption: Timeout 15000ms exceeded.
Call log:
  - waiting for getByLabel('Baseline run', { exact: true })

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
    - generic [ref=f1e12]: REFERENCE PREVIEW
    - button "Environment" [ref=f1e13] [cursor=pointer]
    - generic "Local operator" [ref=f1e20]: LO
  - generic [ref=f1e21]:
    - navigation "Main navigation" [ref=f1e22]:
      - button "Workspace" [ref=f1e23] [cursor=pointer]
      - button "Catalog" [ref=f1e30] [cursor=pointer]
      - button "Laboratory" [ref=f1e37] [cursor=pointer]:
        - generic [ref=f1e41]: Lab
      - button "Compatibility and environment" [ref=f1e42] [cursor=pointer]:
        - generic [ref=f1e48]: Settings
      - generic [ref=f1e49]: v0.1
    - main [ref=f1e50]:
      - generic [ref=f1e51]:
        - generic [ref=f1e52]:
          - generic [ref=f1e53]:
            - button "Workspace" [ref=f1e54] [cursor=pointer]
            - generic [ref=f1e57]: System
          - generic [ref=f1e58]:
            - heading "Recorded comparison 1440" [level=1] [ref=f1e65]
            - generic [ref=f1e66]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e67]: Process control terms
            - generic [ref=f1e70]: rev 4
        - generic [ref=f1e71]:
          - 'button "Dependencies: none unresolved" [ref=f1e72] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f1e73]
          - button "Redo" [disabled] [ref=f1e74]
          - button "Export" [ref=f1e75] [cursor=pointer]
          - button "Validate" [ref=f1e78] [cursor=pointer]
          - button "Preflight & run" [ref=f1e81] [cursor=pointer]
      - tablist "System workflows" [ref=f1e84]:
        - tab "Model" [ref=f1e85] [cursor=pointer]
        - tab "Connections" [ref=f1e91] [cursor=pointer]
        - tab "Deployment" [ref=f1e96] [cursor=pointer]
        - tab "Experiments" [ref=f1e99] [cursor=pointer]
        - tab "Results 1" [selected] [ref=f1e102] [cursor=pointer]:
          - text: Results
          - generic [ref=f1e105]: "1"
        - button "XDL source" [ref=f1e107] [cursor=pointer]
      - generic [ref=f1e110]:
        - generic [ref=f1e111]:
          - text: Draft revision
          - code [ref=f1e113]: "4"
        - generic [ref=f1e114]: 3 elements · 2 connections
        - generic [ref=f1e115]:
          - text: Run snapshot
          - code [ref=f1e116]: snap-ffd8bd5
          - generic [ref=f1e117]: stopped
          - button "Draft differs from run inputs (1 document, 0 elements, 1 parameter)" [ref=f1e118] [cursor=pointer]
      - generic [ref=f1e119]:
        - generic [ref=f1e120]:
          - generic [ref=f1e121]:
            - heading "Run results stopped" [level=2] [ref=f1e122]:
              - text: Run results
              - generic [ref=f1e123]: stopped
            - paragraph [ref=f1e124]:
              - code [ref=f1e125]: run-119ea1ef-d7eb-4544-b9a1-88afb5d752ad
              - generic [ref=f1e126]:
                - text: Snapshot
                - code [ref=f1e127]: snap-ffd8bd5d-26f9
          - generic [ref=f1e128]:
            - generic [ref=f1e129]:
              - text: Recorded run
              - combobox "Recorded run" [ref=f1e130]:
                - option "run-119ea1ef-d7eb-4544-b9a1-88afb5d752ad · stopped" [selected]
                - option "run-2696c720-07fb-4f5e-96cb-0dd664b4e5e2 · stopped"
                - option "run-2c5b3f90-6581-4e5d-bb22-cbad97da1f99 · stopped"
            - button "Frozen inputs" [ref=f1e131] [cursor=pointer]
            - button "Rerun frozen inputs" [ref=f1e134] [cursor=pointer]
            - button "Refresh" [ref=f1e137] [cursor=pointer]
        - region "Run controls" [ref=f1e140]:
          - generic [ref=f1e141]:
            - generic [ref=f1e142]:
              - button "Stop" [disabled] [ref=f1e143]
              - generic [ref=f1e146]: Not available while the run is stopped.
            - generic [ref=f1e147]:
              - button "Cancel" [disabled] [ref=f1e148]
              - generic [ref=f1e149]: Not available while the run is stopped.
            - paragraph [ref=f1e150]: "Not admitted for this run: pause, resume, step, reset, set_parameter. The backend rejects them; absence of a button is not support."
        - generic [ref=f1e151]:
          - generic [ref=f1e152]:
            - text: Execution
            - strong [ref=f1e153]: stopped
            - text: Lifecycle outcome
          - generic [ref=f1e155]:
            - text: Assertion verdict
            - strong [ref=f1e156]: Not evaluated
            - text: Separate assessment result
          - generic [ref=f1e158]:
            - text: Cleanup
            - strong [ref=f1e159]: complete
            - text: Owned-resource release
          - generic [ref=f1e161]:
            - text: Evidence
            - strong [ref=f1e162]: complete
            - text: Integrity and completeness
        - generic [ref=f1e164]:
          - generic [ref=f1e165]: owned_reference
          - generic [ref=f1e166]: owned_reference · Source clocks retained · Browser presentation is bounded
          - generic [ref=f1e167]: Retained history available
        - tablist "Result sections" [ref=f1e169]:
          - tab "Observations" [ref=f1e170] [cursor=pointer]
          - tab "Events & logs 0" [ref=f1e171] [cursor=pointer]:
            - text: Events & logs
            - generic [ref=f1e172]: "0"
          - tab "Diagnosis" [ref=f1e173] [cursor=pointer]
          - tab "Evidence" [ref=f1e174] [cursor=pointer]
          - tab "Compare" [active] [selected] [ref=f1e175] [cursor=pointer]
          - tab "Annotations" [ref=f1e176] [cursor=pointer]
        - generic [ref=f1e177]:
          - generic [ref=f1e178]:
            - heading "Baseline comparison" [level=3] [ref=f1e179]
            - paragraph [ref=f1e180]: Check model, deployment, parameters, capabilities, units, and clocks before interpreting differences.
            - generic [ref=f1e181]:
              - generic [ref=f1e182]:
                - text: Baseline run
                - combobox "Baseline run" [ref=f1e183]:
                  - option "Select a recorded run" [selected]
                  - option "run-2696c720-07f · stopped"
                  - option "run-2c5b3f90-658 · stopped"
                  - option "run-2467fc11-c69 · stopped"
                  - option "run-3d48fdba-ce0 · stopped"
                  - option "run-4fca8ffd-00c · stopped"
              - button "Inspect compatibility" [disabled] [ref=f1e184]
          - complementary [ref=f1e185]:
            - heading "Replay and rerun" [level=3] [ref=f1e186]
            - paragraph [ref=f1e187]: Replay re-presents recorded observations. It does not execute the model or establish determinism.
            - paragraph [ref=f1e188]: A rerun creates a new identity after fresh preflight of the current draft.
            - button "Preflight a new run" [ref=f1e189] [cursor=pointer]
      - generic [ref=f1e192]:
        - generic [ref=f1e193]: Local project · Saved on backend
        - generic [ref=f1e196]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e197]: 1 provider(s) available
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
  36 |   await page.getByRole('tab', { name: 'Results', exact: false }).click();
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
> 48 |     await baseline.selectOption(runs[0].runId);
     |                    ^ TimeoutError: locator.selectOption: Timeout 15000ms exceeded.
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
