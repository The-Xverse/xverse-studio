# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline.spec.ts >> scenario timeline: native frozen intent, observed faults and evaluation windows at 1024
- Location: tests/e2e/scenario-timeline.spec.ts:52:7

# Error details

```
TimeoutError: locator.focus: Timeout 15000ms exceeded.
Call log:
  - waiting for getByRole('tab', { name: 'Timeline', exact: true })

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
        - tab "Experiments" [active] [selected] [ref=f1e97] [cursor=pointer]
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
          - code [ref=f1e114]: snap-68139c4
          - generic [ref=f1e115]: stopped
          - button "Draft differs from run inputs (1 document, 0 elements, 0 parameters)" [ref=f1e116] [cursor=pointer]
      - generic [ref=f1e117]:
        - generic [ref=f1e118]:
          - generic [ref=f1e119]:
            - heading "Experiments" [level=2] [ref=f1e120]
            - paragraph [ref=f1e121]: Author bounded intent, inspect actual events, and assess immutable evidence.
          - button "Edit scenario XDL" [ref=f1e122] [cursor=pointer]
        - tablist "Experiment sections" [ref=f1e125]:
          - tab "Scenario" [selected] [ref=f1e126] [cursor=pointer]
          - tab "Assertions" [ref=f1e127] [cursor=pointer]
          - tab "Campaigns" [ref=f1e128] [cursor=pointer]
        - region "Scenario authoring" [ref=f1e129]:
          - generic [ref=f1e130]:
            - generic [ref=f1e131]:
              - heading "Author operating scenario intent" [level=3] [ref=f1e132]
              - paragraph [ref=f1e133]: Edits create a validated draft revision. Existing run inputs stay frozen.
            - button "Edit initial conditions" [ref=f1e134] [cursor=pointer]
          - paragraph [ref=f1e135]: Actions, fault activation/recovery and metric acceptance are authored intent. They are not runtime permissions, observed effects or evaluated assertions. Unsupported schedules block preflight.
          - generic [ref=f1e136]:
            - region "Stimulus step authoring" [ref=f1e137]:
              - generic [ref=f1e138]:
                - heading "Stimulus steps 1 / 64" [level=4] [ref=f1e139]:
                  - text: Stimulus steps
                  - generic [ref=f1e140]: 1 / 64
                - button "Add stimulus step" [ref=f1e141] [cursor=pointer]
              - article [ref=f1e142]:
                - code [ref=f1e143]: later-start
                - generic [ref=f1e144]:
                  - button "Edit step later-start" [ref=f1e145] [cursor=pointer]: Edit
                  - button "View source for step later-start" [ref=f1e146] [cursor=pointer]: Source
                  - button "Remove step later-start" [disabled] [ref=f1e147]: Remove
            - region "Fault intent authoring" [ref=f1e148]:
              - generic [ref=f1e149]:
                - heading "Fault intents 0 / 32" [level=4] [ref=f1e150]:
                  - text: Fault intents
                  - generic [ref=f1e151]: 0 / 32
                - button "Add fault intent" [ref=f1e152] [cursor=pointer]
              - paragraph [ref=f1e153]: No fault intent declared.
            - region "Observer authoring" [ref=f1e154]:
              - generic [ref=f1e155]:
                - heading "Observers 1 / 32" [level=4] [ref=f1e156]:
                  - text: Observers
                  - generic [ref=f1e157]: 1 / 32
                - button "Add observer" [ref=f1e158] [cursor=pointer]
              - article [ref=f1e159]:
                - code [ref=f1e160]: state-observer
                - generic [ref=f1e161]:
                  - button "Edit observer state-observer" [ref=f1e162] [cursor=pointer]: Edit
                  - button "View source for observer state-observer" [ref=f1e163] [cursor=pointer]: Source
                  - button "Remove observer state-observer" [disabled] [ref=f1e164]: Remove
            - region "Metric intent authoring" [ref=f1e165]:
              - generic [ref=f1e166]:
                - heading "Metric intents 1 / 64" [level=4] [ref=f1e167]:
                  - text: Metric intents
                  - generic [ref=f1e168]: 1 / 64
                - button "Add metric intent" [ref=f1e169] [cursor=pointer]
              - article [ref=f1e170]:
                - code [ref=f1e171]: final-state
                - generic [ref=f1e172]:
                  - button "Edit metric final-state" [ref=f1e173] [cursor=pointer]: Edit
                  - button "View source for metric final-state" [ref=f1e174] [cursor=pointer]: Source
                  - button "Remove metric final-state" [disabled] [ref=f1e175]: Remove
          - paragraph [ref=f1e176]: Clock and target choices come from this Scenario’s selected resources. The public XDL validator decides reference validity; a provider must separately admit execution.
        - generic [ref=f1e177]:
          - generic [ref=f1e178]:
            - generic [ref=f1e179]: SCENARIO INTENT
            - heading "reference-response" [level=3] [ref=f1e180]
            - paragraph [ref=f1e181]: Studio-owned reference fixture.
            - generic [ref=f1e182]:
              - generic [ref=f1e183]:
                - term [ref=f1e184]: System
                - definition [ref=f1e185]: org.xverse.studio.process-control/reference-loop
              - generic [ref=f1e186]:
                - term [ref=f1e187]: Deployment
                - definition [ref=f1e188]: org.xverse.studio.process-control/local-reference
              - generic [ref=f1e189]:
                - term [ref=f1e190]: Clock domain
                - definition [ref=f1e191]: simulation-time
              - generic [ref=f1e192]:
                - term [ref=f1e193]: Initial conditions
                - definition [ref=f1e194]: "{\"stateParameterRef\":\"initial\"}"
            - paragraph [ref=f1e195]: Exercise the owned reference provider; completion alone is not an assertion pass.
          - generic [ref=f1e196]:
            - heading "Scheduled actions" [level=3] [ref=f1e197]
            - generic [ref=f1e199]:
              - generic [ref=f1e200]: 0 s
              - generic [ref=f1e201]:
                - strong [ref=f1e202]: later-start
                - paragraph [ref=f1e203]: start · org.xverse.studio.process-control/reference-loop/plant
                - generic [ref=f1e204]: Intent
            - paragraph [ref=f1e205]: Requested activation is not proof of an observed effect. Only provider-admitted targets and fault actions may execute.
        - generic [ref=f1e206]:
          - heading "Observers" [level=3] [ref=f1e207]
          - table [ref=f1e209]:
            - rowgroup [ref=f1e210]:
              - row [ref=f1e211]:
                - columnheader "Observer" [ref=f1e212]
                - columnheader "Target" [ref=f1e213]
                - columnheader "Sampling intent" [ref=f1e214]
                - columnheader "Clock / units" [ref=f1e215]
            - rowgroup [ref=f1e216]:
              - row [ref=f1e217]:
                - cell [ref=f1e218]:
                  - strong [ref=f1e219]: state-observer
                - cell "org.xverse.studio.process-control/reference-loop/state-flow" [ref=f1e220]
                - cell "every fixed model step including initial state" [ref=f1e221]
                - cell "simulation-time 1" [ref=f1e222]:
                  - text: simulation-time
                  - generic [ref=f1e223]: "1"
        - generic [ref=f1e224]:
          - heading "Metrics and assessment intent" [level=3] [ref=f1e225]
          - generic [ref=f1e226]:
            - strong [ref=f1e227]: final-state
            - generic [ref=f1e228]: Not evaluated
            - paragraph [ref=f1e229]: Opaque intent only; use an admitted bounded assertion definition to assess evidence.
            - text: urn:xverse:studio:metric:last
          - group [ref=f1e230]:
            - generic "Inspect exact data" [ref=f1e231] [cursor=pointer]
      - generic [ref=f1e232]:
        - generic [ref=f1e233]: Local project · Saved on backend
        - generic [ref=f1e236]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e237]: 1 provider(s) available
```

