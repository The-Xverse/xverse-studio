# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: probe.spec.ts >> actual frozen-input reply preserves a newer recorded run at 1024
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
            - heading "Frozen inspection context 1024" [level=1] [ref=f1e64]
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
        - tab "Experiments" [ref=f1e97] [cursor=pointer]
        - tab "Results 1" [selected] [ref=f1e100] [cursor=pointer]:
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
          - code [ref=f1e114]: snap-5e5359e
          - generic [ref=f1e115]: stopped
          - button "Draft matches run inputs" [ref=f1e116] [cursor=pointer]
      - generic [ref=f1e117]:
        - generic [ref=f1e118]:
          - generic [ref=f1e119]:
            - heading "Run results stopped" [level=2] [ref=f1e120]:
              - text: Run results
              - generic [ref=f1e121]: stopped
            - paragraph [ref=f1e122]:
              - code [ref=f1e123]: run-5a0c5409-e3f4-4fce-afa9-daba82ca07bf
              - generic [ref=f1e124]:
                - text: Snapshot
                - code [ref=f1e125]: snap-5e5359e7-7b62
          - generic [ref=f1e126]:
            - generic [ref=f1e127]:
              - text: Recorded run
              - combobox "Recorded run" [ref=f1e128]:
                - option "run-5a0c5409-e3f4-4fce-afa9-daba82ca07bf · stopped" [selected]
                - option "run-b3f8404c-3968-4f01-938a-fbf29d915701 · stopped"
            - button "Frozen inputs" [ref=f1e129] [cursor=pointer]
            - button "Rerun frozen inputs" [ref=f1e132] [cursor=pointer]
            - button "Refresh" [ref=f1e135] [cursor=pointer]
        - region "Run controls" [ref=f1e138]:
          - generic [ref=f1e139]:
            - generic [ref=f1e140]:
              - button "Stop" [disabled] [ref=f1e141]
              - generic [ref=f1e144]: Not available while the run is stopped.
            - generic [ref=f1e145]:
              - button "Cancel" [disabled] [ref=f1e146]
              - generic [ref=f1e147]: Not available while the run is stopped.
            - paragraph [ref=f1e148]: "Not admitted for this run: pause, resume, step, reset, set_parameter. The backend rejects them; absence of a button is not support."
        - generic [ref=f1e149]:
          - generic [ref=f1e150]:
            - text: Execution
            - strong [ref=f1e151]: stopped
            - text: Lifecycle outcome
          - generic [ref=f1e153]:
            - text: Assertion verdict
            - strong [ref=f1e154]: Not evaluated
            - text: Separate assessment result
          - generic [ref=f1e156]:
            - text: Cleanup
            - strong [ref=f1e157]: complete
            - text: Owned-resource release
          - generic [ref=f1e159]:
            - text: Evidence
            - strong [ref=f1e160]: complete
            - text: Integrity and completeness
        - generic [ref=f1e162]:
          - generic [ref=f1e163]: owned_reference
          - generic [ref=f1e164]: owned_reference · Source clocks retained · Browser presentation is bounded
          - generic [ref=f1e165]: Retained history available
        - tablist "Result sections" [ref=f1e167]:
          - tab "Observations" [selected] [ref=f1e168] [cursor=pointer]
          - tab "Events & logs 0" [ref=f1e169] [cursor=pointer]:
            - text: Events & logs
            - generic [ref=f1e170]: "0"
          - tab "Diagnosis" [ref=f1e171] [cursor=pointer]
          - tab "Evidence" [ref=f1e172] [cursor=pointer]
          - tab "Compare" [ref=f1e173] [cursor=pointer]
          - tab "Annotations" [ref=f1e174] [cursor=pointer]
        - generic [ref=f1e175]:
          - generic [ref=f1e176]:
            - generic [ref=f1e177]:
              - heading "Recorded observations" [level=3] [ref=f1e178]
              - paragraph [ref=f1e179]: Original source time and quantity semantics are preserved.
            - generic [ref=f1e180]:
              - button "Table view" [ref=f1e181] [cursor=pointer]
              - button "Replay observations" [ref=f1e182] [cursor=pointer]
          - generic [ref=f1e183]:
            - generic [ref=f1e184]:
              - generic [ref=f1e185]:
                - text: Element reference
                - combobox "Element reference" [ref=f1e186]:
                  - option "All elements" [selected]
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#controller"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#plant"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#state-flow"
              - generic [ref=f1e187]:
                - text: Emitter provider
                - combobox "Emitter provider" [ref=f1e188]:
                  - option "All reported identities" [selected]
                  - option "studio.reference"
              - generic [ref=f1e189]:
                - text: Observer
                - combobox "Observer" [ref=f1e190]:
                  - option "All reported identities" [selected]
                  - option "state-observer"
              - generic [ref=f1e191]:
                - text: Observation field
                - combobox "Observation field" [ref=f1e192]:
                  - option "All reported fields" [selected]
                  - option "control"
                  - option "measured"
                  - option "target"
                  - option "value"
              - generic [ref=f1e193]:
                - text: Time basis
                - combobox "Time basis" [ref=f1e194]:
                  - option "No time window" [selected]
                  - option "Original source clock"
                  - option "Recorded receipt UTC"
            - paragraph [ref=f1e195]: The field predicate selects records and the returned value field. Original immutable payloads remain inspectable in Events.
            - generic [ref=f1e196]:
              - button "Apply evidence filters" [ref=f1e197] [cursor=pointer]
              - button "Reset evidence filters" [ref=f1e198] [cursor=pointer]
          - status "Evidence read quality" [ref=f1e199]:
            - generic [ref=f1e200]: "Matched: 2 · Returned: 2 · Omitted from page: 0"
            - generic [ref=f1e201]: "missingSourceTime: 0"
            - generic [ref=f1e202]: "malformedSourceTime: 0"
            - generic [ref=f1e203]: "otherClock: 0"
            - generic [ref=f1e204]: "missingReceiptTime: 0"
            - generic [ref=f1e205]: "unsupportedReceiptEncoding: 0"
            - generic [ref=f1e206]: "Reader integrity: valid"
          - generic [ref=f1e207]:
            - paragraph [ref=f1e208]: "Original clock: simulation-time · tick unit: microsecond. Exact endpoint ticks: 0 to 100000."
            - img "Recorded observation chart in simulation-time. Exact source ticks; missing time is not plotted." [ref=f1e209]:
              - generic [ref=f1e210]: "0.000"
              - generic [ref=f1e212]: "0.3000"
              - generic [ref=f1e214]: "0.6000"
              - generic [ref=f1e216]: "0.9000"
              - generic [ref=f1e218]: "1.200"
              - generic [ref=f1e220]: "0"
              - generic [ref=f1e221]: "100000"
            - generic [ref=f1e237]:
              - generic [ref=f1e238]: control
              - generic [ref=f1e240]: measured
              - generic [ref=f1e242]: target
              - generic [ref=f1e244]: value
          - generic [ref=f1e246]:
            - button "Previous observation page" [disabled] [ref=f1e247]
            - button "Next observation page" [disabled] [ref=f1e248]
          - generic [ref=f1e249]:
            - generic [ref=f1e250]:
              - text: "Clock:"
              - strong [ref=f1e251]: simulation-time
            - generic [ref=f1e252]:
              - text: "Unit:"
              - strong [ref=f1e253]: 1, 1, 1, 1
            - generic [ref=f1e254]:
              - text: "Reduction:"
              - strong [ref=f1e255]: page
        - generic [ref=f1e256]:
          - heading "Input and evidence provenance" [level=3] [ref=f1e257]
          - generic [ref=f1e258]:
            - generic [ref=f1e259]:
              - term [ref=f1e260]: Snapshot
              - definition [ref=f1e261]: snap-5e5359e7-7b62-4494-937e-718d6a57c601
            - generic [ref=f1e262]:
              - term [ref=f1e263]: Plan digest
              - definition [ref=f1e264]: sha256:8b5c7a5658f481a14c64e1336920953a31af5cf34b02a6a0da55195dcef1fc81
            - generic [ref=f1e265]:
              - term [ref=f1e266]: Provider
              - definition [ref=f1e267]: studio.reference
            - generic [ref=f1e268]:
              - term [ref=f1e269]: Clock uncertainty
              - definition [ref=f1e270]: Not declared
            - generic [ref=f1e271]:
              - term [ref=f1e272]: Coverage
              - definition [ref=f1e273]: Unknown
          - group [ref=f1e274]:
            - generic "Inspect exact data" [ref=f1e275] [cursor=pointer]
        - dialog [ref=f1e277]:
          - generic [ref=f1e278]:
            - heading "Frozen run inputs · read-only" [level=2] [ref=f1e279]
            - button "Close dialog" [active] [ref=f1e280] [cursor=pointer]
          - paragraph [ref=f1e283]: These verified source inputs belong to this immutable run snapshot. Current project edits create separate draft revisions.
          - generic [ref=f1e284]:
            - generic [ref=f1e285]: Backend integrity verified
            - generic [ref=f1e286]:
              - generic [ref=f1e287]:
                - term [ref=f1e288]: Snapshot
                - definition [ref=f1e289]: snap-ad8de7e8-637d-4239-854d-f65c92be5cf1
              - generic [ref=f1e290]:
                - term [ref=f1e291]: Project revision
                - definition [ref=f1e292]: "2"
              - generic [ref=f1e293]:
                - term [ref=f1e294]: Snapshot identity
                - definition [ref=f1e295]: sha256:a3ca9cffba1d2374f376b69415c86a3fce5da20200711ad9e7376aee34337bf8
              - generic [ref=f1e296]:
                - term [ref=f1e297]: Plan identity
                - definition [ref=f1e298]: sha256:156f451a517a97b80580e49dcaa072278b8b523e4fffc294c1ea7507aab61467
              - generic [ref=f1e299]:
                - term [ref=f1e300]: Semantic identity
                - definition [ref=f1e301]: sha256:9bb8ac6a3ec47689b9ae8a5d248a902b2c0586edb24a1353a46c962f782115e3
              - generic [ref=f1e302]:
                - term [ref=f1e303]: Selected Deployment
                - definition [ref=f1e304]: xdl://org.xverse.studio.process-control/deployment/local-reference
              - generic [ref=f1e305]:
                - term [ref=f1e306]: Selected Scenario
                - definition [ref=f1e307]: xdl://org.xverse.studio.process-control/scenario/reference-response
          - generic [ref=f1e308]:
            - generic [ref=f1e309]:
              - text: Input set
              - combobox "Frozen input set" [ref=f1e310]:
                - option "Compiled contributing inputs" [selected]
                - option "Complete authored revision"
            - generic [ref=f1e311]:
              - text: Frozen document
              - combobox "Frozen document" [ref=f1e312]:
                - option "xdl/controller.xdl.yaml" [selected]
                - option "xdl/deployment.xdl.yaml"
                - option "xdl/evaluation-profile.xdl.yaml"
                - option "xdl/plant.xdl.yaml"
                - option "xdl/profile.xdl.yaml"
                - option "xdl/scenario.xdl.yaml"
                - option "xdl/system.xdl.yaml"
          - generic [ref=f1e313]: Frozen source text (read-only)
          - textbox "Frozen source text (read-only)" [ref=f1e314]: "apiVersion: xverse.io/xdl/v1alpha1 kind: Component metadata: namespace: org.xverse.studio.process-control name: reference-controller version: 1.0.0 description: Studio-owned reference fixture. provenance: source: urn:xverse:studio:reference revision: 1.0.0 maturity: prototype limitations: - Owned executable reference only; no external simulator, device or scientific fidelity claim. spec: capabilities: - reference-control interfaces: - id: command direction: bidirectional payloadSchema: urn:xverse:studio:normalized-scalar:v1 unitSemantics: '1' compatibility: exact endpoints: - id: command-out ownerId: reference-controller interfaceId: command direction: output parameters: []"
          - group [ref=f1e315]:
            - generic "Inspect exact data" [ref=f1e316] [cursor=pointer]
      - generic [ref=f1e317]:
        - generic [ref=f1e318]: Local project · Saved on backend
        - generic [ref=f1e321]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e322]: 1 provider(s) available
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
