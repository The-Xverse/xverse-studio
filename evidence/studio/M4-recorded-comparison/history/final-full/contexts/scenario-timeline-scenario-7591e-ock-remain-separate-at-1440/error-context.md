# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline.spec.ts >> scenario timeline: labelled exact large ticks, gaps and unsupported clock remain separate at 1440
- Location: tests/e2e/scenario-timeline.spec.ts:423:7

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
  506 |         value.recorded.gapCount = 1;
  507 |         value.recorded.gapsComplete = true;
  508 |         value.recorded.gaps = [
  509 |           {
  510 |             reason: "Labelled transport fixture gap",
  511 |             detailUnavailable: false,
  512 |             sourceTime: {},
  513 |           },
  514 |         ];
  515 |         await route.fulfill({ json: value });
  516 |       },
  517 |     );
  518 |     await inspect.focus();
  519 |     await page.keyboard.press("Enter");
> 520 |     await expect(heading).toBeFocused();
      |                           ^ Error: expect(locator).toBeFocused() failed
  521 |     await expect(panel).toContainText("9007199254740993");
  522 |     await expect(panel).toContainText("9007199254740995");
  523 |     await expect(panel).toContainText("Labelled transport fixture gap");
  524 |     await expect(panel).toContainText("recorded evidence incomplete");
  525 |     const markers = panel.locator("svg .timeline-marker");
  526 |     await expect(markers).toHaveCount(2);
  527 |     const xs = await markers.evaluateAll((nodes) =>
  528 |       nodes.map((n) => Number(n.querySelector("circle")!.getAttribute("cx"))),
  529 |     );
  530 |     expect(xs[0]).toBeLessThan(xs[1]);
  531 |     await panel
  532 |       .getByLabel("Timeline clock", { exact: true })
  533 |       .selectOption("device-time");
  534 |     await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(0);
  535 |     await inspect.focus();
  536 |     await page.keyboard.press("Enter");
  537 |     await expect(heading).toBeFocused();
  538 |     await expect(panel.locator("svg .timeline-marker")).toHaveCount(0);
  539 |     await expect(panel).toContainText("TICK_ENCODING_UNADMITTED");
  540 |     expect((await request(page, `/runs/${made.run.runId}`)).journalDigest).toBe(
  541 |       made.run.journalDigest,
  542 |     );
  543 |     expect(await request(page, `/projects/${made.project.projectId}`)).toEqual(
  544 |       made.project,
  545 |     );
  546 |     await info.attach("fixture-scope", {
  547 |       body: "Labelled transport projection only; original journal and snapshot are unchanged. No device clock support or physical execution claim.",
  548 |       contentType: "text/plain",
  549 |     });
  550 |   });
  551 |   test(`scenario timeline: native canonical pages preserve identities and reject changed evaluation cursors at ${width}`, async ({
  552 |     page,
  553 |   }, info) => {
  554 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  555 |     await connectStudio(page, info);
  556 |     const made = await prepare(page, width, true);
  557 |     const { panel, inspect, heading } = await openTimeline(page);
  558 |     await inspect.focus();
  559 |     await page.keyboard.press("Enter");
  560 |     await expect(heading).toBeFocused();
  561 |     const expected: string[] = [],
  562 |       seen: string[] = [];
  563 |     let canonical = await request(
  564 |       page,
  565 |       `/runs/${made.run.runId}/timeline?limit=100`,
  566 |     );
  567 |     while (true) {
  568 |       expected.push(...canonical.items.map((r: any) => r.id));
  569 |       if (!canonical.nextCursor) break;
  570 |       canonical = await request(
  571 |         page,
  572 |         `/runs/${made.run.runId}/timeline?limit=100&cursor=${encodeURIComponent(canonical.nextCursor)}`,
  573 |       );
  574 |     }
  575 |     expect(expected.length).toBeGreaterThan(200);
  576 |     while (true) {
  577 |       seen.push(
  578 |         ...(await panel
  579 |           .locator("tr[data-timeline-id]")
  580 |           .evaluateAll((nodes) =>
  581 |             nodes.map((n) => n.getAttribute("data-timeline-id")!),
  582 |           )),
  583 |       );
  584 |       const next = panel.getByRole("button", {
  585 |         name: "Next timeline page",
  586 |         exact: true,
  587 |       });
  588 |       if (await next.isDisabled()) break;
  589 |       await next.focus();
  590 |       await page.keyboard.press("Enter");
  591 |       await expect(heading).toBeFocused();
  592 |     }
  593 |     expect(seen).toEqual(expected);
  594 |     expect(new Set(seen).size).toBe(expected.length);
  595 |     await panel
  596 |       .getByRole("button", { name: "Previous timeline page", exact: true })
  597 |       .focus();
  598 |     await page.keyboard.press("Enter");
  599 |     await expect(heading).toBeFocused();
  600 |     await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(100);
  601 |     // A new real immutable evaluation changes the bound cursor identity; it is a deliberate setup mutation.
  602 |     const d = (await request(page, `/runs/${made.run.runId}/definitions`))
  603 |       .items[0];
  604 |     await request(page, `/runs/${made.run.runId}/evaluations`, "POST", {
  605 |       snapshotId: made.run.snapshotId,
  606 |       definitionRef: d.definitionRef,
  607 |       definitionDigest: d.definitionDigest,
  608 |       evidenceRefs: [made.run.runId + ":reference-journal"],
  609 |     });
  610 |     await panel
  611 |       .getByRole("button", { name: "Next timeline page", exact: true })
  612 |       .focus();
  613 |     await page.keyboard.press("Enter");
  614 |     await expect(panel.getByRole("alert")).toContainText(
  615 |       "TIMELINE_CURSOR_STALE",
  616 |     );
  617 |     await expect(panel.getByRole("alert")).toBeFocused();
  618 |     await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(0);
  619 |     await inspect.focus();
  620 |     await page.keyboard.press("Enter");
```
