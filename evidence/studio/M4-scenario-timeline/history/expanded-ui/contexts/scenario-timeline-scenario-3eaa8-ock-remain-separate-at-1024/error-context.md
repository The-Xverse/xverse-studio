# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline.spec.ts >> scenario timeline: labelled exact large ticks, gaps and unsupported clock remain separate at 1024
- Location: tests/e2e/scenario-timeline.spec.ts:165:7

# Error details

```
Error: expect(received).toBeLessThan(expected)

Expected: < 0
Received:   0
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
        - generic [ref=f1e66]:
          - 'button "Dependencies: none unresolved" [ref=f1e67] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f1e68]
          - button "Redo" [disabled] [ref=f1e69]
          - button "Export" [ref=f1e70] [cursor=pointer]
          - button "Validate" [ref=f1e73] [cursor=pointer]
          - button "Preflight & run" [ref=f1e76] [cursor=pointer]
      - tablist "System workflows" [ref=f1e79]:
        - tab "Model" [ref=f1e80] [cursor=pointer]
        - tab "Connections" [ref=f1e86] [cursor=pointer]
        - tab "Deployment" [ref=f1e91] [cursor=pointer]
        - tab "Experiments" [selected] [ref=f1e94] [cursor=pointer]
        - tab "Results 1" [ref=f1e97] [cursor=pointer]:
          - text: Results
          - generic [ref=f1e100]: "1"
        - button "XDL source" [ref=f1e102] [cursor=pointer]
      - generic [ref=f1e105]:
        - generic [ref=f1e106]:
          - text: Draft revision
          - code [ref=f1e108]: "3"
        - generic [ref=f1e109]: 3 elements · 2 connections
        - generic [ref=f1e110]:
          - text: Run snapshot
          - code [ref=f1e111]: snap-6566550
          - generic [ref=f1e112]: stopped
      - generic [ref=f1e113]:
        - generic [ref=f1e114]:
          - generic [ref=f1e115]:
            - heading "Experiments" [level=2] [ref=f1e116]
            - paragraph [ref=f1e117]: Author bounded intent, inspect actual events, and assess immutable evidence.
          - button "Edit scenario XDL" [ref=f1e118] [cursor=pointer]
        - tablist "Experiment sections" [ref=f1e121]:
          - tab "Scenario" [ref=f1e122] [cursor=pointer]
          - tab "Timeline" [selected] [ref=f1e123] [cursor=pointer]
          - tab "Assertions" [ref=f1e124] [cursor=pointer]
          - tab "Campaigns" [ref=f1e125] [cursor=pointer]
        - region "Selected run timeline" [ref=f1e126]:
          - generic [ref=f1e127]:
            - generic [ref=f1e128]:
              - heading "Selected run timeline" [active] [level=3] [ref=f1e129]
              - paragraph [ref=f1e130]: Frozen intentions, recorded events and immutable evaluation windows.
            - button "Inspect selected run timeline" [ref=f1e131] [cursor=pointer]
          - paragraph [ref=f1e132]: Read-only inspection. Same-axis placement does not prove causality or an intended effect. Source time and receipt time remain separate.
          - generic [ref=f1e133]:
            - text: Timeline clock
            - combobox "Timeline clock" [ref=f1e134]:
              - option "Frozen System default" [selected]
              - option "simulation-time · declared"
              - option "device-time · observed only"
          - generic [ref=f1e135]:
            - generic [ref=f1e136]:
              - term [ref=f1e137]: Run
              - definition [ref=f1e138]: run-5e176e85-f351-4360-89d6-a3aefc63fc39
            - generic [ref=f1e139]:
              - term [ref=f1e140]: Snapshot
              - definition [ref=f1e141]: snap-6566550d-408c-4759-91aa-83f40c09896f
            - generic [ref=f1e142]:
              - term [ref=f1e143]: Snapshot digest
              - definition [ref=f1e144]: sha256:8a1ba0ac0884338a52e5614da347adc2214cb891bfa37269305afbc760c1688d
            - generic [ref=f1e145]:
              - term [ref=f1e146]: Executed project revision
              - definition [ref=f1e147]: "2"
            - generic [ref=f1e148]:
              - term [ref=f1e149]: Frozen Scenario
              - definition [ref=f1e150]: xdl://org.xverse.studio.process-control/scenario/reference-response
            - generic [ref=f1e151]:
              - term [ref=f1e152]: Frozen Deployment
              - definition [ref=f1e153]: xdl://org.xverse.studio.process-control/deployment/local-reference
            - generic [ref=f1e154]:
              - term [ref=f1e155]: Source clock
              - definition [ref=f1e156]: simulation-time
            - generic [ref=f1e157]:
              - term [ref=f1e158]: Admitted axis unit
              - definition [ref=f1e159]: microsecond
            - generic [ref=f1e160]:
              - term [ref=f1e161]: Intent display codec
              - definition [ref=f1e162]: Unavailable
            - generic [ref=f1e163]:
              - term [ref=f1e164]: Evidence scope
              - definition [ref=f1e165]: fixture
            - generic [ref=f1e166]:
              - term [ref=f1e167]: Journal integrity
              - definition [ref=f1e168]: valid
            - generic [ref=f1e169]:
              - term [ref=f1e170]: Evidence collection
              - definition [ref=f1e171]: partial
            - generic [ref=f1e172]:
              - term [ref=f1e173]: Timeline coverage
              - definition [ref=f1e174]: Not attested
          - paragraph [ref=f1e175]: Current draft differs from the executed revision or Scenario. This timeline uses only the frozen run inputs; current draft revision 3 is separate.
          - status [ref=f1e176]: Showing rows 1–3 of 3. 1 unplaced rows across the projection.
          - paragraph [ref=f1e177]: "Input completeness: intentions complete; recorded evidence incomplete; evaluation lookup complete. Clock list incomplete."
          - paragraph [ref=f1e178]: "Recorded gaps: 1. Gap list complete. No line bridges missing observations; an empty page does not establish absence."
          - paragraph [ref=f1e179]: "Gap 1: Labelled transport fixture gap"
          - figure "Selected-page markers · simulation-time · microsecond. Independent markers and half-open evaluation ranges; exact ticks are in the table." [ref=f1e180]:
            - img "Scenario intent, recorded events and evaluation windows; structured alternative in Timeline records table" [ref=f1e182]:
              - generic [ref=f1e183]: intent
              - generic [ref=f1e185]: recorded
              - generic [ref=f1e187]: evaluation
              - 'generic "observation.available: 9007199254740993" [ref=f1e189]'
              - 'generic "observation.available: 9007199254740995" [ref=f1e191]'
              - generic [ref=f1e193]: "9007199254740993"
              - generic [ref=f1e194]: "9007199254740995"
            - paragraph [ref=f1e195]: 2 of 2 placed page rows drawn. Overlapping markers retain separate identities in the table. This page is a display projection, not canonical coverage.
          - region "Scrollable timeline records" [ref=f1e196]:
            - table "Timeline records" [ref=f1e197]:
              - rowgroup [ref=f1e198]:
                - row [ref=f1e199]:
                  - columnheader "Layer / identity" [ref=f1e200]
                  - columnheader "Original time / placement" [ref=f1e201]
                  - columnheader "Observation or assessment" [ref=f1e202]
                  - columnheader "Scope / provenance" [ref=f1e203]
              - rowgroup [ref=f1e204]:
                - row [ref=f1e205]:
                  - cell [ref=f1e206]:
                    - strong [ref=f1e207]: recorded · observation.available
                    - code [ref=f1e208]: labelled-large-0
                  - 'cell "9007199254740993 simulation-time · microsecond Placed in selected clock Original metadata: {\"tick\":\"9007199254740993\",\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"uncertainty\":2} Receipt UTC: 2026-10-27T04:47:06.381153Z · unix_seconds_reference_v1" [ref=f1e209]':
                    - text: "9007199254740993"
                    - generic [ref=f1e210]: simulation-time · microsecond
                    - generic [ref=f1e211]: Placed in selected clock
                    - generic [ref=f1e212]: "Original metadata: {\"tick\":\"9007199254740993\",\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"uncertainty\":2}"
                    - generic [ref=f1e213]: "Receipt UTC: 2026-10-27T04:47:06.381153Z · unix_seconds_reference_v1"
                  - 'cell "observerRef: state-observer Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0 1" [ref=f1e214]':
                    - generic [ref=f1e215]: "observerRef: state-observer"
                    - generic [ref=f1e216]: "Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0 1"
                  - cell "fixture run-5e176e85-f351-4360-89d6-a3aefc63fc39:reference-journal" [ref=f1e217]:
                    - generic [ref=f1e218]: fixture
                    - generic [ref=f1e219]: run-5e176e85-f351-4360-89d6-a3aefc63fc39:reference-journal
                    - group [ref=f1e220]:
                      - generic "Inspect exact data" [ref=f1e221] [cursor=pointer]
                - row [ref=f1e222]:
                  - cell [ref=f1e223]:
                    - strong [ref=f1e224]: recorded · observation.available
                    - code [ref=f1e225]: labelled-large-1
                  - 'cell "9007199254740995 simulation-time · microsecond Placed in selected clock Original metadata: {\"tick\":\"9007199254740995\",\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"uncertainty\":2} Receipt UTC: 2026-10-27T04:47:06.381153Z · unix_seconds_reference_v1" [ref=f1e226]':
                    - text: "9007199254740995"
                    - generic [ref=f1e227]: simulation-time · microsecond
                    - generic [ref=f1e228]: Placed in selected clock
                    - generic [ref=f1e229]: "Original metadata: {\"tick\":\"9007199254740995\",\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"uncertainty\":2}"
                    - generic [ref=f1e230]: "Receipt UTC: 2026-10-27T04:47:06.381153Z · unix_seconds_reference_v1"
                  - 'cell "observerRef: state-observer Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0 1" [ref=f1e231]':
                    - generic [ref=f1e232]: "observerRef: state-observer"
                    - generic [ref=f1e233]: "Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0 1"
                  - cell "fixture run-5e176e85-f351-4360-89d6-a3aefc63fc39:reference-journal" [ref=f1e234]:
                    - generic [ref=f1e235]: fixture
                    - generic [ref=f1e236]: run-5e176e85-f351-4360-89d6-a3aefc63fc39:reference-journal
                    - group [ref=f1e237]:
                      - generic "Inspect exact data" [ref=f1e238] [cursor=pointer]
                - row [ref=f1e239]:
                  - cell [ref=f1e240]:
                    - strong [ref=f1e241]: recorded · observation.available
                    - code [ref=f1e242]: labelled-unknown
                  - 'cell "7 device-time · Unit unknown Unplaced: TICK_ENCODING_UNADMITTED Original metadata: {\"tick\":\"7\",\"clockDomain\":\"device-time\",\"resolution\":\"unknown\"} Receipt UTC: 2026-10-27T04:47:06.381153Z · unix_seconds_reference_v1" [ref=f1e243]':
                    - text: "7"
                    - generic [ref=f1e244]: device-time · Unit unknown
                    - generic [ref=f1e245]: "Unplaced: TICK_ENCODING_UNADMITTED"
                    - generic [ref=f1e246]: "Original metadata: {\"tick\":\"7\",\"clockDomain\":\"device-time\",\"resolution\":\"unknown\"}"
                    - generic [ref=f1e247]: "Receipt UTC: 2026-10-27T04:47:06.381153Z · unix_seconds_reference_v1"
                  - 'cell "observerRef: state-observer Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0 1" [ref=f1e248]':
                    - generic [ref=f1e249]: "observerRef: state-observer"
                    - generic [ref=f1e250]: "Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0 1"
                  - cell "fixture run-5e176e85-f351-4360-89d6-a3aefc63fc39:reference-journal" [ref=f1e251]:
                    - generic [ref=f1e252]: fixture
                    - generic [ref=f1e253]: run-5e176e85-f351-4360-89d6-a3aefc63fc39:reference-journal
                    - group [ref=f1e254]:
                      - generic "Inspect exact data" [ref=f1e255] [cursor=pointer]
          - generic [ref=f1e256]:
            - button "Previous timeline page" [disabled] [ref=f1e257]
            - button "Next timeline page" [disabled] [ref=f1e258]
          - list [ref=f1e259]:
            - listitem [ref=f1e260]: Same-axis placement is not causality or proof of an intended effect.
            - listitem [ref=f1e261]: Unplaced declarations and unknown clocks remain unsupported; receipt time is independent.
            - listitem [ref=f1e262]: Windowed evaluations retain their own exact evidence provenance and do not change lifecycle.
      - generic [ref=f1e263]:
        - generic [ref=f1e264]: Local project · Saved on backend
        - generic [ref=f1e267]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e268]: 1 provider(s) available
```

