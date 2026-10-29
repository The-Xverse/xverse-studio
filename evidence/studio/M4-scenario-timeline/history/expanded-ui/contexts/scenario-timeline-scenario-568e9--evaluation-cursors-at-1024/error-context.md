# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline.spec.ts >> scenario timeline: native canonical pages preserve identities and reject changed evaluation cursors at 1024
- Location: tests/e2e/scenario-timeline.spec.ts:194:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: "ready"
Received: "blocked"
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "Skip to workspace" [ref=e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=e5]:
    - button "X-Verse Studio home" [ref=e6] [cursor=pointer]:
      - generic [ref=e7]: X
      - generic [ref=e8]: X-VERSE STUDIO
    - generic [ref=e10]: Local workspace
    - button "Environment" [ref=e12] [cursor=pointer]
    - generic "Local operator" [ref=e19]: LO
  - generic [ref=e20]:
    - navigation "Main navigation" [ref=e21]:
      - button "Workspace" [ref=e22] [cursor=pointer]
      - button "Catalog" [ref=e29] [cursor=pointer]
      - button "Laboratory" [ref=e36] [cursor=pointer]:
        - generic [ref=e40]: Lab
      - button "Compatibility and environment" [ref=e41] [cursor=pointer]:
        - generic [ref=e47]: Settings
      - generic [ref=e48]: v0.1
    - main [ref=e49]:
      - generic [ref=e50]:
        - generic [ref=e51]:
          - generic [ref=e52]:
            - generic [ref=e53]: LOCAL WORKSPACE
            - heading "Build understanding. One System at a time." [level=1] [ref=e54]: Build understanding.One System at a time.
            - paragraph [ref=e55]: Model, connect, and explore cyber-physical systems. Keep every experiment connected to its evidence.
          - generic [ref=e56]:
            - button "New project" [ref=e57] [cursor=pointer]
            - button "Import project" [ref=e60] [cursor=pointer]
            - button "Import evidence" [ref=e63] [cursor=pointer]
            - button "Import evidence archive" [ref=e66]
            - button "Import project archive" [ref=e67]
        - generic [ref=e68]:
          - generic [ref=e69]:
            - generic [ref=e70]:
              - heading "Start with an example" [level=2] [ref=e71]
              - paragraph [ref=e72]: A guided path from a model to a recorded result.
            - generic [ref=e73]: OWNED REFERENCE PROVIDER
          - generic [ref=e74]:
            - 'button "fixture Process control reference Explore a normalized process response, tune the setpoint and compare measured reference observations. Guided example owned_reference Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated." [ref=e75] [cursor=pointer]':
              - generic [ref=e76]: fixture
              - generic [ref=e92]:
                - heading "Process control reference" [level=3] [ref=e93]
                - paragraph [ref=e96]: Explore a normalized process response, tune the setpoint and compare measured reference observations.
                - generic [ref=e97]:
                  - generic [ref=e98]: Guided example
                  - generic [ref=e99]: owned_reference
                - paragraph [ref=e100]: "Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."
            - 'button "fixture Automotive reference Explore a normalized controller and plant response using the same reference model; no vehicle dynamics claim. Guided example owned_reference Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated." [ref=e101] [cursor=pointer]':
              - generic [ref=e102]: fixture
              - generic [ref=e118]:
                - heading "Automotive reference" [level=3] [ref=e119]
                - paragraph [ref=e122]: Explore a normalized controller and plant response using the same reference model; no vehicle dynamics claim.
                - generic [ref=e123]:
                  - generic [ref=e124]: Guided example
                  - generic [ref=e125]: owned_reference
                - paragraph [ref=e126]: "Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."
            - 'button "fixture Process control feedback reference Declare the reference loop''s unit-delay feedback explicitly and observe the state through an explicit linear converter to percent. Guided example owned_reference Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated." [ref=e127] [cursor=pointer]':
              - generic [ref=e128]: fixture
              - generic [ref=e144]:
                - heading "Process control feedback reference" [level=3] [ref=e145]
                - paragraph [ref=e148]: Declare the reference loop's unit-delay feedback explicitly and observe the state through an explicit linear converter to percent.
                - generic [ref=e149]:
                  - generic [ref=e150]: Guided example
                  - generic [ref=e151]: owned_reference
                - paragraph [ref=e152]: "Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."
          - paragraph [ref=e153]: Reference runs verify Studio workflows. Their results do not establish external simulator or physical-device integration.
        - generic [ref=e157]:
          - generic [ref=e158]:
            - generic [ref=e159]:
              - heading "Recent projects" [level=2] [ref=e160]
              - paragraph [ref=e161]: Continue from your last saved draft.
            - generic [ref=e162]: 7 projects
          - generic [ref=e163]:
            - generic [ref=e164]:
              - button "Owned timeline 1024 System workspace · rev 3 Local" [ref=e165] [cursor=pointer]:
                - generic [ref=e172]:
                  - strong [ref=e173]: Owned timeline 1024
                  - generic [ref=e174]: System workspace · rev 3
                - generic [ref=e175]: Local
              - button "Review retention for project Owned timeline 1024" [ref=e178] [cursor=pointer]: Retention
            - generic [ref=e179]:
              - button "Owned timeline 1024 System workspace · rev 3 Local" [ref=e180] [cursor=pointer]:
                - generic [ref=e187]:
                  - strong [ref=e188]: Owned timeline 1024
                  - generic [ref=e189]: System workspace · rev 3
                - generic [ref=e190]: Local
              - button "Review retention for project Owned timeline 1024" [ref=e193] [cursor=pointer]: Retention
            - generic [ref=e194]:
              - button "Owned timeline 1440 System workspace · rev 4 Local" [ref=e195] [cursor=pointer]:
                - generic [ref=e202]:
                  - strong [ref=e203]: Owned timeline 1440
                  - generic [ref=e204]: System workspace · rev 4
                - generic [ref=e205]: Local
              - button "Review retention for project Owned timeline 1440" [ref=e208] [cursor=pointer]: Retention
            - generic [ref=e209]:
              - button "Owned timeline 1024 System workspace · rev 4 Local" [ref=e210] [cursor=pointer]:
                - generic [ref=e217]:
                  - strong [ref=e218]: Owned timeline 1024
                  - generic [ref=e219]: System workspace · rev 4
                - generic [ref=e220]: Local
              - button "Review retention for project Owned timeline 1024" [ref=e223] [cursor=pointer]: Retention
            - generic [ref=e224]:
              - button "Owned timeline 1440 System workspace · rev 3 Local" [ref=e225] [cursor=pointer]:
                - generic [ref=e232]:
                  - strong [ref=e233]: Owned timeline 1440
                  - generic [ref=e234]: System workspace · rev 3
                - generic [ref=e235]: Local
              - button "Review retention for project Owned timeline 1440" [ref=e238] [cursor=pointer]: Retention
            - generic [ref=e239]:
              - button "Owned timeline 1024 System workspace · rev 3 Local" [ref=e240] [cursor=pointer]:
                - generic [ref=e247]:
                  - strong [ref=e248]: Owned timeline 1024
                  - generic [ref=e249]: System workspace · rev 3
                - generic [ref=e250]: Local
              - button "Review retention for project Owned timeline 1024" [ref=e253] [cursor=pointer]: Retention
            - generic [ref=e254]:
              - button "Scenario intent authoring System workspace · rev 9 Local" [ref=e255] [cursor=pointer]:
                - generic [ref=e262]:
                  - strong [ref=e263]: Scenario intent authoring
                  - generic [ref=e264]: System workspace · rev 9
                - generic [ref=e265]: Local
              - button "Review retention for project Scenario intent authoring" [ref=e268] [cursor=pointer]: Retention
