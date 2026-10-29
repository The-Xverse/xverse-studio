# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: expanded.spec.ts >> frozen input inspection missing authored at 1024
- Location: .studio-local/frozen-input-read-context/expanded.spec.ts:10:6

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false
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
          - code [ref=f1e114]: snap-a42f939
          - generic [ref=f1e115]: stopped
          - button "Draft differs from run inputs (1 document, 0 elements, 1 parameter)" [ref=f1e116] [cursor=pointer]
      - generic [ref=f1e117]:
        - generic [ref=f1e118]:
          - generic [ref=f1e119]:
            - heading "Run results stopped" [level=2] [ref=f1e120]:
              - text: Run results
              - generic [ref=f1e121]: stopped
            - paragraph [ref=f1e122]:
              - code [ref=f1e123]: run-c9e38bfb-47b9-45a4-85e8-b23e4aaaf37b
              - generic [ref=f1e124]:
                - text: Snapshot
                - code [ref=f1e125]: snap-a42f939b-74f3
          - generic [ref=f1e126]:
            - generic [ref=f1e127]:
              - text: Recorded run
              - combobox "Recorded run" [ref=f1e128]:
                - option "run-c9e38bfb-47b9-45a4-85e8-b23e4aaaf37b · stopped" [selected]
                - option "run-0254224b-02cc-42bc-8e6e-c53d66b99f68 · stopped"
            - generic [ref=f1e129]:
              - button "Frozen inputs" [ref=f1e130] [cursor=pointer]
              - dialog [ref=f1e134]:
                - generic [ref=f1e135]:
                  - heading "Frozen run inputs · read-only" [level=2] [ref=f1e136]
                  - button "Close dialog" [active] [ref=f1e137] [cursor=pointer]
                - paragraph [ref=f1e140]: These verified source inputs belong to this immutable run snapshot. Current project edits create separate draft revisions.
                - generic [ref=f1e141]:
                  - generic [ref=f1e142]: Backend integrity verified
                  - generic [ref=f1e143]:
                    - generic [ref=f1e144]:
                      - term [ref=f1e145]: Run
                      - definition [ref=f1e146]: run-c9e38bfb-47b9-45a4-85e8-b23e4aaaf37b
                    - generic [ref=f1e147]:
                      - term [ref=f1e148]: Project
                      - definition [ref=f1e149]: prj-a4ed9852-1278-4e9d-8e00-fad82fd121f7
                    - generic [ref=f1e150]:
                      - term [ref=f1e151]: Snapshot
                      - definition [ref=f1e152]: snap-a42f939b-74f3-40d4-a1af-c5d33058654a
                    - generic [ref=f1e153]:
                      - term [ref=f1e154]: Project revision
                      - definition [ref=f1e155]: "2"
                    - generic [ref=f1e156]:
                      - term [ref=f1e157]: Snapshot identity
                      - definition [ref=f1e158]: sha256:1aed30c1b2f983ac9b2a682cc6b71e6878a04952e54b148ad058b352e0749ef5
                    - generic [ref=f1e159]:
                      - term [ref=f1e160]: Plan identity
                      - definition [ref=f1e161]: sha256:156f451a517a97b80580e49dcaa072278b8b523e4fffc294c1ea7507aab61467
                    - generic [ref=f1e162]:
                      - term [ref=f1e163]: Semantic identity
                      - definition [ref=f1e164]: sha256:9bb8ac6a3ec47689b9ae8a5d248a902b2c0586edb24a1353a46c962f782115e3
                    - generic [ref=f1e165]:
                      - term [ref=f1e166]: Selected Deployment
                      - definition [ref=f1e167]: xdl://org.xverse.studio.process-control/deployment/local-reference
                    - generic [ref=f1e168]:
                      - term [ref=f1e169]: Selected Scenario
                      - definition [ref=f1e170]: xdl://org.xverse.studio.process-control/scenario/reference-response
                - generic [ref=f1e171]:
                  - generic [ref=f1e172]:
                    - text: Input set
                    - combobox "Frozen input set" [ref=f1e173]:
                      - option "Compiled contributing inputs" [selected]
                      - option "Complete authored revision · unavailable" [disabled]
                  - generic [ref=f1e174]:
                    - text: Frozen document
                    - combobox "Frozen document" [ref=f1e175]:
                      - option "xdl/controller.xdl.yaml" [selected]
                      - option "xdl/deployment.xdl.yaml"
                      - option "xdl/evaluation-profile.xdl.yaml"
                      - option "xdl/plant.xdl.yaml"
                      - option "xdl/profile.xdl.yaml"
                      - option "xdl/scenario.xdl.yaml"
                      - option "xdl/system.xdl.yaml"
                - paragraph [ref=f1e176]: The complete authored revision was not recorded. Compiled contributing inputs remain available.
                - generic [ref=f1e177]: Frozen source text (read-only)
                - textbox "Frozen source text (read-only)" [ref=f1e178]: "apiVersion: xverse.io/xdl/v1alpha1 kind: Component metadata: namespace: org.xverse.studio.process-control name: reference-controller version: 1.0.0 description: Studio-owned reference fixture. provenance: source: urn:xverse:studio:reference revision: 1.0.0 maturity: prototype limitations: - Owned executable reference only; no external simulator, device or scientific fidelity claim. spec: capabilities: - reference-control interfaces: - id: command direction: bidirectional payloadSchema: urn:xverse:studio:normalized-scalar:v1 unitSemantics: '1' compatibility: exact endpoints: - id: command-out ownerId: reference-controller interfaceId: command direction: output parameters: []"
                - group [ref=f1e179]:
                  - generic "Inspect exact data" [ref=f1e180] [cursor=pointer]
            - button "Rerun frozen inputs" [ref=f1e181] [cursor=pointer]
            - button "Refresh" [ref=f1e184] [cursor=pointer]
        - region "Run controls" [ref=f1e187]:
          - generic [ref=f1e188]:
            - generic [ref=f1e189]:
              - button "Stop" [disabled] [ref=f1e190]
              - generic [ref=f1e193]: Not available while the run is stopped.
            - generic [ref=f1e194]:
              - button "Cancel" [disabled] [ref=f1e195]
              - generic [ref=f1e196]: Not available while the run is stopped.
            - paragraph [ref=f1e197]: "Not admitted for this run: pause, resume, step, reset, set_parameter. The backend rejects them; absence of a button is not support."
        - generic [ref=f1e198]:
          - generic [ref=f1e199]:
            - text: Execution
            - strong [ref=f1e200]: stopped
            - text: Lifecycle outcome
          - generic [ref=f1e202]:
            - text: Assertion verdict
            - strong [ref=f1e203]: Not evaluated
            - text: Separate assessment result
          - generic [ref=f1e205]:
            - text: Cleanup
            - strong [ref=f1e206]: complete
            - text: Owned-resource release
          - generic [ref=f1e208]:
            - text: Evidence
            - strong [ref=f1e209]: complete
            - text: Integrity and completeness
        - generic [ref=f1e211]:
          - generic [ref=f1e212]: owned_reference
          - generic [ref=f1e213]: owned_reference · Source clocks retained · Browser presentation is bounded
          - generic [ref=f1e214]: Retained history available
        - tablist "Result sections" [ref=f1e216]:
          - tab "Observations" [selected] [ref=f1e217] [cursor=pointer]
          - tab "Events & logs 0" [ref=f1e218] [cursor=pointer]:
            - text: Events & logs
            - generic [ref=f1e219]: "0"
          - tab "Diagnosis" [ref=f1e220] [cursor=pointer]
          - tab "Evidence" [ref=f1e221] [cursor=pointer]
          - tab "Compare" [ref=f1e222] [cursor=pointer]
          - tab "Annotations" [ref=f1e223] [cursor=pointer]
        - generic [ref=f1e224]:
          - generic [ref=f1e225]:
            - generic [ref=f1e226]:
              - heading "Recorded observations" [level=3] [ref=f1e227]
              - paragraph [ref=f1e228]: Original source time and quantity semantics are preserved.
            - generic [ref=f1e229]:
              - button "Table view" [ref=f1e230] [cursor=pointer]
              - button "Replay observations" [ref=f1e231] [cursor=pointer]
          - generic [ref=f1e232]:
            - generic [ref=f1e233]:
              - generic [ref=f1e234]:
                - text: Element reference
                - combobox "Element reference" [ref=f1e235]:
                  - option "All elements" [selected]
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#controller"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#plant"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#state-flow"
              - generic [ref=f1e236]:
                - text: Emitter provider
                - combobox "Emitter provider" [ref=f1e237]:
                  - option "All reported identities" [selected]
                  - option "studio.reference"
              - generic [ref=f1e238]:
                - text: Observer
                - combobox "Observer" [ref=f1e239]:
                  - option "All reported identities" [selected]
                  - option "state-observer"
              - generic [ref=f1e240]:
                - text: Observation field
                - combobox "Observation field" [ref=f1e241]:
                  - option "All reported fields" [selected]
                  - option "control"
                  - option "measured"
                  - option "target"
                  - option "value"
              - generic [ref=f1e242]:
                - text: Time basis
                - combobox "Time basis" [ref=f1e243]:
                  - option "No time window" [selected]
                  - option "Original source clock"
                  - option "Recorded receipt UTC"
            - paragraph [ref=f1e244]: The field predicate selects records and the returned value field. Original immutable payloads remain inspectable in Events.
            - generic [ref=f1e245]:
              - button "Apply evidence filters" [ref=f1e246] [cursor=pointer]
              - button "Reset evidence filters" [ref=f1e247] [cursor=pointer]
          - status "Evidence read quality" [ref=f1e248]:
            - generic [ref=f1e249]: "Matched: 2 · Returned: 2 · Omitted from page: 0"
            - generic [ref=f1e250]: "missingSourceTime: 0"
            - generic [ref=f1e251]: "malformedSourceTime: 0"
            - generic [ref=f1e252]: "otherClock: 0"
            - generic [ref=f1e253]: "missingReceiptTime: 0"
            - generic [ref=f1e254]: "unsupportedReceiptEncoding: 0"
            - generic [ref=f1e255]: "Reader integrity: valid"
          - generic [ref=f1e256]:
            - paragraph [ref=f1e257]: "Original clock: simulation-time · tick unit: microsecond. Exact endpoint ticks: 0 to 100000."
            - img "Recorded observation chart in simulation-time. Exact source ticks; missing time is not plotted." [ref=f1e258]:
              - generic [ref=f1e259]: "0.000"
              - generic [ref=f1e261]: "0.2500"
              - generic [ref=f1e263]: "0.5000"
              - generic [ref=f1e265]: "0.7500"
              - generic [ref=f1e267]: "1.000"
              - generic [ref=f1e269]: "0"
              - generic [ref=f1e270]: "100000"
            - generic [ref=f1e286]:
              - generic [ref=f1e287]: control
              - generic [ref=f1e289]: measured
              - generic [ref=f1e291]: target
              - generic [ref=f1e293]: value
          - generic [ref=f1e295]:
            - button "Previous observation page" [disabled] [ref=f1e296]
            - button "Next observation page" [disabled] [ref=f1e297]
          - generic [ref=f1e298]:
            - generic [ref=f1e299]:
              - text: "Clock:"
              - strong [ref=f1e300]: simulation-time
            - generic [ref=f1e301]:
              - text: "Unit:"
              - strong [ref=f1e302]: 1, 1, 1, 1
            - generic [ref=f1e303]:
              - text: "Reduction:"
              - strong [ref=f1e304]: page
        - generic [ref=f1e305]:
          - heading "Input and evidence provenance" [level=3] [ref=f1e306]
          - generic [ref=f1e307]:
            - generic [ref=f1e308]:
              - term [ref=f1e309]: Snapshot
              - definition [ref=f1e310]: snap-a42f939b-74f3-40d4-a1af-c5d33058654a
            - generic [ref=f1e311]:
              - term [ref=f1e312]: Plan digest
              - definition [ref=f1e313]: sha256:156f451a517a97b80580e49dcaa072278b8b523e4fffc294c1ea7507aab61467
            - generic [ref=f1e314]:
              - term [ref=f1e315]: Provider
              - definition [ref=f1e316]: studio.reference
            - generic [ref=f1e317]:
              - term [ref=f1e318]: Clock uncertainty
              - definition [ref=f1e319]: Not declared
            - generic [ref=f1e320]:
              - term [ref=f1e321]: Coverage
              - definition [ref=f1e322]: Unknown
          - group [ref=f1e323]:
            - generic "Inspect exact data" [ref=f1e324] [cursor=pointer]
      - generic [ref=f1e325]:
        - generic [ref=f1e326]: Local project · Saved on backend
        - generic [ref=f1e329]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e330]: 1 provider(s) available
