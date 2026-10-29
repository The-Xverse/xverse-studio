# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline.spec.ts >> scenario timeline: held actual read preserves focus at 1024
- Location: tests/e2e/scenario-timeline.spec.ts:627:9

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false

Call Log:
- Timeout 30000ms exceeded while waiting on the predicate
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
            - heading "Owned timeline 1024" [level=1] [ref=f1e64]
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
        - tab "Model" [ref=f1e83] [cursor=pointer]
        - tab "Connections" [ref=f1e89] [cursor=pointer]
        - tab "Deployment" [ref=f1e94] [cursor=pointer]
        - tab "Experiments" [selected] [ref=f1e97] [cursor=pointer]
        - tab "Results 1" [ref=f1e100] [cursor=pointer]:
          - text: Results
          - generic [ref=f1e103]: "1"
        - button "XDL source" [ref=f1e105] [cursor=pointer]
      - generic [ref=f1e108]:
        - generic [ref=f1e109]:
          - text: Draft revision
          - code [ref=f1e111]: "3"
        - generic [ref=f1e112]: 3 elements · 2 connections
        - generic [ref=f1e113]:
          - text: Run snapshot
          - code [ref=f1e114]: snap-896eafa
          - generic [ref=f1e115]: stopped
          - button "Draft differs from run inputs (1 document, 0 elements, 0 parameters)" [ref=f1e116] [cursor=pointer]
      - generic [ref=f1e117]:
        - generic [ref=f1e118]:
          - generic [ref=f1e119]:
            - heading "Experiments" [level=2] [ref=f1e120]
            - paragraph [ref=f1e121]: Author bounded intent, inspect actual events, and assess immutable evidence.
          - button "Edit scenario XDL" [ref=f1e122] [cursor=pointer]
        - tablist "Experiment sections" [ref=f1e125]:
          - tab "Scenario" [ref=f1e126] [cursor=pointer]
          - tab "Timeline" [active] [selected] [ref=f1e127] [cursor=pointer]
          - tab "Assertions" [ref=f1e128] [cursor=pointer]
          - tab "Campaigns" [ref=f1e129] [cursor=pointer]
        - region "Selected run timeline" [ref=f1e130]:
          - generic [ref=f1e131]:
            - generic [ref=f1e132]:
              - heading "Selected run timeline" [level=3] [ref=f1e133]
              - paragraph [ref=f1e134]: Frozen intentions, recorded events and immutable evaluation windows.
            - button "Inspect selected run timeline" [ref=f1e135] [cursor=pointer]
          - paragraph [ref=f1e136]: Read-only inspection. Same-axis placement does not prove causality or an intended effect. Source time and receipt time remain separate.
          - generic [ref=f1e137]:
            - text: Timeline clock
            - combobox "Timeline clock" [ref=f1e138]:
              - option "Frozen System default" [selected]
          - paragraph [ref=f1e139]: Inspect to read the exact run inputs and available clocks. Changing the clock requires a new inspection.
      - generic [ref=f1e140]:
        - generic [ref=f1e141]: Local project · Saved on backend
        - generic [ref=f1e144]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e145]: 1 provider(s) available