```

# Test source

```ts
  1   | import { test, expect, type Page } from "@playwright/test";
  2   | import { parse, stringify } from "yaml";
  3   | import { connectStudio } from "./connect-studio";
  4   | async function request(page: Page, path: string, method = "GET", body?: any, revision?: number) {
  5   |   return page.evaluate(async ({path, method, body, revision}) => {
  6   |     const session = await fetch("/api/v1/session").then(r => r.json());
  7   |     const response = await fetch("/api/v1" + path, {method,
  8   |       headers: {"Content-Type":"application/json", "X-CSRF-Token":session.csrfToken,
  9   |         ...(revision ? {"If-Match":String(revision)} : {}), ...(method === "POST" ? {"Idempotency-Key":crypto.randomUUID()} : {})},
  10  |       ...(body === undefined ? {} : {body:JSON.stringify(body)})});
  11  |     if (!response.ok) throw new Error(path + ": " + response.status + " " + await response.text());
  12  |     return response.json();
  13  |   }, {path, method, body, revision});
  14  | }
  15  | async function prepare(page: Page, width: number, dense = false) {
  16  |   let project = await request(page,"/projects","POST",{name:"Owned timeline " + width});
  17  |   const [docId, doc]: any = Object.entries(project.documents).find(([,d]:any) => d.path.endsWith("/scenario.xdl.yaml"))!;
  18  |   const scenario = parse(doc.content);
  19  |   const params = scenario.extensions["io.xverse.experiment"].parameters;
  20  |   params.find((p:any) => p.id === "duration").value = 0.2;
  21  |   if (dense) params.find((p:any) => p.id === "timestep").value = 0.001;
  22  |   params.find((p:any) => p.id === "fault").value = "stuck-sensor";
  23  |   const definitions = scenario.extensions["io.xverse.studio.experiments"].definitions;
  24  |   definitions.forEach((d:any) => d.window.endTick = "200000");
  25  |   definitions.push({...structuredClone(definitions[0]), evaluationId:"timeline-peak", name:"Timeline peak", kind:"metric", resultUnit:"1", expression: structuredClone(definitions[0].expression.left)});
  26  |   project = await request(page, `/projects/${project.projectId}/documents/${docId}`, "PUT", {content:stringify(scenario),format:"yaml"},project.revision);
  27  |   const pf = await request(page,`/projects/${project.projectId}/preflights`,"POST",{revision:project.revision});
> 28  |   expect(pf.status).toBe("ready");
      |                     ^ Error: expect(received).toBe(expected) // Object.is equality
  29  |   const created = await request(page,"/runs","POST",{snapshotId:pf.snapshotId,preflightId:pf.preflightId});
  30  |   await expect.poll(async () => (await request(page,`/runs/${created.runId}`)).state).toBe("stopped");
  31  |   const run = await request(page,`/runs/${created.runId}`);
  32  |   const snapshot = (await request(page,`/runs/${run.runId}/snapshot`)).snapshot;
  33  |   for (const d of (await request(page,`/runs/${run.runId}/definitions`)).items) {
  34  |     await request(page,`/runs/${run.runId}/evaluations`,"POST",{snapshotId:run.snapshotId,definitionRef:d.definitionRef,definitionDigest:d.definitionDigest,evidenceRefs:[run.runId+":reference-journal"]});
  35  |   }
  36  |   const timeline = await request(page,`/runs/${run.runId}/timeline`);
  37  |   expect(timeline.items.some((r:any) => r.kind === "fault.activation_observed")).toBe(true);
  38  |   scenario.spec.steps[0].id = "later-start";
  39  |   project = await request(page,`/projects/${project.projectId}/documents/${docId}`,"PUT",{content:stringify(scenario),format:"yaml"},project.revision);
  40  |   const runIds = (await request(page,"/runs")).items.map((r:any) => r.runId);
  41  |   await page.evaluate(({project,run,snapshot}) => {
  42  |     localStorage.setItem("studio.projectId",project.projectId);
  43  |     localStorage.setItem("studio.lastRun."+project.projectId,run.runId);
  44  |     localStorage.setItem("studio.lastRun",run.runId);
  45  |     localStorage.setItem("studio.selection."+project.projectId,JSON.stringify({deploymentRef:snapshot.selection.deploymentRef,scenarioRef:snapshot.selection.scenarioRef}));
  46  |   },{project,run,snapshot});
  47  |   await page.reload();
  48  |   await page.getByRole("tab",{name:"Experiments",exact:true}).focus();
  49  |   await page.keyboard.press("Enter");
  50  |   return {project,run,snapshot,timeline,runIds};
  51  | }
  52  | for (const width of [1024,1440]) {
  53  |   test(`scenario timeline: native frozen intent, observed faults and evaluation windows at ${width}`,async ({page},info) => {
  54  |     await page.setViewportSize({width,height:900});
  55  |     await connectStudio(page,info);
  56  |     const made = await prepare(page,width);
  57  |     const writes:string[] = [], errors:string[] = [];
  58  |     page.on("request",r => {if (!["GET","HEAD","OPTIONS"].includes(r.method())) writes.push(r.method()+" "+new URL(r.url()).pathname);});
  59  |     page.on("pageerror",e => errors.push(e.message));
  60  |     await page.getByRole("tab",{name:"Timeline",exact:true}).focus();
  61  |     await page.keyboard.press("Enter");
  62  |     const panel = page.getByRole("region",{name:"Selected run timeline",exact:true});
  63  |     await panel.getByRole("button",{name:"Inspect selected run timeline",exact:true}).focus();
  64  |     await page.keyboard.press("Enter");
  65  |     const heading = panel.getByRole("heading",{name:"Selected run timeline",exact:true});
  66  |     await expect(heading).toBeFocused();
  67  |     await expect(panel).toContainText(made.snapshot.snapshotId);
  68  |     await expect(panel).toContainText("Current draft differs from the executed revision");
  69  |     await expect(panel.getByRole("table",{name:"Timeline records",exact:true})).toBeVisible();
  70  |     await expect(panel.locator('[data-timeline-id="intent:steps:start-reference"]')).toBeVisible();
  71  |     await expect(panel.locator('[data-timeline-id="intent:steps:later-start"]')).toHaveCount(0);
  72  |     for (const kind of ["fault.activation_requested","fault.activation_observed"]) {
  73  |       const row = panel.locator("tr[data-timeline-id]").filter({hasText:kind});
  74  |       await expect(row).toHaveCount(1);
  75  |       await expect(row).toContainText("100000");
  76  |       await expect(row).toContainText("owned_reference");
  77  |     }
  78  |     const assertion = panel.locator("tr[data-timeline-id]").filter({hasText:"assertion"});
  79  |     await expect(assertion).toContainText("complete");
  80  |     await expect(assertion).toContainText("pass");
  81  |     await expect(assertion).toContainText("[0, 200000)");
  82  |     const metric = panel.locator("tr[data-timeline-id]").filter({hasText:"evaluation · metric"});
  83  |     await expect(metric).toContainText("No verdict");
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
```