# Test source

```ts
  1  | import { test, expect, type Page } from "@playwright/test";
  2  | import { parse, stringify } from "yaml";
  3  | import { connectStudio } from "./connect-studio";
  4  | async function request(page: Page, path: string, method = "GET", body?: any, revision?: number) {
  5  |   return page.evaluate(async ({path, method, body, revision}) => {
  6  |     const session = await fetch("/api/v1/session").then(r => r.json());
  7  |     const response = await fetch("/api/v1" + path, {method,
  8  |       headers: {"Content-Type":"application/json", "X-CSRF-Token":session.csrfToken,
  9  |         ...(revision ? {"If-Match":String(revision)} : {}), ...(method === "POST" ? {"Idempotency-Key":crypto.randomUUID()} : {})},
  10 |       ...(body === undefined ? {} : {body:JSON.stringify(body)})});
  11 |     if (!response.ok) throw new Error(path + ": " + response.status + " " + await response.text());
  12 |     return response.json();
  13 |   }, {path, method, body, revision});
  14 | }
  15 | async function prepare(page: Page, width: number) {
  16 |   let project = await request(page,"/projects","POST",{name:"Owned timeline " + width});
  17 |   const [docId, doc]: any = Object.entries(project.documents).find(([,d]:any) => d.path.endsWith("/scenario.xdl.yaml"))!;
  18 |   const scenario = parse(doc.content);
  19 |   const params = scenario.extensions["io.xverse.experiment"].parameters;
  20 |   params.find((p:any) => p.id === "duration").value = 0.2;
  21 |   params.find((p:any) => p.id === "fault").value = "stuck-sensor";
  22 |   const definitions = scenario.extensions["io.xverse.studio.experiments"].definitions;
  23 |   definitions.forEach((d:any) => d.window.endTick = "200000");
  24 |   definitions.push({...structuredClone(definitions[0]), evaluationId:"timeline-peak", name:"Timeline peak", kind:"metric", resultUnit:"1", expression: structuredClone(definitions[0].expression.left)});
  25 |   project = await request(page, `/projects/${project.projectId}/documents/${docId}`, "PUT", {content:stringify(scenario),format:"yaml"},project.revision);
  26 |   const pf = await request(page,`/projects/${project.projectId}/preflights`,"POST",{revision:project.revision});
  27 |   expect(pf.status).toBe("ready");
  28 |   const created = await request(page,"/runs","POST",{snapshotId:pf.snapshotId,preflightId:pf.preflightId});
  29 |   await expect.poll(async () => (await request(page,`/runs/${created.runId}`)).state).toBe("stopped");
  30 |   const run = await request(page,`/runs/${created.runId}`);
  31 |   const snapshot = (await request(page,`/runs/${run.runId}/snapshot`)).snapshot;
  32 |   for (const d of (await request(page,`/runs/${run.runId}/definitions`)).items) {
  33 |     await request(page,`/runs/${run.runId}/evaluations`,"POST",{snapshotId:run.snapshotId,definitionRef:d.definitionRef,definitionDigest:d.definitionDigest,evidenceRefs:[run.runId+":reference-journal"]});
  34 |   }
  35 |   const timeline = await request(page,`/runs/${run.runId}/timeline`);
  36 |   expect(timeline.items.some((r:any) => r.kind === "fault.activation_observed")).toBe(true);
  37 |   scenario.spec.steps[0].id = "later-start";
  38 |   project = await request(page,`/projects/${project.projectId}/documents/${docId}`,"PUT",{content:stringify(scenario),format:"yaml"},project.revision);
  39 |   const runIds = (await request(page,"/runs")).items.map((r:any) => r.runId);
  40 |   await page.evaluate(({project,run,snapshot}) => {
  41 |     localStorage.setItem("studio.projectId",project.projectId);
  42 |     localStorage.setItem("studio.lastRun."+project.projectId,run.runId);
  43 |     localStorage.setItem("studio.lastRun",run.runId);
  44 |     localStorage.setItem("studio.selection."+project.projectId,JSON.stringify({deploymentRef:snapshot.selection.deploymentRef,scenarioRef:snapshot.selection.scenarioRef}));
  45 |   },{project,run,snapshot});
  46 |   await page.reload();
  47 |   await page.getByRole("tab",{name:"Experiments",exact:true}).focus();
  48 |   await page.keyboard.press("Enter");
  49 |   return {project,run,snapshot,timeline,runIds};
  50 | }
  51 | for (const width of [1024,1440]) {
  52 |   test(`scenario timeline: native frozen intent, observed faults and evaluation windows at ${width}`,async ({page},info) => {
  53 |     await page.setViewportSize({width,height:900});
  54 |     await connectStudio(page,info);
  55 |     const made = await prepare(page,width);
  56 |     const writes:string[] = [], errors:string[] = [];
  57 |     page.on("request",r => {if (!["GET","HEAD","OPTIONS"].includes(r.method())) writes.push(r.method()+" "+new URL(r.url()).pathname);});
  58 |     page.on("pageerror",e => errors.push(e.message));
> 59 |     await page.getByRole("tab",{name:"Timeline",exact:true}).focus();
     |                                                              ^ TimeoutError: locator.focus: Timeout 15000ms exceeded.
  60 |     await page.keyboard.press("Enter");
  61 |     const panel = page.getByRole("region",{name:"Selected run timeline",exact:true});
  62 |     await panel.getByRole("button",{name:"Inspect selected run timeline",exact:true}).focus();
  63 |     await page.keyboard.press("Enter");
  64 |     const heading = panel.getByRole("heading",{name:"Selected run timeline",exact:true});
  65 |     await expect(heading).toBeFocused();
  66 |     await expect(panel).toContainText(made.snapshot.snapshotId);
  67 |     await expect(panel).toContainText("Current draft differs from the executed revision");
  68 |     await expect(panel.getByRole("table",{name:"Timeline records",exact:true})).toBeVisible();
  69 |     await expect(panel.locator('[data-timeline-id="intent:steps:start-reference"]')).toBeVisible();
  70 |     await expect(panel.locator('[data-timeline-id="intent:steps:later-start"]')).toHaveCount(0);
  71 |     for (const kind of ["fault.activation_requested","fault.activation_observed"]) {
  72 |       const row = panel.locator("tr[data-timeline-id]").filter({hasText:kind});
  73 |       await expect(row).toHaveCount(1);
  74 |       await expect(row).toContainText("100000");
  75 |       await expect(row).toContainText("owned_reference");
  76 |     }
  77 |     const assertion = panel.locator("tr[data-timeline-id]").filter({hasText:"assertion"});
  78 |     await expect(assertion).toContainText("complete");
  79 |     await expect(assertion).toContainText("pass");
  80 |     await expect(assertion).toContainText("[0, 200000)");
  81 |     const metric = panel.locator("tr[data-timeline-id]").filter({hasText:"evaluation · metric"});
  82 |     await expect(metric).toContainText("No verdict");
  83 |     expect(await request(page,`/projects/${made.project.projectId}`)).toEqual(made.project);
  84 |     expect((await request(page,`/runs/${made.run.runId}/snapshot`)).snapshot).toEqual(made.snapshot);
  85 |     expect((await request(page,`/runs/${made.run.runId}`)).journalDigest).toBe(made.run.journalDigest);
  86 |     expect((await request(page,"/runs")).items.map((r:any) => r.runId)).toEqual(made.runIds);
  87 |     expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth+1)).toBe(false);
  88 |     expect(writes).toEqual([]); expect(errors).toEqual([]);
  89 |     await info.attach("owned-timeline-context",{body:JSON.stringify({runId:made.run.runId,snapshotId:made.snapshot.snapshotId,revision:made.snapshot.revision,projectRevision:made.project.revision,scope:made.timeline.evidenceScope}),contentType:"application/json"});
  90 |     await page.screenshot({path:info.outputPath("scenario-timeline.png"),fullPage:true});
  91 |   });
  92 | }
  93 |
```