```

# Test source

```ts
  1   | import {test,expect} from '@playwright/test';
  2   | import {readFileSync} from 'node:fs';
  3   | import path from 'node:path';
  4   | import {createHash} from 'node:crypto';
  5   | import {connectStudio} from '../../tests/e2e/connect-studio';
  6   | import {traceApi} from '../../tests/e2e/trace-claims-flow';
  7   |
  8   | for(const mode of ['normal','new run','Model','Home','tab','focus','back','HTTP503','wrong snapshot','wrong plan','malformed documents','unverified','missing authored','superseded','duplicate'])
  9   | for(const width of [1024,1440]) {
  10  |  test(`frozen input inspection ${mode} at ${width}`,async({page},info)=>{
  11  |   await page.setViewportSize({width,height:width===1024?768:900});
  12  |   await connectStudio(page,info);
  13  |   let project=(await traceApi(page,'/projects','POST',{name:'Frozen inspection context '+width})).body;
  14  |   const runs:any[]=[];
  15  |   for(const gain of [0.8,1.2]) {
  16  |    const saved=await traceApi(page,`/projects/${project.projectId}/edits`,'POST',{
  17  |     baseRevision:project.revision,edits:[{kind:'set_parameter',parameterId:'duration',value:0.2},{kind:'set_parameter',parameterId:'gain',value:gain}],
  18  |    },project.revision);
  19  |    expect(saved.status).toBe(200);project=saved.body;
  20  |    const pf=(await traceApi(page,`/projects/${project.projectId}/preflights`,'POST',{revision:project.revision})).body;
  21  |    expect(pf.status).toBe('ready');
  22  |    const started=await traceApi(page,'/runs','POST',{snapshotId:pf.snapshotId,preflightId:pf.preflightId});
  23  |    expect(started.status).toBe(202);
  24  |    await expect.poll(async()=>(await traceApi(page,'/runs/'+started.body.runId)).body.state,{timeout:20000}).toBe('stopped');
  25  |    runs.push((await traceApi(page,'/runs/'+started.body.runId)).body);
  26  |   }
  27  |   const [original,newer]=runs;
  28  |   const digest=(name:string)=>createHash('sha256').update(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!,name))).digest('hex');
  29  |   const names=runs.flatMap(run=>[`runs/${run.runId}/evidence.jsonl`,`snapshots/${run.snapshotId}/snapshot.json`]);
  30  |   const before=Object.fromEntries(names.map(name=>[name,digest(name)]));
  31  |   await page.evaluate(({pid,rid})=>{
  32  |    localStorage.setItem('studio.projectId',pid);localStorage.setItem('studio.lastRun',rid);localStorage.setItem('studio.lastRun.'+pid,rid);
  33  |   },{pid:project.projectId,rid:original.runId});
  34  |   await page.reload();await page.getByRole('tab',{name:'Results',exact:false}).click();
  35  |   const selected=page.getByLabel('Recorded run',{exact:true});await expect(selected).toHaveValue(original.runId);
  36  |   let release!:()=>void,ready!:()=>void,complete!:()=>void;
  37  |   const held=new Promise<void>(r=>release=r),actual=new Promise<void>(r=>ready=r),delivered=new Promise<void>(r=>complete=r);
  38  |   let returned:any,delivery='pending',calls=0;
  39  |   let observed=await traceApi(page,`/runs/${newer.runId}/snapshot`);expect(observed.status).toBe(200);const other=observed.body;
  40  |   const sourceJson=JSON.stringify((await traceApi(page,`/runs/${original.runId}/snapshot`)).body.snapshot);
  41  |   await page.route(`**/api/v1/runs/${original.runId}/snapshot`,async route=>{
  42  |    calls++;const response=await route.fetch();expect(response.status()).toBe(200);returned=await response.json();
  43  |    expect(returned.integrity).toBe('valid');expect(returned.readOnly).toBe(true);expect(returned.snapshot.snapshotId).toBe(original.snapshotId);
  44  |    ready();await held;
  45  |    try{
  46  |     if(mode==='HTTP503') await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({code:'LABELLED_INSPECTION_UNAVAILABLE',message:'Labelled frozen-input read unavailable.'})});
  47  |     else if(['wrong snapshot','wrong plan','malformed documents','unverified','missing authored'].includes(mode)) {
  48  |      const body=structuredClone(returned);
  49  |      if(mode==='wrong snapshot') body.snapshot=other.snapshot;
  50  |      if(mode==='wrong plan') body.snapshot.planDigest=other.snapshot.planDigest;
  51  |      if(mode==='malformed documents') body.snapshot.documents=['labelled-not-a-source-map'];
  52  |      if(mode==='unverified') body.integrity='unknown';
  53  |      if(mode==='missing authored') delete body.snapshot.projectDocuments;
  54  |      await route.fulfill({response,json:body});
  55  |     } else await route.fulfill({response});
  56  |     delivery='fulfilled';
  57  |    }
  58  |    catch(error){if(!route.request().failure())throw error;delivery='browser aborted';}
  59  |    finally{complete();}
  60  |   });
  61  |   const workloads:string[]=[];
  62  |   page.on('request',request=>{
  63  |    const url=new URL(request.url());
  64  |    if(request.method()==='POST' && (/\/api\/v1\/(runs|campaigns)$/.test(url.pathname)||/\/(reruns|commands|evaluations)$/.test(url.pathname))) workloads.push(url.pathname);
  65  |   });
  66  |   const button=page.getByRole('button',{name:'Frozen inputs',exact:true});await button.focus();await page.keyboard.press('Enter');await actual;
  67  |   await expect(button).toBeDisabled();
  68  |   let focused=page.getByRole('button',{name:'Refresh',exact:true});
  69  |   if(mode==='new run'||mode==='back'||mode==='superseded') {
  70  |    await selected.focus();await page.keyboard.press('End');await page.keyboard.press('Enter');
  71  |    await expect(selected).toHaveValue(newer.runId);
  72  |    if(mode==='back') {await selected.focus();await page.keyboard.press('Home');await page.keyboard.press('Enter');await expect(selected).toHaveValue(original.runId);}
  73  |    if(mode==='superseded') {await button.click();await expect(page.getByRole('dialog')).toContainText(newer.snapshotId);}
  74  |   } else if(mode==='Model') await page.getByRole('tab',{name:'Model',exact:true}).click();
  75  |   else if(mode==='Home') await page.getByRole('button',{name:'X-Verse Studio home',exact:true}).click();
  76  |   else if(mode==='tab') await page.getByRole('tab',{name:'Events & logs',exact:true}).click();
  77  |   else if(mode==='focus') await focused.focus();
  78  |   else if(mode==='duplicate') {await button.evaluate(element=>element.dispatchEvent(new MouseEvent('click',{bubbles:true})));}
  79  |   release();await delivered;
  80  |   await expect(page.getByText('Verifying immutable run inputs…',{exact:true})).toHaveCount(0);
  81  |   const dialog=page.getByRole('dialog');
  82  |   if(['HTTP503','wrong snapshot','wrong plan','malformed documents','unverified'].includes(mode)) {
  83  |    await expect(page.getByRole('alert').filter({hasText:/selected run|Labelled frozen/})).toBeVisible();
  84  |    await expect(dialog).toHaveCount(0);await expect(selected).toHaveValue(original.runId);
  85  |    await page.unroute(`**/api/v1/runs/${original.runId}/snapshot`);await button.click();
  86  |    await expect(dialog).toContainText(original.snapshotId);
  87  |   } else if(mode==='normal'||mode==='duplicate'||mode==='missing authored') {
  88  |    await expect(dialog).toContainText(original.snapshotId);await expect(dialog).toContainText(original.runId);
  89  |    await expect(dialog).toContainText(project.projectId);
  90  |    if(mode==='missing authored') {
  91  |     await expect(dialog.getByText('The complete authored revision was not recorded. Compiled contributing inputs remain available.',{exact:true})).toBeVisible();
> 92  |     expect(await dialog.getByRole('option',{name:'Complete authored revision · unavailable',exact:true}).isDisabled()).toBe(true);
      |                                                                                                                        ^ Error: expect(received).toBe(expected) // Object.is equality
  93  |    }
  94  |    const document=await dialog.getByLabel('Frozen document',{exact:true}).inputValue();
  95  |    await expect(dialog.getByLabel('Frozen source text (read-only)',{exact:true})).toHaveValue(JSON.parse(sourceJson).documents[document]);
  96  |    expect(await dialog.getByLabel('Frozen source text (read-only)',{exact:true}).evaluate((node:HTMLTextAreaElement)=>node.readOnly)).toBe(true);
  97  |    if(mode==='normal') {
  98  |     const authored=JSON.parse(sourceJson).projectDocuments;await dialog.getByLabel('Frozen input set',{exact:true}).selectOption('projectDocuments');
  99  |     const name=await dialog.getByLabel('Frozen document',{exact:true}).inputValue();await expect(dialog.getByLabel('Frozen source text (read-only)',{exact:true})).toHaveValue(authored[name]);
  100 |     await page.screenshot({path:info.outputPath('frozen-inputs-'+width+'.png'),fullPage:true});
  101 |    }
  102 |    await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);await expect(button).toBeFocused();
  103 |    expect(calls).toBe(1);
  104 |   } else if(mode==='superseded') {
  105 |    await expect(dialog).toHaveCount(1);await expect(dialog).toContainText(newer.snapshotId);
  106 |    expect((await dialog.textContent())?.includes(original.snapshotId)).toBe(false);
  107 |    await page.keyboard.press('Escape');await expect(button).toBeFocused();
  108 |   } else {
  109 |    await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
  110 |    await expect(dialog).toHaveCount(0);
  111 |    if(mode==='Model') await expect(page.getByRole('tab',{name:'Model',exact:true})).toHaveAttribute('aria-selected','true');
  112 |    if(mode==='Home') await expect(page.getByRole('heading',{name:'Start with an example',exact:true})).toBeVisible();
  113 |    if(mode==='tab') await expect(page.getByRole('tab',{name:'Events & logs',exact:true})).toHaveAttribute('aria-selected','true');
  114 |    if(mode==='focus') await expect(focused).toBeFocused();
  115 |   }
  116 |   const facts={scope:'Two actual native owned runs. DTO/HTTP-negative modes substitute explicitly labelled response fields only; all protected files remain unchanged.',
  117 |    mode,width,originalRunId:original.runId,originalSnapshotId:original.snapshotId,newerRunId:newer.runId,newerSnapshotId:newer.snapshotId,
  118 |    delivery,calls,canonicalBytesUnchanged:names.every(name=>digest(name)===before[name]),workloads};
  119 |   await info.attach('frozen-input-inspection-control',{contentType:'application/json',body:JSON.stringify(facts)});
  120 |   expect(facts.canonicalBytesUnchanged).toBe(true);expect(workloads).toEqual([]);
  121 |
  122 |  });
  123 | }
  124 |
```
