# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: expanded.spec.ts >> frozen input inspection back at 1024
- Location: .studio-local/frozen-input-read-context/expanded.spec.ts:10:6

# Error details

```
Error: apiResponse.json: Response has been disposed
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
          - code [ref=f1e114]: snap-cb3a4da
          - generic [ref=f1e115]: stopped
      - generic [ref=f1e116]:
        - generic [ref=f1e117]:
          - generic [ref=f1e118]:
            - heading "Run results stopped" [level=2] [ref=f1e119]:
              - text: Run results
              - generic [ref=f1e120]: stopped
            - paragraph [ref=f1e121]:
              - code [ref=f1e122]: run-71876cc1-8d34-4d61-a836-534d08cd0c61
              - generic [ref=f1e123]:
                - text: Snapshot
                - code [ref=f1e124]: snap-cb3a4da5-a502
          - generic [ref=f1e125]:
            - generic [ref=f1e126]:
              - text: Recorded run
              - combobox "Recorded run" [active] [ref=f1e127]:
                - option "run-71876cc1-8d34-4d61-a836-534d08cd0c61 · stopped" [selected]
                - option "run-08d0f7c1-b395-46f6-a169-a877ed129e31 · stopped"
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
              - generic [ref=f1e212]: "0.2500"
              - generic [ref=f1e214]: "0.5000"
              - generic [ref=f1e216]: "0.7500"
              - generic [ref=f1e218]: "1.000"
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
              - definition [ref=f1e261]: snap-cb3a4da5-a502-4bce-a0c1-c5e0cad6fe8d
            - generic [ref=f1e262]:
              - term [ref=f1e263]: Plan digest
              - definition [ref=f1e264]: sha256:156f451a517a97b80580e49dcaa072278b8b523e4fffc294c1ea7507aab61467
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
      - generic [ref=f1e276]:
        - generic [ref=f1e277]: Local project · Saved on backend
        - generic [ref=f1e280]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e281]: 1 provider(s) available
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
> 42  |    calls++;const response=await route.fetch();expect(response.status()).toBe(200);returned=await response.json();
      |                                                                                                           ^ Error: apiResponse.json: Response has been disposed
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
  70  |    await selected.focus();await page.keyboard.press('End');
  71  |    await expect(selected).toHaveValue(newer.runId);
  72  |    if(mode==='back') {await selected.focus();await page.keyboard.press('End');await expect(selected).toHaveValue(original.runId);}
  73  |    if(mode==='superseded') {await button.click();await expect(page.getByRole('dialog')).toContainText(newer.snapshotId);}
  74  |   } else if(mode==='Model') await page.getByRole('tab',{name:'Model',exact:true}).click();
  75  |   else if(mode==='Home') await page.getByRole('button',{name:'X-Verse Studio home',exact:true}).click();
  76  |   else if(mode==='tab') await page.getByRole('tab',{name:/^Events & logs/}).click();
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
  92  |     await expect(dialog.getByRole('option',{name:'Complete authored revision · unavailable',exact:true})).toHaveAttribute('disabled','');
  93  |     await dialog.getByLabel('Frozen input set',{exact:true}).focus();await page.keyboard.press('End');await expect(dialog.getByLabel('Frozen input set',{exact:true})).toHaveValue('documents');
  94  |    }
  95  |    const document=await dialog.getByLabel('Frozen document',{exact:true}).inputValue();
  96  |    await expect(dialog.getByLabel('Frozen source text (read-only)',{exact:true})).toHaveValue(JSON.parse(sourceJson).documents[document]);
  97  |    expect(await dialog.getByLabel('Frozen source text (read-only)',{exact:true}).evaluate((node:HTMLTextAreaElement)=>node.readOnly)).toBe(true);
  98  |    if(mode==='normal') {
  99  |     const authored=JSON.parse(sourceJson).projectDocuments;await dialog.getByLabel('Frozen input set',{exact:true}).selectOption('projectDocuments');
  100 |     const name=await dialog.getByLabel('Frozen document',{exact:true}).inputValue();await expect(dialog.getByLabel('Frozen source text (read-only)',{exact:true})).toHaveValue(authored[name]);
  101 |     await page.screenshot({path:info.outputPath('frozen-inputs-'+width+'.png'),fullPage:true});
  102 |    }
  103 |    await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);await expect(button).toBeFocused();
  104 |    expect(calls).toBe(1);
  105 |   } else if(mode==='superseded') {
  106 |    await expect(dialog).toHaveCount(1);await expect(dialog).toContainText(newer.snapshotId);
  107 |    expect((await dialog.textContent())?.includes(original.snapshotId)).toBe(false);
  108 |    await page.keyboard.press('Escape');await expect(button).toBeFocused();
  109 |   } else {
  110 |    await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
  111 |    await expect(dialog).toHaveCount(0);
  112 |    if(mode==='Model') await expect(page.getByRole('tab',{name:'Model',exact:true})).toHaveAttribute('aria-selected','true');
  113 |    if(mode==='Home') await expect(page.getByRole('heading',{name:'Start with an example',exact:true})).toBeVisible();
  114 |    if(mode==='tab') await expect(page.getByRole('tab',{name:/^Events & logs/})).toHaveAttribute('aria-selected','true');
  115 |    if(mode==='focus') await expect(focused).toBeFocused();
  116 |   }
  117 |   const facts={scope:'Two actual native owned runs. DTO/HTTP-negative modes substitute explicitly labelled response fields only; all protected files remain unchanged.',
  118 |    mode,width,originalRunId:original.runId,originalSnapshotId:original.snapshotId,newerRunId:newer.runId,newerSnapshotId:newer.snapshotId,
  119 |    delivery,calls,canonicalBytesUnchanged:names.every(name=>digest(name)===before[name]),workloads};
  120 |   await info.attach('frozen-input-inspection-control',{contentType:'application/json',body:JSON.stringify(facts)});
  121 |   expect(facts.canonicalBytesUnchanged).toBe(true);expect(workloads).toEqual([]);
  122 |
  123 |  });
  124 | }
  125 |
```
