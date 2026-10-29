# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: run-reconnect.spec.ts >> run session: lost Start acknowledgement survives refresh and resolves one run from two tabs
- Location: tests/e2e/run-reconnect.spec.ts:749:5

# Error details

```
TimeoutError: apiRequestContext.get: Timeout 15000ms exceeded.
Call log:
  - → GET http://127.0.0.1:48669/api/v1/runs
    - user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/156.0.8078.4 Safari/537.36
    - accept: */*
    - accept-encoding: gzip,deflate,br
    - cookie: studio_session=<redacted>

```

# Page snapshot

```yaml
- generic [ref=f2e3]:
  - link "Skip to workspace" [ref=f2e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=f2e5]:
    - button "X-Verse Studio home" [ref=f2e6] [cursor=pointer]:
      - generic [ref=f2e7]: X
      - generic [ref=f2e8]: X-VERSE STUDIO
    - generic [ref=f2e10]: Local workspace
    - generic [ref=f2e12]: REFERENCE PREVIEW
    - button "Environment" [ref=f2e13] [cursor=pointer]
    - generic "Local operator" [ref=f2e20]: LO
  - generic [ref=f2e21]:
    - navigation "Main navigation" [ref=f2e22]:
      - button "Workspace" [ref=f2e23] [cursor=pointer]
      - button "Catalog" [ref=f2e30] [cursor=pointer]
      - button "Laboratory" [ref=f2e37] [cursor=pointer]:
        - generic [ref=f2e41]: Lab
      - button "Compatibility and environment" [ref=f2e42] [cursor=pointer]:
        - generic [ref=f2e48]: Settings
      - generic [ref=f2e49]: v0.1
    - main [ref=f2e50]:
      - generic [ref=f2e52]:
        - text: Run accepted by the backend. Browser disconnection will not duplicate or terminate it.
        - button "Dismiss notice" [ref=f2e56] [cursor=pointer]
      - generic [ref=f2e59]:
        - generic [ref=f2e60]:
          - generic [ref=f2e61]:
            - button "Workspace" [ref=f2e62] [cursor=pointer]
            - generic [ref=f2e65]: System
          - generic [ref=f2e66]:
            - heading "Lost Start acknowledgement" [level=1] [ref=f2e73]
            - generic [ref=f2e74]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f2e75]: Process control terms
            - generic [ref=f2e78]: rev 2
        - generic [ref=f2e79]:
          - 'button "Dependencies: none unresolved" [ref=f2e80] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f2e81]
          - button "Redo" [disabled] [ref=f2e82]
          - button "Export" [ref=f2e83] [cursor=pointer]
          - button "Validate" [ref=f2e86] [cursor=pointer]
          - button "Preflight & run" [ref=f2e89] [cursor=pointer]
      - tablist "System workflows" [ref=f2e92]:
        - tab "Model" [ref=f2e93] [cursor=pointer]
        - tab "Connections" [ref=f2e99] [cursor=pointer]
        - tab "Deployment" [ref=f2e104] [cursor=pointer]
        - tab "Experiments" [ref=f2e107] [cursor=pointer]
        - tab "Results 1" [selected] [ref=f2e110] [cursor=pointer]:
          - text: Results
          - generic [ref=f2e113]: "1"
        - button "XDL source" [ref=f2e115] [cursor=pointer]
      - generic [ref=f2e118]:
        - generic [ref=f2e119]:
          - text: Draft revision
          - code [ref=f2e121]: "2"
        - generic [ref=f2e122]: 3 elements · 2 connections
        - generic [ref=f2e123]:
          - text: Run snapshot
          - code [ref=f2e124]: snap-4481ea0
          - generic [ref=f2e125]: stopped
          - button "Draft matches run inputs" [ref=f2e126] [cursor=pointer]
      - generic [ref=f2e127]:
        - generic [ref=f2e128]:
          - generic [ref=f2e129]:
            - heading "Run results stopped" [level=2] [ref=f2e130]:
              - text: Run results
              - generic [ref=f2e131]: stopped
            - paragraph [ref=f2e132]:
              - code [ref=f2e133]: run-2a526be2-3101-4935-b9bd-6745112dc055
              - generic [ref=f2e134]:
                - text: Snapshot
                - code [ref=f2e135]: snap-4481ea0a-74e9
          - generic [ref=f2e136]:
            - generic [ref=f2e137]:
              - text: Recorded run
              - combobox "Recorded run" [ref=f2e138]:
                - option "run-2a526be2-3101-4935-b9bd-6745112dc055 · stopped" [selected]
            - button "Frozen inputs" [ref=f2e139] [cursor=pointer]
            - button "Rerun frozen inputs" [ref=f2e142] [cursor=pointer]
            - button "Refresh" [ref=f2e145] [cursor=pointer]
        - region "Run controls" [ref=f2e148]:
          - generic [ref=f2e149]:
            - generic [ref=f2e150]:
              - button "Stop" [disabled] [ref=f2e151]
              - generic [ref=f2e154]: Not available while the run is stopped.
            - generic [ref=f2e155]:
              - button "Cancel" [disabled] [ref=f2e156]
              - generic [ref=f2e157]: Not available while the run is stopped.
            - paragraph [ref=f2e158]: "Not admitted for this run: pause, resume, step, reset, set_parameter. The backend rejects them; absence of a button is not support."
        - generic [ref=f2e159]:
          - generic [ref=f2e160]:
            - text: Execution
            - strong [ref=f2e161]: stopped
            - text: Lifecycle outcome
          - generic [ref=f2e163]:
            - text: Assertion verdict
            - strong [ref=f2e164]: Not evaluated
            - text: Separate assessment result
          - generic [ref=f2e166]:
            - text: Cleanup
            - strong [ref=f2e167]: complete
            - text: Owned-resource release
          - generic [ref=f2e169]:
            - text: Evidence
            - strong [ref=f2e170]: complete
            - text: Integrity and completeness
        - generic [ref=f2e172]:
          - generic [ref=f2e173]: owned_reference
          - generic [ref=f2e174]: owned_reference · Source clocks retained · Browser presentation is bounded
          - generic [ref=f2e175]: Retained history available
        - tablist "Result sections" [ref=f2e177]:
          - tab "Observations" [selected] [ref=f2e178] [cursor=pointer]
          - tab "Events & logs 0" [ref=f2e179] [cursor=pointer]:
            - text: Events & logs
            - generic [ref=f2e180]: "0"
          - tab "Diagnosis" [ref=f2e181] [cursor=pointer]
          - tab "Evidence" [ref=f2e182] [cursor=pointer]
          - tab "Compare" [ref=f2e183] [cursor=pointer]
          - tab "Annotations" [ref=f2e184] [cursor=pointer]
        - generic [ref=f2e185]:
          - generic [ref=f2e186]:
            - generic [ref=f2e187]:
              - heading "Recorded observations" [level=3] [ref=f2e188]
              - paragraph [ref=f2e189]: Original source time and quantity semantics are preserved.
            - generic [ref=f2e190]:
              - button "Table view" [ref=f2e191] [cursor=pointer]
              - button "Replay observations" [ref=f2e192] [cursor=pointer]
          - generic [ref=f2e193]:
            - generic [ref=f2e194]:
              - generic [ref=f2e195]:
                - text: Element reference
                - combobox "Element reference" [ref=f2e196]:
                  - option "All elements" [selected]
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#controller"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#plant"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#state-flow"
              - generic [ref=f2e197]:
                - text: Emitter provider
                - combobox "Emitter provider" [ref=f2e198]:
                  - option "All reported identities" [selected]
                  - option "studio.reference"
              - generic [ref=f2e199]:
                - text: Observer
                - combobox "Observer" [ref=f2e200]:
                  - option "All reported identities" [selected]
                  - option "state-observer"
              - generic [ref=f2e201]:
                - text: Observation field
                - combobox "Observation field" [ref=f2e202]:
                  - option "All reported fields" [selected]
                  - option "control"
                  - option "measured"
                  - option "target"
                  - option "value"
              - generic [ref=f2e203]:
                - text: Time basis
                - combobox "Time basis" [ref=f2e204]:
                  - option "No time window" [selected]
                  - option "Original source clock"
                  - option "Recorded receipt UTC"
            - paragraph [ref=f2e205]: The field predicate selects records and the returned value field. Original immutable payloads remain inspectable in Events.
            - generic [ref=f2e206]:
              - button "Apply evidence filters" [ref=f2e207] [cursor=pointer]
              - button "Reset evidence filters" [ref=f2e208] [cursor=pointer]
          - status "Evidence read quality" [ref=f2e209]:
            - generic [ref=f2e210]: "Matched: 30 · Returned: 30 · Omitted from page: 0"
            - generic [ref=f2e211]: "missingSourceTime: 0"
            - generic [ref=f2e212]: "malformedSourceTime: 0"
            - generic [ref=f2e213]: "otherClock: 0"
            - generic [ref=f2e214]: "missingReceiptTime: 0"
            - generic [ref=f2e215]: "unsupportedReceiptEncoding: 0"
            - generic [ref=f2e216]: "Reader integrity: valid"
          - generic [ref=f2e217]:
            - paragraph [ref=f2e218]: "Original clock: simulation-time · tick unit: microsecond. Exact endpoint ticks: 0 to 2900000."
            - img "Recorded observation chart in simulation-time. Exact source ticks; missing time is not plotted." [ref=f2e219]:
              - generic [ref=f2e220]: "0.000"
              - generic [ref=f2e222]: "0.2500"
              - generic [ref=f2e224]: "0.5000"
              - generic [ref=f2e226]: "0.7500"
              - generic [ref=f2e228]: "1.000"
              - generic [ref=f2e230]: "0"
              - generic [ref=f2e231]: "2900000"
            - generic [ref=f2e359]:
              - generic [ref=f2e360]: control
              - generic [ref=f2e362]: measured
              - generic [ref=f2e364]: target
              - generic [ref=f2e366]: value
          - generic [ref=f2e368]:
            - button "Previous observation page" [disabled] [ref=f2e369]
            - button "Next observation page" [disabled] [ref=f2e370]
          - generic [ref=f2e371]:
            - generic [ref=f2e372]:
              - text: "Clock:"
              - strong [ref=f2e373]: simulation-time
            - generic [ref=f2e374]:
              - text: "Unit:"
              - strong [ref=f2e375]: 1, 1, 1, 1
            - generic [ref=f2e376]:
              - text: "Reduction:"
              - strong [ref=f2e377]: page
        - generic [ref=f2e378]:
          - heading "Input and evidence provenance" [level=3] [ref=f2e379]
          - generic [ref=f2e380]:
            - generic [ref=f2e381]:
              - term [ref=f2e382]: Snapshot
              - definition [ref=f2e383]: snap-4481ea0a-74e9-4555-a65d-5ab4d6615d7f
            - generic [ref=f2e384]:
              - term [ref=f2e385]: Plan digest
              - definition [ref=f2e386]: sha256:99800af486b0a78f46f223bac5e240cf931b0c0909bad3d3dc83770b4b5e4eb0
            - generic [ref=f2e387]:
              - term [ref=f2e388]: Provider
              - definition [ref=f2e389]: studio.reference
            - generic [ref=f2e390]:
              - term [ref=f2e391]: Clock uncertainty
              - definition [ref=f2e392]: Not declared
            - generic [ref=f2e393]:
              - term [ref=f2e394]: Coverage
              - definition [ref=f2e395]: Unknown
          - group [ref=f2e396]:
            - generic "Inspect exact data" [ref=f2e397] [cursor=pointer]
      - generic [ref=f2e398]:
        - generic [ref=f2e399]: Local project · Saved on backend
        - generic [ref=f2e402]: Authoritative XDL · Layout stored separately
        - generic [ref=f2e403]: 1 provider(s) available
```

