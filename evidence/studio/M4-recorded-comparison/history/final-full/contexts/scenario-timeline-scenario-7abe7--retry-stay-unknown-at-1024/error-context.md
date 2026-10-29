# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline.spec.ts >> scenario timeline: malformed transport contracts and HTTP retry stay unknown at 1024
- Location: tests/e2e/scenario-timeline.spec.ts:324:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('alert')
Expected substring: "Timeline availability is unknown"
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toContainText" getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('alert') with timeout 10000ms
  - waiting for getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('alert')

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
  - heading "Owned timeline 1024" [level=1]
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
    - tab "Results 1"
    - button "XDL source"
  - text: Draft revision
  - code: "3"
  - text: 3 elements · 2 connections Run snapshot
  - code: snap-3ca3756
  - text: stopped
  - button "Draft differs from run inputs (1 document, 0 elements, 0 parameters)"
  - heading "Experiments" [level=2]
  - paragraph: Author bounded intent, inspect actual events, and assess immutable evidence.
  - button "Edit scenario XDL"
  - tablist "Experiment sections":
    - tab "Scenario"
    - tab "Timeline" [selected]
    - tab "Assertions"
    - tab "Campaigns"
  - region "Selected run timeline":
    - heading "Selected run timeline" [level=3]
    - paragraph: Frozen intentions, recorded events and immutable evaluation windows.
    - button "Inspect selected run timeline"
    - paragraph: Read-only inspection. Same-axis placement does not prove causality or an intended effect. Source time and receipt time remain separate.
    - text: Timeline clock
    - combobox "Timeline clock":
      - option "Frozen System default" [selected]
    - paragraph: Inspect to read the exact run inputs and available clocks. Changing the clock requires a new inspection.
  - text: Local project · Saved on backend Authoritative XDL · Layout stored separately 1 provider(s) available
