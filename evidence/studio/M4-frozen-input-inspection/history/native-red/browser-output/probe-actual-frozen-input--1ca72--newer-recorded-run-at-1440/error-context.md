# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: probe.spec.ts >> actual frozen-input reply preserves a newer recorded run at 1440
- Location: .studio-local/frozen-input-read-context/probe.spec.ts:9:6

# Error details

```
Error: expect(locator).toHaveCount(expected) failed

Locator:  getByRole('dialog')
Expected: 0
Received: 1
Timeout:  10000ms

Call log:
  - Expect "toHaveCount" getByRole('dialog') with timeout 10000ms
  - waiting for getByRole('dialog')
    24 × locator resolved to 1 element
       - unexpected value "1"

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
            - heading "Frozen inspection context 1440" [level=1] [ref=f1e65]
            - generic [ref=f1e66]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e67]: Process control terms
            - generic [ref=f1e70]: rev 3
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
          - code [ref=f1e113]: "3"
        - generic [ref=f1e114]: 3 elements · 2 connections
        - generic [ref=f1e115]:
          - text: Run snapshot
          - code [ref=f1e116]: snap-8aa5840
          - generic [ref=f1e117]: stopped
          - button "Draft matches run inputs" [ref=f1e118] [cursor=pointer]
      - generic [ref=f1e119]:
        - generic [ref=f1e120]:
          - generic [ref=f1e121]:
            - heading "Run results stopped" [level=2] [ref=f1e122]:
              - text: Run results
              - generic [ref=f1e123]: stopped
            - paragraph [ref=f1e124]:
              - code [ref=f1e125]: run-c7f66a65-25c2-4394-a777-2c7078394789
              - generic [ref=f1e126]:
                - text: Snapshot
                - code [ref=f1e127]: snap-8aa5840b-3331
          - generic [ref=f1e128]:
            - generic [ref=f1e129]:
              - text: Recorded run
              - combobox "Recorded run" [ref=f1e130]:
                - option "run-c7f66a65-25c2-4394-a777-2c7078394789 · stopped" [selected]
                - option "run-d469ebb3-bf99-4c58-b764-0651a389c8ac · stopped"
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
          - tab "Observations" [selected] [ref=f1e170] [cursor=pointer]
          - tab "Events & logs 0" [ref=f1e171] [cursor=pointer]:
            - text: Events & logs
            - generic [ref=f1e172]: "0"
          - tab "Diagnosis" [ref=f1e173] [cursor=pointer]
          - tab "Evidence" [ref=f1e174] [cursor=pointer]
          - tab "Compare" [ref=f1e175] [cursor=pointer]
          - tab "Annotations" [ref=f1e176] [cursor=pointer]
        - generic [ref=f1e177]:
          - generic [ref=f1e178]:
            - generic [ref=f1e179]:
              - heading "Recorded observations" [level=3] [ref=f1e180]
              - paragraph [ref=f1e181]: Original source time and quantity semantics are preserved.
            - generic [ref=f1e182]:
              - button "Table view" [ref=f1e183] [cursor=pointer]
              - button "Replay observations" [ref=f1e184] [cursor=pointer]
          - generic [ref=f1e185]:
            - generic [ref=f1e186]:
              - generic [ref=f1e187]:
                - text: Element reference
                - combobox "Element reference" [ref=f1e188]:
                  - option "All elements" [selected]
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#controller"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#plant"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#state-flow"
              - generic [ref=f1e189]:
                - text: Emitter provider
                - combobox "Emitter provider" [ref=f1e190]:
                  - option "All reported identities" [selected]
                  - option "studio.reference"
              - generic [ref=f1e191]:
                - text: Observer
                - combobox "Observer" [ref=f1e192]:
                  - option "All reported identities" [selected]
                  - option "state-observer"
              - generic [ref=f1e193]:
                - text: Observation field
                - combobox "Observation field" [ref=f1e194]:
                  - option "All reported fields" [selected]
                  - option "control"
                  - option "measured"
                  - option "target"
                  - option "value"
              - generic [ref=f1e195]:
                - text: Time basis
                - combobox "Time basis" [ref=f1e196]:
                  - option "No time window" [selected]
                  - option "Original source clock"
                  - option "Recorded receipt UTC"
            - paragraph [ref=f1e197]: The field predicate selects records and the returned value field. Original immutable payloads remain inspectable in Events.
            - generic [ref=f1e198]:
              - button "Apply evidence filters" [ref=f1e199] [cursor=pointer]
              - button "Reset evidence filters" [ref=f1e200] [cursor=pointer]
          - status "Evidence read quality" [ref=f1e201]:
            - generic [ref=f1e202]: "Matched: 2 · Returned: 2 · Omitted from page: 0"
            - generic [ref=f1e203]: "missingSourceTime: 0"
            - generic [ref=f1e204]: "malformedSourceTime: 0"
            - generic [ref=f1e205]: "otherClock: 0"
            - generic [ref=f1e206]: "missingReceiptTime: 0"
            - generic [ref=f1e207]: "unsupportedReceiptEncoding: 0"
            - generic [ref=f1e208]: "Reader integrity: valid"
          - generic [ref=f1e209]:
            - paragraph [ref=f1e210]: "Original clock: simulation-time · tick unit: microsecond. Exact endpoint ticks: 0 to 100000."
            - img "Recorded observation chart in simulation-time. Exact source ticks; missing time is not plotted." [ref=f1e211]:
              - generic [ref=f1e212]: "0.000"
              - generic [ref=f1e214]: "0.3000"
              - generic [ref=f1e216]: "0.6000"
              - generic [ref=f1e218]: "0.9000"
              - generic [ref=f1e220]: "1.200"
              - generic [ref=f1e222]: "0"
              - generic [ref=f1e223]: "100000"
            - generic [ref=f1e239]:
              - generic [ref=f1e240]: control
              - generic [ref=f1e242]: measured
              - generic [ref=f1e244]: target
              - generic [ref=f1e246]: value
          - generic [ref=f1e248]:
            - button "Previous observation page" [disabled] [ref=f1e249]
            - button "Next observation page" [disabled] [ref=f1e250]
          - generic [ref=f1e251]:
            - generic [ref=f1e252]:
              - text: "Clock:"
              - strong [ref=f1e253]: simulation-time
            - generic [ref=f1e254]:
              - text: "Unit:"
              - strong [ref=f1e255]: 1, 1, 1, 1
            - generic [ref=f1e256]:
              - text: "Reduction:"
              - strong [ref=f1e257]: page
        - generic [ref=f1e258]:
          - heading "Input and evidence provenance" [level=3] [ref=f1e259]
          - generic [ref=f1e260]:
            - generic [ref=f1e261]:
              - term [ref=f1e262]: Snapshot
              - definition [ref=f1e263]: snap-8aa5840b-3331-4437-8986-e303cd3c6844
            - generic [ref=f1e264]:
              - term [ref=f1e265]: Plan digest
              - definition [ref=f1e266]: sha256:8b5c7a5658f481a14c64e1336920953a31af5cf34b02a6a0da55195dcef1fc81
            - generic [ref=f1e267]:
              - term [ref=f1e268]: Provider
              - definition [ref=f1e269]: studio.reference
            - generic [ref=f1e270]:
              - term [ref=f1e271]: Clock uncertainty
              - definition [ref=f1e272]: Not declared
            - generic [ref=f1e273]:
              - term [ref=f1e274]: Coverage
              - definition [ref=f1e275]: Unknown
          - group [ref=f1e276]:
            - generic "Inspect exact data" [ref=f1e277] [cursor=pointer]
        - dialog [ref=f1e279]:
          - generic [ref=f1e280]:
            - heading "Frozen run inputs · read-only" [level=2] [ref=f1e281]
            - button "Close dialog" [active] [ref=f1e282] [cursor=pointer]
          - paragraph [ref=f1e285]: These verified source inputs belong to this immutable run snapshot. Current project edits create separate draft revisions.
          - generic [ref=f1e286]:
            - generic [ref=f1e287]: Backend integrity verified
            - generic [ref=f1e288]:
              - generic [ref=f1e289]:
                - term [ref=f1e290]: Snapshot
                - definition [ref=f1e291]: snap-d4fb2923-08ce-4fbb-a694-b75f861ad9da
              - generic [ref=f1e292]:
                - term [ref=f1e293]: Project revision
                - definition [ref=f1e294]: "2"
              - generic [ref=f1e295]:
                - term [ref=f1e296]: Snapshot identity
                - definition [ref=f1e297]: sha256:6dd4dd1390012e1c9fecd3ff128153fc844e84c9cc575c6fc5ba5b36f0354878
              - generic [ref=f1e298]:
                - term [ref=f1e299]: Plan identity
                - definition [ref=f1e300]: sha256:156f451a517a97b80580e49dcaa072278b8b523e4fffc294c1ea7507aab61467
              - generic [ref=f1e301]:
                - term [ref=f1e302]: Semantic identity
                - definition [ref=f1e303]: sha256:9bb8ac6a3ec47689b9ae8a5d248a902b2c0586edb24a1353a46c962f782115e3
              - generic [ref=f1e304]:
                - term [ref=f1e305]: Selected Deployment
                - definition [ref=f1e306]: xdl://org.xverse.studio.process-control/deployment/local-reference
              - generic [ref=f1e307]:
                - term [ref=f1e308]: Selected Scenario
                - definition [ref=f1e309]: xdl://org.xverse.studio.process-control/scenario/reference-response
          - generic [ref=f1e310]:
            - generic [ref=f1e311]:
              - text: Input set
              - combobox "Frozen input set" [ref=f1e312]:
                - option "Compiled contributing inputs" [selected]
                - option "Complete authored revision"
            - generic [ref=f1e313]:
              - text: Frozen document
              - combobox "Frozen document" [ref=f1e314]:
                - option "xdl/controller.xdl.yaml" [selected]
                - option "xdl/deployment.xdl.yaml"
                - option "xdl/evaluation-profile.xdl.yaml"
                - option "xdl/plant.xdl.yaml"
                - option "xdl/profile.xdl.yaml"
                - option "xdl/scenario.xdl.yaml"
                - option "xdl/system.xdl.yaml"
          - generic [ref=f1e315]: Frozen source text (read-only)
          - textbox "Frozen source text (read-only)" [ref=f1e316]: "apiVersion: xverse.io/xdl/v1alpha1 kind: Component metadata: namespace: org.xverse.studio.process-control name: reference-controller version: 1.0.0 description: Studio-owned reference fixture. provenance: source: urn:xverse:studio:reference revision: 1.0.0 maturity: prototype limitations: - Owned executable reference only; no external simulator, device or scientific fidelity claim. spec: capabilities: - reference-control interfaces: - id: command direction: bidirectional payloadSchema: urn:xverse:studio:normalized-scalar:v1 unitSemantics: '1' compatibility: exact endpoints: - id: command-out ownerId: reference-controller interfaceId: command direction: output parameters: []"
          - group [ref=f1e317]:
            - generic "Inspect exact data" [ref=f1e318] [cursor=pointer]
      - generic [ref=f1e319]:
        - generic [ref=f1e320]: Local project · Saved on backend
        - generic [ref=f1e323]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e324]: 1 provider(s) available
```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test';
  2  | import {readFileSync} from 'node:fs';
  3  | import path from 'node:path';
  4  | import {createHash} from 'node:crypto';
  5  | import {connectStudio} from '../../tests/e2e/connect-studio';
  6  | import {traceApi} from '../../tests/e2e/trace-claims-flow';
  7  |
  8  | for(const width of [1024,1440]) {
  9  |  test(`actual frozen-input reply preserves a newer recorded run at ${width}`,async({page},info)=>{
  10 |   await page.setViewportSize({width,height:width===1024?768:900});
  11 |   await connectStudio(page,info);
  12 |   let project=(await traceApi(page,'/projects','POST',{name:'Frozen inspection context '+width})).body;
  13 |   const runs:any[]=[];
  14 |   for(const gain of [0.8,1.2]) {
  15 |    const saved=await traceApi(page,`/projects/${project.projectId}/edits`,'POST',{
  16 |     baseRevision:project.revision,edits:[{kind:'set_parameter',parameterId:'duration',value:0.2},{kind:'set_parameter',parameterId:'gain',value:gain}],
  17 |    },project.revision);
  18 |    expect(saved.status).toBe(200);project=saved.body;
  19 |    const pf=(await traceApi(page,`/projects/${project.projectId}/preflights`,'POST',{revision:project.revision})).body;
  20 |    expect(pf.status).toBe('ready');
  21 |    const started=await traceApi(page,'/runs','POST',{snapshotId:pf.snapshotId,preflightId:pf.preflightId});
  22 |    expect(started.status).toBe(202);
  23 |    await expect.poll(async()=>(await traceApi(page,'/runs/'+started.body.runId)).body.state,{timeout:20000}).toBe('stopped');
  24 |    runs.push((await traceApi(page,'/runs/'+started.body.runId)).body);
  25 |   }
  26 |   const [original,newer]=runs;
  27 |   const digest=(name:string)=>createHash('sha256').update(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!,name))).digest('hex');
  28 |   const names=runs.flatMap(run=>[`runs/${run.runId}/evidence.jsonl`,`snapshots/${run.snapshotId}/snapshot.json`]);
  29 |   const before=Object.fromEntries(names.map(name=>[name,digest(name)]));
  30 |   await page.evaluate(({pid,rid})=>{
  31 |    localStorage.setItem('studio.projectId',pid);localStorage.setItem('studio.lastRun',rid);localStorage.setItem('studio.lastRun.'+pid,rid);
  32 |   },{pid:project.projectId,rid:original.runId});
  33 |   await page.reload();await page.getByRole('tab',{name:'Results',exact:false}).click();
  34 |   const selected=page.getByLabel('Recorded run',{exact:true});await expect(selected).toHaveValue(original.runId);
  35 |   let release!:()=>void,ready!:()=>void,complete!:()=>void;
  36 |   const held=new Promise<void>(r=>release=r),actual=new Promise<void>(r=>ready=r),delivered=new Promise<void>(r=>complete=r);
  37 |   let returned:any,delivery='pending';
  38 |   await page.route(`**/api/v1/runs/${original.runId}/snapshot`,async route=>{
  39 |    const response=await route.fetch();expect(response.status()).toBe(200);returned=await response.json();
  40 |    expect(returned.integrity).toBe('valid');expect(returned.readOnly).toBe(true);expect(returned.snapshot.snapshotId).toBe(original.snapshotId);
  41 |    ready();await held;
  42 |    try{await route.fulfill({response});delivery='fulfilled';}
  43 |    catch(error){if(!route.request().failure())throw error;delivery='browser aborted';}
  44 |    finally{complete();}
  45 |   });
  46 |   const workloads:string[]=[];
  47 |   page.on('request',request=>{
  48 |    const url=new URL(request.url());
  49 |    if(request.method()==='POST' && (/\/api\/v1\/(runs|campaigns)$/.test(url.pathname)||/\/(reruns|commands|evaluations)$/.test(url.pathname))) workloads.push(url.pathname);
  50 |   });
  51 |   const button=page.getByRole('button',{name:'Frozen inputs',exact:true});await button.focus();await page.keyboard.press('Enter');await actual;
  52 |   await selected.selectOption(newer.runId);await expect(selected).toHaveValue(newer.runId);
  53 |   release();await delivered;
  54 |   await expect(page.getByText('Verifying immutable run inputs…',{exact:true})).toHaveCount(0);
  55 |   await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
  56 |   const dialog=page.getByRole('dialog'),count=await dialog.count();
  57 |   const facts={scope:'Two actual native owned runs; only delivery of the original managed HTTP200 snapshot reply was held.',width,
  58 |    originalRunId:original.runId,originalSnapshotId:original.snapshotId,newerRunId:newer.runId,newerSnapshotId:newer.snapshotId,
  59 |    currentRunId:await selected.inputValue(),returnedSnapshotId:returned.snapshot.snapshotId,delivery,dialogCount:count,
  60 |    dialogContainsOriginalSnapshot:count?((await dialog.textContent())||'').includes(original.snapshotId):false,
  61 |    canonicalBytesUnchanged:names.every(name=>digest(name)===before[name]),workloads};
  62 |   await info.attach('frozen-input-context-control',{contentType:'application/json',body:JSON.stringify(facts)});
  63 |   expect(facts.canonicalBytesUnchanged).toBe(true);expect(workloads).toEqual([]);expect(facts.currentRunId).toBe(newer.runId);
> 64 |   await expect(dialog).toHaveCount(0);
     |                        ^ Error: expect(locator).toHaveCount(expected) failed
  65 |  });
  66 | }
  67 |
```