# Test source

```ts
  646 |   let facet = "partial";
  647 |   const versions: number[] = [],
  648 |     writes: string[] = [];
  649 |   await page.route(`**/api/v1/runs/${fixture.runId}`, async (route) => {
  650 |     const response = await route.fetch(),
  651 |       metadata = await response.json();
  652 |     versions.push(metadata.stateVersion);
  653 |     await route.fulfill({ response, json: { ...metadata, evidence: facet } });
  654 |   });
  655 |   page.on("request", (r) => {
  656 |     if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
  657 |       writes.push(r.method() + " " + r.url());
  658 |   });
  659 |   await showRun(page, project.projectId, fixture.runId);
  660 |   await expect(page.locator(".stream-indicator")).toHaveText("Connected");
  661 |   const evidence = page
  662 |       .locator(".status-card")
  663 |       .filter({ has: page.getByText("Evidence", { exact: true }) }),
  664 |     execution = page
  665 |       .locator(".status-card")
  666 |       .filter({ has: page.getByText("Execution", { exact: true }) });
  667 |   await expect(evidence).toContainText(/partial/i);
  668 |   await expect(execution).toContainText(/unknown/i);
  669 |   facet = "invalid";
  670 |   await expect(evidence).toContainText(/invalid/i, { timeout: 8000 });
  671 |   await expect(execution).toContainText(/unknown/i);
  672 |   facet = "unavailable";
  673 |   await expect(evidence).toContainText(/unavailable/i, { timeout: 8000 });
  674 |   await expect(execution).toContainText(/unknown/i);
  675 |   expect(new Set(versions).size).toBe(1);
  676 |   expect(sha(journalPath)).toBe(journalHash);
  677 |   expect(sha(snapshotPath)).toBe(snapshotHash);
  678 |   const actual = await page.request
  679 |     .get(`/api/v1/runs/${fixture.runId}`)
  680 |     .then((r) => r.json());
  681 |   expect(actual.evidence).toBe("partial");
  682 |   expect(actual.stateVersion).toBe(versions[0]);
  683 |   expect(writes).toEqual([]);
  684 |   await testInfo.attach("same-version-ui-negative-scope", {
  685 |     body: JSON.stringify({
  686 |       scope:
  687 |         "controlled HTTP metadata UI negative only; source journal and snapshot unchanged",
  688 |       evidenceScope: fixture.evidenceScope,
  689 |       requestedStates: ["partial", "invalid", "unavailable"],
  690 |       stateVersions: versions,
  691 |       journalSha256: journalHash,
  692 |       snapshotSha256: snapshotHash,
  693 |       backendEvidence: actual.evidence,
  694 |       mutations: writes,
  695 |     }),
  696 |     contentType: "application/json",
  697 |   });
  698 |   await page.screenshot({
  699 |     path: testInfo.outputPath(
  700 |       "same-version-evidence-unavailable-ui-fixture.png",
  701 |     ),
  702 |     fullPage: true,
  703 |   });
  704 | });
  705 | async function openTimedProject(page: Page, name: string, duration: number) {
  706 |   const project = await makeProject(page, name);
  707 |   await page.evaluate(
  708 |     async ({ project, duration }) => {
  709 |       const { csrfToken } = await fetch("/api/v1/session").then((r) =>
  710 |         r.json(),
  711 |       );
  712 |       const r = await fetch(`/api/v1/projects/${project.projectId}/edits`, {
  713 |         method: "POST",
  714 |         headers: {
  715 |           "Content-Type": "application/json",
  716 |           "X-CSRF-Token": csrfToken,
  717 |           "If-Match": String(project.revision),
  718 |         },
  719 |         body: JSON.stringify({
  720 |           baseRevision: project.revision,
  721 |           edits: [
  722 |             { kind: "set_parameter", parameterId: "duration", value: duration },
  723 |           ],
  724 |         }),
  725 |       });
  726 |       if (!r.ok) throw Error(await r.text());
  727 |       localStorage.setItem("studio.projectId", project.projectId);
  728 |     },
  729 |     { project, duration },
  730 |   );
  731 |   await page.reload();
  732 |   await expect(page.locator(".project-header h1")).toHaveText(name);
  733 |   return project;
  734 | }
  735 | /** Records the Idempotency-Key of every Start request this page sends. */
  736 | function recordStarts(page: Page, keys: string[]) {
  737 |   page.on("request", (request) => {
  738 |     if (
  739 |       request.method() === "POST" &&
  740 |       new URL(request.url()).pathname === "/api/v1/runs"
  741 |     )
  742 |       keys.push(request.headers()["idempotency-key"]);
  743 |   });
  744 | }
  745 | async function projectRuns(page: Page, projectId: string) {
> 746 |   const list = await page.request.get("/api/v1/runs").then((r) => r.json());
      |                                   ^ TimeoutError: apiRequestContext.get: Timeout 15000ms exceeded.
  747 |   return list.items.filter((r: any) => r.projectId === projectId);
  748 | }
  749 | test("run session: lost Start acknowledgement survives refresh and resolves one run from two tabs", async ({
  750 |   page,
  751 |   context,
  752 | }, testInfo) => {
  753 |   test.setTimeout(90000);
  754 |   await connectStudio(page, testInfo);
  755 |   const project = await openTimedProject(page, "Lost Start acknowledgement", 3);
  756 |   const keys: string[] = [];
  757 |   recordStarts(page, keys);
  758 |   let dropped = 0;
  759 |   // Fault injection: the backend receives and accepts Start; only its response is lost.
  760 |   await page.route("**/api/v1/runs", async (route) => {
  761 |     if (route.request().method() !== "POST" || dropped) return route.fallback();
  762 |     dropped++;
  763 |     await route.fetch();
  764 |     await route.abort("connectionreset");
  765 |   });
  766 |   await page
  767 |     .getByRole("button", { name: "Preflight & run", exact: true })
  768 |     .click();
  769 |   await page
  770 |     .getByRole("button", { name: "Start frozen snapshot", exact: true })
  771 |     .click();
  772 |   await expect(page.getByText("REQUEST_UNAVAILABLE")).toBeVisible();
  773 |   expect(dropped).toBe(1);
  774 |   const accepted = await projectRuns(page, project.projectId);
  775 |   expect(accepted).toHaveLength(1);
  776 |   await page.reload();
  777 |   const notice = page.locator("[data-pending-start]");
  778 |   await expect(notice).toHaveAttribute("data-pending-start", "unacknowledged");
  779 |   await expect(notice).toContainText("Start acknowledgement not received");
  780 |   // A fresh preflight carries a new request identity; it cannot Start meanwhile.
  781 |   await page
  782 |     .getByRole("button", { name: "Preflight & run", exact: true })
  783 |     .click();
  784 |   const freshStart = page.getByRole("button", {
  785 |     name: "Start frozen snapshot",
  786 |     exact: true,
  787 |   });
  788 |   await expect(page.locator("#start-blocked-reason")).toContainText(
  789 |     "An earlier Start acknowledgement is unresolved",
  790 |   );
  791 |   await expect(freshStart).toBeDisabled();
  792 |   await page
  793 |     .getByRole("button", { name: "Back to draft", exact: true })
  794 |     .click();
  795 |   const second = await context.newPage();
  796 |   recordStarts(second, keys);
  797 |   await second.goto("/");
  798 |   await expect(second.locator("[data-pending-start]")).toContainText(
  799 |     "Retry same Start",
  800 |   );
  801 |   await Promise.all(
  802 |     [page, second].map((tab) =>
  803 |       tab
  804 |         .getByRole("button", { name: "Retry same Start", exact: true })
  805 |         .click(),
  806 |     ),
  807 |   );
  808 |   for (const tab of [page, second]) {
  809 |     await expect(
  810 |       tab.getByRole("heading", { name: /Run results/ }),
  811 |     ).toBeVisible();
  812 |     await expect(tab.locator(".run-identity code").first()).toHaveText(
  813 |       accepted[0].runId,
  814 |     );
  815 |   }
  816 |   await expect(page.locator("[data-pending-start]")).toHaveCount(0);
  817 |   // Three Start deliveries of one request identity; the backend owns exactly one run.
  818 |   expect(keys).toHaveLength(3);
  819 |   expect(new Set(keys).size).toBe(1);
  820 |   expect(await projectRuns(page, project.projectId)).toHaveLength(1);
  821 |   await second.close();
  822 |   await page.screenshot({
  823 |     path: testInfo.outputPath("lost-start-two-tab-retry.png"),
  824 |     fullPage: true,
  825 |   });
  826 | });
  827 | test("run session: double Start, page close/reopen and a lost Stop acknowledgement keep one run and one command", async ({
  828 |   page,
  829 |   context,
  830 | }, testInfo) => {
  831 |   test.setTimeout(90000);
  832 |   await connectStudio(page, testInfo);
  833 |   const project = await openTimedProject(page, "Owned control receipts", 20);
  834 |   const keys: string[] = [];
  835 |   recordStarts(page, keys);
  836 |   await page
  837 |     .getByRole("button", { name: "Preflight & run", exact: true })
  838 |     .click();
  839 |   await page
  840 |     .getByRole("button", { name: "Start frozen snapshot", exact: true })
  841 |     .dblclick();
  842 |   await expect(
  843 |     page.getByRole("heading", { name: /Run results/ }),
  844 |   ).toBeVisible();
  845 |   expect(new Set(keys).size).toBe(1);
  846 |   const [run] = await projectRuns(page, project.projectId);
```