```

# Test source

```ts
  305 |   await page.getByRole("tab", { name: "Timeline", exact: true }).focus();
  306 |   await page.keyboard.press("Enter");
  307 |   const panel = page.getByRole("region", {
  308 |     name: "Selected run timeline",
  309 |     exact: true,
  310 |   });
  311 |   return {
  312 |     panel,
  313 |     inspect: panel.getByRole("button", {
  314 |       name: "Inspect selected run timeline",
  315 |       exact: true,
  316 |     }),
  317 |     heading: panel.getByRole("heading", {
  318 |       name: "Selected run timeline",
  319 |       exact: true,
  320 |     }),
  321 |   };
  322 | }
  323 | for (const width of [1024, 1440]) {
  324 |   test(`scenario timeline: malformed transport contracts and HTTP retry stay unknown at ${width}`, async ({
  325 |     page,
  326 |   }, info) => {
  327 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  328 |     await connectStudio(page, info);
  329 |     const made = await prepare(page, width);
  330 |     const { panel, inspect, heading } = await openTimeline(page);
  331 |     const writes: string[] = [];
  332 |     page.on("request", (r) => {
  333 |       if (!["GET", "HEAD", "OPTIONS"].includes(r.method()))
  334 |         writes.push(r.method());
  335 |     });
  336 |     let mode = "http";
  337 |     await page.route(
  338 |       `**/api/v1/runs/${made.run.runId}/timeline*`,
  339 |       async (route) => {
  340 |         if (mode === "real") return route.continue();
  341 |         if (mode === "http")
  342 |           return route.fulfill({
  343 |             status: 503,
  344 |             json: {
  345 |               code: "LABELLED_TIMELINE_UNAVAILABLE",
  346 |               message: "Labelled transport fixture",
  347 |             },
  348 |           });
  349 |         const value = structuredClone(made.timeline);
  350 |         if (mode === "snapshot") value.snapshotId = "foreign-snapshot";
  351 |         if (mode === "version") value.timelineVersion = "99.0";
  352 |         if (mode === "authority") value.readOnly = false;
  353 |         if (mode === "clock")
  354 |           value.items.find(
  355 |             (r: any) => r.position.status === "aligned",
  356 |           ).position.clockDomain = "unmapped-device-clock";
  357 |         if (mode === "metric")
  358 |           value.items.find(
  359 |             (r: any) => r.layer === "evaluation" && r.kind === "metric",
  360 |           ).verdict = "pass";
  361 |         if (mode === "window")
  362 |           value.items.find(
  363 |             (r: any) => r.layer === "evaluation",
  364 |           ).window.endTick = "-1";
  365 |         if (mode === "complete-coverage") {
  366 |           const row = value.items.find(
  367 |             (r: any) => r.layer === "evaluation" && r.kind === "assertion",
  368 |           );
  369 |           row.coverage = null;
  370 |           row.partial = null;
  371 |         }
  372 |         if (mode === "running-verdict")
  373 |           value.items.find(
  374 |             (r: any) => r.layer === "evaluation" && r.kind === "assertion",
  375 |           ).executionStatus = "running";
  376 |         if (mode === "definition-context")
  377 |           value.assessmentDefinitions.items[0].definition.scenarioRef =
  378 |             "xdl://foreign/scenario/foreign";
  379 |         if (mode === "definition-shape")
  380 |           value.assessmentDefinitions.items[0].definition.expression =
  381 |             "unsupported-string";
  382 |         if (mode === "duplicate") {
  383 |           value.items[1] = structuredClone(value.items[0]);
  384 |         }
  385 |         await route.fulfill({ json: value });
  386 |       },
  387 |     );
  388 |     for (const next of [
  389 |       "http",
  390 |       "snapshot",
  391 |       "version",
  392 |       "authority",
  393 |       "clock",
  394 |       "metric",
  395 |       "window",
  396 |       "duplicate",
  397 |       "definition-context",
  398 |       "definition-shape",
  399 |       "complete-coverage",
  400 |       "running-verdict",
  401 |     ]) {
  402 |       mode = next;
  403 |       await inspect.focus();
  404 |       await page.keyboard.press("Enter");
> 405 |       await expect(panel.getByRole("alert")).toContainText(
      |                                              ^ Error: expect(locator).toContainText(expected) failed
  406 |         "Timeline availability is unknown",
  407 |       );
  408 |       await expect(panel.getByRole("alert")).toBeFocused();
  409 |       await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(0);
  410 |     }
  411 |     mode = "real";
  412 |     await inspect.focus();
  413 |     await page.keyboard.press("Enter");
  414 |     await expect(heading).toBeFocused();
  415 |     await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(
  416 |       made.timeline.items.length,
  417 |     );
  418 |     expect(writes).toEqual([]);
  419 |     expect(await request(page, `/projects/${made.project.projectId}`)).toEqual(
  420 |       made.project,
  421 |     );
  422 |   });
  423 |   test(`scenario timeline: labelled exact large ticks, gaps and unsupported clock remain separate at ${width}`, async ({
  424 |     page,
  425 |   }, info) => {
  426 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  427 |     await connectStudio(page, info);
  428 |     const made = await prepare(page, width);
  429 |     const { panel, inspect, heading } = await openTimeline(page);
  430 |     await page.route(
  431 |       `**/api/v1/runs/${made.run.runId}/timeline*`,
  432 |       async (route) => {
  433 |         const clock =
  434 |           new URL(route.request().url()).searchParams.get("clockDomain") ||
  435 |           "simulation-time";
  436 |         const value = structuredClone(made.timeline),
  437 |           sample = made.timeline.items.find(
  438 |             (r: any) => r.kind === "observation.available",
  439 |           );
  440 |         value.evidenceScope = "fixture";
  441 |         value.intentClockCodec = null;
  442 |         value.clockDomain = clock;
  443 |         value.tickUnit = clock === "simulation-time" ? "microsecond" : null;
  444 |         value.clockDomains = [
  445 |           { id: "simulation-time", declared: true, observed: true },
  446 |           { id: "device-time", declared: false, observed: true },
  447 |         ];
  448 |         value.clockDomainsComplete = false;
  449 |         value.items = ["9007199254740993", "9007199254740995"].map(
  450 |           (tick, i) => ({
  451 |             ...structuredClone(sample),
  452 |             id: "recorded:labelled-large-" + i,
  453 |             eventId: "labelled-large-" + i,
  454 |             evidenceScope: "fixture",
  455 |             sourceTime: {
  456 |               tick,
  457 |               clockDomain: "simulation-time",
  458 |               resolution: "microsecond",
  459 |               uncertainty: 2,
  460 |             },
  461 |             position: {
  462 |               tick,
  463 |               clockDomain: "simulation-time",
  464 |               tickUnit: "microsecond",
  465 |               status: clock === "simulation-time" ? "aligned" : "unplaced",
  466 |               reason: clock === "simulation-time" ? null : "CLOCK_NOT_SELECTED",
  467 |             },
  468 |           }),
  469 |         );
  470 |         value.items.push({
  471 |           ...structuredClone(sample),
  472 |           id: "recorded:labelled-unknown",
  473 |           eventId: "labelled-unknown",
  474 |           evidenceScope: "fixture",
  475 |           sourceTime: {
  476 |             tick: "7",
  477 |             clockDomain: "device-time",
  478 |             resolution: "unknown",
  479 |           },
  480 |           position: {
  481 |             tick: "7",
  482 |             clockDomain: "device-time",
  483 |             tickUnit: null,
  484 |             status: "unplaced",
  485 |             reason: "TICK_ENCODING_UNADMITTED",
  486 |           },
  487 |         });
  488 |         value.nextCursor = null;
  489 |         value.counts = {
  490 |           ...value.counts,
  491 |           matchedRows: 3,
  492 |           returnedRows: 3,
  493 |           unplacedRows: clock === "simulation-time" ? 1 : 3,
  494 |           recordedInputs: 3,
  495 |           recordedInputsConsidered: 3,
  496 |           intentInputs: 0,
  497 |           intentInputsConsidered: 0,
  498 |           evaluationInputsConsidered: 0,
  499 |         };
  500 |         value.inputsComplete = {
  501 |           recorded: false,
  502 |           intents: true,
  503 |           evaluations: true,
  504 |         };
  505 |         value.recorded.collectionStatus = "partial";
```