# Test source

```ts
  84  |     expect(await request(page,`/projects/${made.project.projectId}`)).toEqual(made.project);
  85  |     expect((await request(page,`/runs/${made.run.runId}/snapshot`)).snapshot).toEqual(made.snapshot);
  86  |     expect((await request(page,`/runs/${made.run.runId}`)).journalDigest).toBe(made.run.journalDigest);
  87  |     expect((await request(page,"/runs")).items.map((r:any) => r.runId)).toEqual(made.runIds);
  88  |     expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth+1)).toBe(false);
  89  |     expect(writes).toEqual([]); expect(errors).toEqual([]);
  90  |     await info.attach("owned-timeline-context",{body:JSON.stringify({runId:made.run.runId,snapshotId:made.snapshot.snapshotId,revision:made.snapshot.revision,projectRevision:made.project.revision,scope:made.timeline.evidenceScope}),contentType:"application/json"});
  91  |     await page.screenshot({path:info.outputPath("scenario-timeline.png"),fullPage:true});
  92  |   });
  93  | }
  94  |
  95  | for (const width of [1024,1440]) {
  96  |   test(`scenario authoring completion: held conditions acknowledgement preserves a reopened draft at ${width}`,async ({page},info) => {
  97  |     await page.setViewportSize({width,height:900}); await connectStudio(page,info);
  98  |     const made=await prepare(page,width);
  99  |     const open=page.getByRole("button",{name:"Edit initial conditions",exact:true});
  100 |     await open.focus(); await page.keyboard.press("Enter");
  101 |     await page.getByLabel("Scenario acceptance intent",{exact:true}).fill("First committed conditions");
  102 |     let release!: () => void;
  103 |     const released=new Promise<void>(resolve => release=resolve);
  104 |     let ready=false, committed:any=null, writes=0;
  105 |     await page.route(`**/api/v1/projects/${made.project.projectId}/edits`,async route => {
  106 |       if (route.request().method() !== "POST") return route.continue();
  107 |       writes++;
  108 |       const response=await route.fetch({timeout:30000}); committed=await response.json(); ready=true;
  109 |       await released; await route.fulfill({response});
  110 |     });
  111 |     try {
  112 |       await page.getByRole("button",{name:"Save scenario conditions",exact:true}).focus(); await page.keyboard.press("Enter");
  113 |       await expect.poll(() => ready,{timeout:30000}).toBe(true);
  114 |       await page.keyboard.press("Enter"); expect(writes).toBe(1);
  115 |       await page.keyboard.press("Escape");
  116 |       await open.focus(); await page.keyboard.press("Enter");
  117 |       const draft=page.getByLabel("Scenario acceptance intent",{exact:true});
  118 |       await draft.fill("Keep this newer unsaved draft"); await draft.focus();
  119 |       release();
  120 |       await expect.poll(async () => (await request(page,`/projects/${made.project.projectId}`)).revision).toBe(committed.revision);
  121 |       // Observe completion from the actual page transport, then preserve the newer form/focus.
  122 |       await expect(page.locator(".project-header")).toContainText(String(committed.revision));
  123 |       await expect(draft).toBeVisible(); await expect(draft).toHaveValue("Keep this newer unsaved draft"); await expect(draft).toBeFocused();
  124 |       expect(writes).toBe(1);
  125 |       expect((await request(page,`/runs/${made.run.runId}/snapshot`)).snapshot).toEqual(made.snapshot);
  126 |       await page.keyboard.press("Escape");
  127 |     } finally {release();}
  128 |   });
  129 | }
  130 |
  131 | async function openTimeline(page: Page) {
  132 |   await page.getByRole("tab",{name:"Timeline",exact:true}).focus(); await page.keyboard.press("Enter");
  133 |   const panel=page.getByRole("region",{name:"Selected run timeline",exact:true});
  134 |   return {panel,inspect:panel.getByRole("button",{name:"Inspect selected run timeline",exact:true}),heading:panel.getByRole("heading",{name:"Selected run timeline",exact:true})};
  135 | }
  136 | for (const width of [1024,1440]) {
  137 |   test(`scenario timeline: malformed transport contracts and HTTP retry stay unknown at ${width}`,async ({page},info) => {
  138 |     await page.setViewportSize({width,height:900}); await connectStudio(page,info); const made=await prepare(page,width);
  139 |     const {panel,inspect,heading}=await openTimeline(page);
  140 |     const writes:string[]=[];page.on("request",r => {if (!["GET","HEAD","OPTIONS"].includes(r.method())) writes.push(r.method());});
  141 |     let mode="http";
  142 |     await page.route(`**/api/v1/runs/${made.run.runId}/timeline*`,async route => {
  143 |       if (mode === "real") return route.continue();
  144 |       if (mode === "http") return route.fulfill({status:503,json:{code:"LABELLED_TIMELINE_UNAVAILABLE",message:"Labelled transport fixture"}});
  145 |       const value=structuredClone(made.timeline);
  146 |       if (mode === "snapshot") value.snapshotId="foreign-snapshot";
  147 |       if (mode === "version") value.timelineVersion="99.0";
  148 |       if (mode === "authority") value.readOnly=false;
  149 |       if (mode === "clock") value.items.find((r:any) => r.position.status === "aligned").position.clockDomain="unmapped-device-clock";
  150 |       if (mode === "metric") value.items.find((r:any) => r.layer === "evaluation" && r.kind === "metric").verdict="pass";
  151 |       if (mode === "window") value.items.find((r:any) => r.layer === "evaluation").window.endTick="-1";
  152 |       if (mode === "duplicate") {value.items[1]=structuredClone(value.items[0]);}
  153 |       await route.fulfill({json:value});
  154 |     });
  155 |     for (const next of ["http","snapshot","version","authority","clock","metric","window","duplicate"]) {
  156 |       mode=next;await inspect.focus();await page.keyboard.press("Enter");
  157 |       await expect(panel.getByRole("alert")).toContainText("Timeline availability is unknown");
  158 |       await expect(panel.getByRole("alert")).toBeFocused();
  159 |       await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(0);
  160 |     }
  161 |     mode="real";await inspect.focus();await page.keyboard.press("Enter");await expect(heading).toBeFocused();
  162 |     await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(made.timeline.items.length);
  163 |     expect(writes).toEqual([]);expect(await request(page,`/projects/${made.project.projectId}`)).toEqual(made.project);
  164 |   });
  165 |   test(`scenario timeline: labelled exact large ticks, gaps and unsupported clock remain separate at ${width}`,async ({page},info) => {
  166 |     await page.setViewportSize({width,height:900});await connectStudio(page,info);const made=await prepare(page,width);
  167 |     const {panel,inspect,heading}=await openTimeline(page);
  168 |     await page.route(`**/api/v1/runs/${made.run.runId}/timeline*`,async route => {
  169 |       const clock=new URL(route.request().url()).searchParams.get("clockDomain") || "simulation-time";
  170 |       const value=structuredClone(made.timeline), sample=made.timeline.items.find((r:any) => r.kind === "observation.available");
  171 |       value.evidenceScope="fixture";value.intentClockCodec=null;value.clockDomain=clock;value.tickUnit=clock === "simulation-time" ? "microsecond" : null;
  172 |       value.clockDomains=[{id:"simulation-time",declared:true,observed:true},{id:"device-time",declared:false,observed:true}];value.clockDomainsComplete=false;
  173 |       value.items=["9007199254740993","9007199254740995"].map((tick,i) => ({...structuredClone(sample),id:"recorded:labelled-large-"+i,eventId:"labelled-large-"+i,evidenceScope:"fixture",sourceTime:{tick,clockDomain:"simulation-time",resolution:"microsecond",uncertainty:2},position:{tick,clockDomain:"simulation-time",tickUnit:"microsecond",status:clock === "simulation-time" ? "aligned" : "unplaced",reason:clock === "simulation-time" ? null : "CLOCK_NOT_SELECTED"}}));
  174 |       value.items.push({...structuredClone(sample),id:"recorded:labelled-unknown",eventId:"labelled-unknown",evidenceScope:"fixture",sourceTime:{tick:"7",clockDomain:"device-time",resolution:"unknown"},position:{tick:"7",clockDomain:"device-time",tickUnit:null,status:"unplaced",reason:"TICK_ENCODING_UNADMITTED"}});
  175 |       value.nextCursor=null;value.counts={...value.counts,matchedRows:3,returnedRows:3,unplacedRows:clock === "simulation-time" ? 1 : 3,recordedInputs:3,recordedInputsConsidered:3,intentInputs:0,intentInputsConsidered:0,evaluationInputsConsidered:0};
  176 |       value.inputsComplete={recorded:false,intents:true,evaluations:true};value.recorded.collectionStatus="partial";
  177 |       value.recorded.gapCount=1;value.recorded.gapsComplete=true;value.recorded.gaps=[{reason:"Labelled transport fixture gap",detailUnavailable:false,sourceTime:{}}];
  178 |       await route.fulfill({json:value});
  179 |     });
  180 |     await inspect.focus();await page.keyboard.press("Enter");await expect(heading).toBeFocused();
  181 |     await expect(panel).toContainText("9007199254740993");await expect(panel).toContainText("9007199254740995");
  182 |     await expect(panel).toContainText("Labelled transport fixture gap");await expect(panel).toContainText("recorded evidence incomplete");
  183 |     const markers=panel.locator("svg .timeline-marker");await expect(markers).toHaveCount(2);
> 184 |     const xs=await markers.evaluateAll(nodes => nodes.map(n => Number(n.getAttribute("cx"))));expect(xs[0]).toBeLessThan(xs[1]);
      |                                                                                                             ^ Error: expect(received).toBeLessThan(expected)
  185 |     await panel.getByLabel("Timeline clock",{exact:true}).selectOption("device-time");
  186 |     await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(0);
  187 |     await inspect.focus();await page.keyboard.press("Enter");await expect(heading).toBeFocused();
  188 |     await expect(panel.locator("svg .timeline-marker")).toHaveCount(0);
  189 |     await expect(panel).toContainText("TICK_ENCODING_UNADMITTED");
  190 |     expect((await request(page,`/runs/${made.run.runId}`)).journalDigest).toBe(made.run.journalDigest);
  191 |     expect(await request(page,`/projects/${made.project.projectId}`)).toEqual(made.project);
  192 |     await info.attach("fixture-scope",{body:"Labelled transport projection only; original journal and snapshot are unchanged. No device clock support or physical execution claim.",contentType:"text/plain"});
  193 |   });
  194 |   test(`scenario timeline: native canonical pages preserve identities and reject changed evaluation cursors at ${width}`,async ({page},info) => {
  195 |     await page.setViewportSize({width,height:900});await connectStudio(page,info);const made=await prepare(page,width,true);
  196 |     const {panel,inspect,heading}=await openTimeline(page);
  197 |     await inspect.focus();await page.keyboard.press("Enter");await expect(heading).toBeFocused();
  198 |     const expected:string[]=[], seen:string[]=[];
  199 |     let canonical=await request(page,`/runs/${made.run.runId}/timeline?limit=100`);
  200 |     while (true) { expected.push(...canonical.items.map((r:any) => r.id)); if (!canonical.nextCursor) break;canonical=await request(page,`/runs/${made.run.runId}/timeline?limit=100&cursor=${encodeURIComponent(canonical.nextCursor)}`); }
  201 |     expect(expected.length).toBeGreaterThan(200);
  202 |     while (true) {
  203 |       seen.push(...await panel.locator("tr[data-timeline-id]").evaluateAll(nodes => nodes.map(n => n.getAttribute("data-timeline-id")!)));
  204 |       const next=panel.getByRole("button",{name:"Next timeline page",exact:true});if (await next.isDisabled()) break;
  205 |       await next.focus();await page.keyboard.press("Enter");await expect(heading).toBeFocused();
  206 |     }
  207 |     expect(seen).toEqual(expected);expect(new Set(seen).size).toBe(expected.length);
  208 |     await panel.getByRole("button",{name:"Previous timeline page",exact:true}).focus();await page.keyboard.press("Enter");await expect(heading).toBeFocused();
  209 |     await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(100);
  210 |     // A new real immutable evaluation changes the bound cursor identity; it is a deliberate setup mutation.
  211 |     const d=(await request(page,`/runs/${made.run.runId}/definitions`)).items[0];
  212 |     await request(page,`/runs/${made.run.runId}/evaluations`,"POST",{snapshotId:made.run.snapshotId,definitionRef:d.definitionRef,definitionDigest:d.definitionDigest,evidenceRefs:[made.run.runId+":reference-journal"]});
  213 |     await panel.getByRole("button",{name:"Next timeline page",exact:true}).focus();await page.keyboard.press("Enter");
  214 |     await expect(panel.getByRole("alert")).toContainText("TIMELINE_CURSOR_STALE");await expect(panel.getByRole("alert")).toBeFocused();
  215 |     await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(0);
  216 |     await inspect.focus();await page.keyboard.press("Enter");await expect(heading).toBeFocused();
  217 |     expect((await request(page,`/runs/${made.run.runId}`)).journalDigest).toBe(made.run.journalDigest);
  218 |   });
  219 |   for (const destination of ["focus","home"]) {
  220 |     test(`scenario timeline: held actual read preserves ${destination} at ${width}`,async ({page},info) => {
  221 |       await page.setViewportSize({width,height:900});await connectStudio(page,info);const made=await prepare(page,width);
  222 |       const {panel,inspect,heading}=await openTimeline(page);
  223 |       let release!:() => void,ready=false,requests=0;
  224 |       const gate=new Promise<void>(resolve => release=resolve);
  225 |       await page.route(`**/api/v1/runs/${made.run.runId}/timeline*`,async route => {requests++;const response=await route.fetch({timeout:30000});ready=true;await gate;await route.fulfill({response});});
  226 |       try {
  227 |         await inspect.focus();await page.keyboard.press("Enter");await expect.poll(() => ready,{timeout:30000}).toBe(true);
  228 |         await page.keyboard.press("Enter");expect(requests).toBe(1);
  229 |         const target=page.getByRole("button",{name:destination === "home" ? "X-Verse Studio home" : "Edit scenario XDL",exact:true});
  230 |         await target.focus();
  231 |         if (destination === "home") await page.keyboard.press("Enter");
  232 |         release();
  233 |         if (destination === "focus") {await expect(panel.locator("tr[data-timeline-id]")).toHaveCount(made.timeline.items.length);await expect(target).toBeFocused();await expect(heading).not.toBeFocused();}
  234 |         else {await expect(panel).toHaveCount(0);await expect(page.getByRole("heading",{name:"Start with an example",exact:true})).toBeVisible();}
  235 |         expect(requests).toBe(1);expect(await request(page,`/projects/${made.project.projectId}`)).toEqual(made.project);
  236 |       } finally {release();}
  237 |     });
  238 |   }
  239 |   test(`scenario timeline: draft marker opens the typed form and saves canonical intent at ${width}`,async ({page},info) => {
  240 |     await page.setViewportSize({width,height:900});await connectStudio(page,info);const made=await prepare(page,width);
  241 |     const authored=page.getByRole("region",{name:"Authored scenario timeline",exact:true});
  242 |     await expect(authored.getByLabel("Authoring clock",{exact:true})).toHaveValue("simulation-time");
  243 |     await authored.getByRole("button",{name:"Edit timeline step later-start",exact:true}).focus();await page.keyboard.press("Enter");
  244 |     await page.getByLabel("Scheduled at",{exact:true}).fill("0.125");
  245 |     await page.getByRole("button",{name:"Save scenario item",exact:true}).focus();await page.keyboard.press("Enter");
  246 |     await expect(page.getByRole("dialog")).toHaveCount(0);
  247 |     const saved=await request(page,`/projects/${made.project.projectId}`), scenario:any=Object.values(saved.documents).map((d:any) => parse(d.content)).find((r:any) => r.kind === "Scenario");
  248 |     expect(saved.revision).toBe(made.project.revision+1);expect(scenario.spec.steps[0].schedule.at).toBe(0.125);
  249 |     expect((await request(page,`/runs/${made.run.runId}/snapshot`)).snapshot).toEqual(made.snapshot);
  250 |     expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth+1)).toBe(false);
  251 |   });
  252 | }
  253 |
```
