# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline.spec.ts >> scenario authoring completion: held conditions acknowledgement preserves a reopened draft at 1024
- Location: tests/e2e/scenario-timeline.spec.ts:95:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByLabel('Scenario acceptance intent', { exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByLabel('Scenario acceptance intent', { exact: true }) with timeout 10000ms
  - waiting for getByLabel('Scenario acceptance intent', { exact: true })

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
  - text: Draft saved. Existing run snapshots remain unchanged.
  - button "Dismiss notice"
  - button "Workspace"
  - text: System
  - heading "Owned timeline 1024" [level=1]
  - text: Draft Process control terms Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched.
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
    - tab "Experiments" [selected]
    - tab "Results 1"
    - button "XDL source"
  - text: Draft revision
  - code: "4"
  - text: 3 elements · 2 connections Run snapshot
  - code: snap-18ac768
  - text: stopped
  - button "Draft differs from run inputs (1 document, 0 elements, 0 parameters)"
  - heading "Experiments" [level=2]
  - paragraph: Author bounded intent, inspect actual events, and assess immutable evidence.
  - button "Edit scenario XDL"
  - tablist "Experiment sections":
    - tab "Scenario" [selected]
    - tab "Timeline"
    - tab "Assertions"
    - tab "Campaigns"
  - region "Scenario authoring":
    - heading "Author operating scenario intent" [level=3]
    - paragraph: Edits create a validated draft revision. Existing run inputs stay frozen.
    - button "Edit initial conditions"
    - paragraph: Actions, fault activation/recovery and metric acceptance are authored intent. They are not runtime permissions, observed effects or evaluated assertions. Unsupported schedules block preflight.
    - region "Stimulus step authoring":
      - heading "Stimulus steps 1 / 64" [level=4]
      - button "Add stimulus step"
      - article:
        - code: later-start
        - button "Edit step later-start": Edit
        - button "View source for step later-start": Source
        - button "Remove step later-start" [disabled]: Remove
    - region "Fault intent authoring":
      - heading "Fault intents 0 / 32" [level=4]
      - button "Add fault intent"
      - paragraph: No fault intent declared.
    - region "Observer authoring":
      - heading "Observers 1 / 32" [level=4]
      - button "Add observer"
      - article:
        - code: state-observer
        - button "Edit observer state-observer": Edit
        - button "View source for observer state-observer": Source
        - button "Remove observer state-observer" [disabled]: Remove
    - region "Metric intent authoring":
      - heading "Metric intents 1 / 64" [level=4]
      - button "Add metric intent"
      - article:
        - code: final-state
        - button "Edit metric final-state": Edit
        - button "View source for metric final-state": Source
        - button "Remove metric final-state" [disabled]: Remove
    - paragraph: Clock and target choices come from this Scenario’s selected resources. The public XDL validator decides reference validity; a provider must separately admit execution.
  - text: SCENARIO INTENT
  - heading "reference-response" [level=3]
  - paragraph: Studio-owned reference fixture.
  - term: System
  - definition: org.xverse.studio.process-control/reference-loop
  - term: Deployment
  - definition: org.xverse.studio.process-control/local-reference
  - term: Declared clocks
  - definition: simulation-time
  - term: Initial conditions
  - definition: "{\"stateParameterRef\":\"initial\"}"
  - paragraph: First committed conditions
  - heading "Scheduled actions" [level=3]
  - text: 0 s
  - strong: later-start
  - paragraph: start · org.xverse.studio.process-control/reference-loop/plant
  - text: Intent
  - paragraph: Requested activation is not proof of an observed effect. Only provider-admitted targets and fault actions may execute.
  - heading "Observers" [level=3]
  - table:
    - rowgroup:
      - row "Observer Target Sampling intent Clock / units":
        - columnheader "Observer"
        - columnheader "Target"
        - columnheader "Sampling intent"
        - columnheader "Clock / units"
    - rowgroup:
      - row "state-observer org.xverse.studio.process-control/reference-loop/state-flow every fixed model step including initial state simulation-time 1":
        - cell "state-observer":
          - strong: state-observer
        - cell "org.xverse.studio.process-control/reference-loop/state-flow"
        - cell "every fixed model step including initial state"
        - cell "simulation-time 1"
  - heading "Metrics and assessment intent" [level=3]
  - strong: final-state
  - text: Not evaluated
  - paragraph: Opaque intent only; use an admitted bounded assertion definition to assess evidence.
  - text: urn:xverse:studio:metric:last
  - group: Inspect exact data
  - text: Local project · Saved on backend Authoritative XDL · Layout stored separately 1 provider(s) available
```

# Test source

```ts
  22  |   const definitions = scenario.extensions["io.xverse.studio.experiments"].definitions;
  23  |   definitions.forEach((d:any) => d.window.endTick = "200000");
  24  |   definitions.push({...structuredClone(definitions[0]), evaluationId:"timeline-peak", name:"Timeline peak", kind:"metric", resultUnit:"1", expression: structuredClone(definitions[0].expression.left)});
  25  |   project = await request(page, `/projects/${project.projectId}/documents/${docId}`, "PUT", {content:stringify(scenario),format:"yaml"},project.revision);
  26  |   const pf = await request(page,`/projects/${project.projectId}/preflights`,"POST",{revision:project.revision});
  27  |   expect(pf.status).toBe("ready");
  28  |   const created = await request(page,"/runs","POST",{snapshotId:pf.snapshotId,preflightId:pf.preflightId});
  29  |   await expect.poll(async () => (await request(page,`/runs/${created.runId}`)).state).toBe("stopped");
  30  |   const run = await request(page,`/runs/${created.runId}`);
  31  |   const snapshot = (await request(page,`/runs/${run.runId}/snapshot`)).snapshot;
  32  |   for (const d of (await request(page,`/runs/${run.runId}/definitions`)).items) {
  33  |     await request(page,`/runs/${run.runId}/evaluations`,"POST",{snapshotId:run.snapshotId,definitionRef:d.definitionRef,definitionDigest:d.definitionDigest,evidenceRefs:[run.runId+":reference-journal"]});
  34  |   }
  35  |   const timeline = await request(page,`/runs/${run.runId}/timeline`);
  36  |   expect(timeline.items.some((r:any) => r.kind === "fault.activation_observed")).toBe(true);
  37  |   scenario.spec.steps[0].id = "later-start";
  38  |   project = await request(page,`/projects/${project.projectId}/documents/${docId}`,"PUT",{content:stringify(scenario),format:"yaml"},project.revision);
  39  |   const runIds = (await request(page,"/runs")).items.map((r:any) => r.runId);
  40  |   await page.evaluate(({project,run,snapshot}) => {
  41  |     localStorage.setItem("studio.projectId",project.projectId);
  42  |     localStorage.setItem("studio.lastRun."+project.projectId,run.runId);
  43  |     localStorage.setItem("studio.lastRun",run.runId);
  44  |     localStorage.setItem("studio.selection."+project.projectId,JSON.stringify({deploymentRef:snapshot.selection.deploymentRef,scenarioRef:snapshot.selection.scenarioRef}));
  45  |   },{project,run,snapshot});
  46  |   await page.reload();
  47  |   await page.getByRole("tab",{name:"Experiments",exact:true}).focus();
  48  |   await page.keyboard.press("Enter");
  49  |   return {project,run,snapshot,timeline,runIds};
  50  | }
  51  | for (const width of [1024,1440]) {
  52  |   test(`scenario timeline: native frozen intent, observed faults and evaluation windows at ${width}`,async ({page},info) => {
  53  |     await page.setViewportSize({width,height:900});
  54  |     await connectStudio(page,info);
  55  |     const made = await prepare(page,width);
  56  |     const writes:string[] = [], errors:string[] = [];
  57  |     page.on("request",r => {if (!["GET","HEAD","OPTIONS"].includes(r.method())) writes.push(r.method()+" "+new URL(r.url()).pathname);});
  58  |     page.on("pageerror",e => errors.push(e.message));
  59  |     await page.getByRole("tab",{name:"Timeline",exact:true}).focus();
  60  |     await page.keyboard.press("Enter");
  61  |     const panel = page.getByRole("region",{name:"Selected run timeline",exact:true});
  62  |     await panel.getByRole("button",{name:"Inspect selected run timeline",exact:true}).focus();
  63  |     await page.keyboard.press("Enter");
  64  |     const heading = panel.getByRole("heading",{name:"Selected run timeline",exact:true});
  65  |     await expect(heading).toBeFocused();
  66  |     await expect(panel).toContainText(made.snapshot.snapshotId);
  67  |     await expect(panel).toContainText("Current draft differs from the executed revision");
  68  |     await expect(panel.getByRole("table",{name:"Timeline records",exact:true})).toBeVisible();
  69  |     await expect(panel.locator('[data-timeline-id="intent:steps:start-reference"]')).toBeVisible();
  70  |     await expect(panel.locator('[data-timeline-id="intent:steps:later-start"]')).toHaveCount(0);
  71  |     for (const kind of ["fault.activation_requested","fault.activation_observed"]) {
  72  |       const row = panel.locator("tr[data-timeline-id]").filter({hasText:kind});
  73  |       await expect(row).toHaveCount(1);
  74  |       await expect(row).toContainText("100000");
  75  |       await expect(row).toContainText("owned_reference");
  76  |     }
  77  |     const assertion = panel.locator("tr[data-timeline-id]").filter({hasText:"assertion"});
  78  |     await expect(assertion).toContainText("complete");
  79  |     await expect(assertion).toContainText("pass");
  80  |     await expect(assertion).toContainText("[0, 200000)");
  81  |     const metric = panel.locator("tr[data-timeline-id]").filter({hasText:"evaluation · metric"});
  82  |     await expect(metric).toContainText("No verdict");
  83  |     expect(await request(page,`/projects/${made.project.projectId}`)).toEqual(made.project);
  84  |     expect((await request(page,`/runs/${made.run.runId}/snapshot`)).snapshot).toEqual(made.snapshot);
  85  |     expect((await request(page,`/runs/${made.run.runId}`)).journalDigest).toBe(made.run.journalDigest);
  86  |     expect((await request(page,"/runs")).items.map((r:any) => r.runId)).toEqual(made.runIds);
  87  |     expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth+1)).toBe(false);
  88  |     expect(writes).toEqual([]); expect(errors).toEqual([]);
  89  |     await info.attach("owned-timeline-context",{body:JSON.stringify({runId:made.run.runId,snapshotId:made.snapshot.snapshotId,revision:made.snapshot.revision,projectRevision:made.project.revision,scope:made.timeline.evidenceScope}),contentType:"application/json"});
  90  |     await page.screenshot({path:info.outputPath("scenario-timeline.png"),fullPage:true});
  91  |   });
  92  | }
  93  |
  94  | for (const width of [1024,1440]) {
  95  |   test(`scenario authoring completion: held conditions acknowledgement preserves a reopened draft at ${width}`,async ({page},info) => {
  96  |     await page.setViewportSize({width,height:900}); await connectStudio(page,info);
  97  |     const made=await prepare(page,width);
  98  |     const open=page.getByRole("button",{name:"Edit initial conditions",exact:true});
  99  |     await open.focus(); await page.keyboard.press("Enter");
  100 |     await page.getByLabel("Scenario acceptance intent",{exact:true}).fill("First committed conditions");
  101 |     let release!: () => void;
  102 |     const released=new Promise<void>(resolve => release=resolve);
  103 |     let ready=false, committed:any=null, writes=0;
  104 |     await page.route(`**/api/v1/projects/${made.project.projectId}/edits`,async route => {
  105 |       if (route.request().method() !== "POST") return route.continue();
  106 |       writes++;
  107 |       const response=await route.fetch({timeout:30000}); committed=await response.json(); ready=true;
  108 |       await released; await route.fulfill({response});
  109 |     });
  110 |     try {
  111 |       await page.getByRole("button",{name:"Save scenario conditions",exact:true}).focus(); await page.keyboard.press("Enter");
  112 |       await expect.poll(() => ready,{timeout:30000}).toBe(true);
  113 |       await page.keyboard.press("Enter"); expect(writes).toBe(1);
  114 |       await page.keyboard.press("Escape");
  115 |       await open.focus(); await page.keyboard.press("Enter");
  116 |       const draft=page.getByLabel("Scenario acceptance intent",{exact:true});
  117 |       await draft.fill("Keep this newer unsaved draft"); await draft.focus();
  118 |       release();
  119 |       await expect.poll(async () => (await request(page,`/projects/${made.project.projectId}`)).revision).toBe(committed.revision);
  120 |       // Observe completion from the actual page transport, then preserve the newer form/focus.
  121 |       await expect(page.locator(".project-header")).toContainText(String(committed.revision));
> 122 |       await expect(draft).toBeVisible(); await expect(draft).toHaveValue("Keep this newer unsaved draft"); await expect(draft).toBeFocused();
      |                           ^ Error: expect(locator).toBeVisible() failed
  123 |       expect(writes).toBe(1);
  124 |       expect((await request(page,`/runs/${made.run.runId}/snapshot`)).snapshot).toEqual(made.snapshot);
  125 |       await page.keyboard.press("Escape");
  126 |     } finally {release();}
  127 |   });
  128 | }
  129 |
```