```

# Test source

```ts
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
  621 |     await expect(heading).toBeFocused();
  622 |     expect((await request(page, `/runs/${made.run.runId}`)).journalDigest).toBe(
  623 |       made.run.journalDigest,
  624 |     );
  625 |   });
  626 |   for (const destination of ["focus", "home"]) {
  627 |     test(`scenario timeline: held actual read preserves ${destination} at ${width}`, async ({
  628 |       page,
  629 |     }, info) => {
  630 |       await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  631 |       await connectStudio(page, info);
  632 |       const made = await prepare(page, width);
  633 |       const { panel, inspect, heading } = await openTimeline(page);
  634 |       let release!: () => void,
  635 |         ready = false,
  636 |         requests = 0;
  637 |       const gate = new Promise<void>((resolve) => (release = resolve));
  638 |       await page.route(
  639 |         `**/api/v1/runs/${made.run.runId}/timeline*`,
  640 |         async (route) => {
  641 |           requests++;
  642 |           const response = await route.fetch({ timeout: 30000 });
  643 |           ready = true;
  644 |           await gate;
  645 |           await route.fulfill({ response });
  646 |         },
  647 |       );
  648 |       try {
  649 |         await inspect.focus();
  650 |         await page.keyboard.press("Enter");
> 651 |         await expect.poll(() => ready, { timeout: 30000 }).toBe(true);
      |                                                            ^ Error: expect(received).toBe(expected) // Object.is equality
  652 |         await page.keyboard.press("Enter");
  653 |         expect(requests).toBe(1);
  654 |         const target = page.getByRole("button", {
  655 |           name:
  656 |             destination === "home"
  657 |               ? "X-Verse Studio home"
  658 |               : "Edit scenario XDL",
  659 |           exact: true,
  660 |         });
  661 |         await target.focus();
  662 |         if (destination === "home") await page.keyboard.press("Enter");
  663 |         release();
  664 |         if (destination === "focus") {
  665 |           await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(
  666 |             made.timeline.items.length,
  667 |           );
  668 |           await expect(target).toBeFocused();
  669 |           await expect(heading).not.toBeFocused();
  670 |         } else {
  671 |           await expect(panel).toHaveCount(0);
  672 |           await expect(
  673 |             page.getByRole("heading", {
  674 |               name: "Start with an example",
  675 |               exact: true,
  676 |             }),
  677 |           ).toBeVisible();
  678 |         }
  679 |         expect(requests).toBe(1);
  680 |         expect(
  681 |           await request(page, `/projects/${made.project.projectId}`),
  682 |         ).toEqual(made.project);
  683 |       } finally {
  684 |         release();
  685 |       }
  686 |     });
  687 |   }
  688 |   test(`scenario timeline: draft marker opens the typed form and saves canonical intent at ${width}`, async ({
  689 |     page,
  690 |   }, info) => {
  691 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  692 |     await connectStudio(page, info);
  693 |     const made = await prepare(page, width);
  694 |     const authored = page.getByRole("region", {
  695 |       name: "Authored scenario timeline",
  696 |       exact: true,
  697 |     });
  698 |     await expect(
  699 |       authored.getByLabel("Authoring clock", { exact: true }),
  700 |     ).toHaveValue("simulation-time");
  701 |     await authored
  702 |       .getByRole("button", {
  703 |         name: "Edit timeline step later-start",
  704 |         exact: true,
  705 |       })
  706 |       .focus();
  707 |     await page.keyboard.press("Enter");
  708 |     await page.getByLabel("Scheduled at", { exact: true }).fill("0.125");
  709 |     await page
  710 |       .getByRole("button", { name: "Save scenario item", exact: true })
  711 |       .focus();
  712 |     await page.keyboard.press("Enter");
  713 |     await expect(page.getByRole("dialog")).toHaveCount(0);
  714 |     const saved = await request(page, `/projects/${made.project.projectId}`),
  715 |       scenario: any = Object.values(saved.documents)
  716 |         .map((d: any) => parse(d.content))
  717 |         .find((r: any) => r.kind === "Scenario");
  718 |     expect(saved.revision).toBe(made.project.revision + 1);
  719 |     expect(scenario.spec.steps[0].schedule.at).toBe(0.125);
  720 |     expect(
  721 |       (await request(page, `/runs/${made.run.runId}/snapshot`)).snapshot,
  722 |     ).toEqual(made.snapshot);
  723 |     expect(
  724 |       await page.evaluate(
  725 |         () => document.documentElement.scrollWidth > innerWidth + 1,
  726 |       ),
  727 |     ).toBe(false);
  728 |   });
  729 | }
  730 |
  731 | for (const width of [1024, 1440]) {
  732 |   test(`scenario authoring completion: a newer item draft survives its earlier actual save at ${width}`, async ({
  733 |     page,
  734 |   }, info) => {
  735 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  736 |     await connectStudio(page, info);
  737 |     const made = await prepare(page, width);
  738 |     await page
  739 |       .getByRole("button", {
  740 |         name: "Edit timeline step later-start",
  741 |         exact: true,
  742 |       })
  743 |       .focus();
  744 |     await page.keyboard.press("Enter");
  745 |     const at = page.getByLabel("Scheduled at", { exact: true });
  746 |     await at.fill("0.125");
  747 |     let release!: () => void,
  748 |       ready = false,
  749 |       committed: any;
  750 |     const gate = new Promise<void>((resolve) => (release = resolve));
  751 |     await page.route(
```
