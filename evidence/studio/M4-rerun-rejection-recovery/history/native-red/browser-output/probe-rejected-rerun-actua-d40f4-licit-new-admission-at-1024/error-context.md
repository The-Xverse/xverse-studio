# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: probe.spec.ts >> rejected rerun: actual capacity release permits explicit new admission at 1024
- Location: .studio-local/rejected-rerun-context/probe.spec.ts:8:37

# Error details

```
Error: Explicit rerun after verified rejection and real capacity release should receive fresh admission.

expect(received).toBe(expected) // Object.is equality

Expected: "completed"
Received: "rejected"
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
      - alert "Operation error" [ref=f1e51]:
        - generic [ref=f1e55]:
          - strong [ref=f1e56]: Operation unavailable
          - paragraph [ref=f1e57]: "RESOURCE_BUSY: Current read-only admission facts no longer allow this execution. Recheck the independent readiness dimensions. Retrying retains the same operation identity."
        - button "Dismiss error" [ref=f1e58] [cursor=pointer]
      - generic [ref=f1e61]:
        - generic [ref=f1e62]:
          - generic [ref=f1e63]:
            - button "Workspace" [ref=f1e64] [cursor=pointer]
            - generic [ref=f1e67]: System
          - generic [ref=f1e68]:
            - heading "Native rejected rerun recovery 1024" [level=1] [ref=f1e75]
            - generic [ref=f1e76]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e77]: Process control terms
        - generic [ref=f1e80]:
          - 'button "Dependencies: none unresolved" [ref=f1e81] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f1e82]
          - button "Redo" [disabled] [ref=f1e83]
          - button "Export" [ref=f1e84] [cursor=pointer]
          - button "Validate" [ref=f1e87] [cursor=pointer]
          - button "Preflight & run" [ref=f1e90] [cursor=pointer]
      - tablist "System workflows" [ref=f1e93]:
        - tab "Model" [ref=f1e94] [cursor=pointer]
        - tab "Connections" [ref=f1e100] [cursor=pointer]
        - tab "Deployment" [ref=f1e105] [cursor=pointer]
        - tab "Experiments" [ref=f1e108] [cursor=pointer]
        - tab "Results 1" [selected] [ref=f1e111] [cursor=pointer]:
          - text: Results
          - generic [ref=f1e114]: "1"
        - button "XDL source" [ref=f1e116] [cursor=pointer]
      - generic [ref=f1e119]:
        - generic [ref=f1e120]:
          - text: Draft revision
          - code [ref=f1e122]: "2"
        - generic [ref=f1e123]: 3 elements · 2 connections
        - generic [ref=f1e124]:
          - text: Run snapshot
          - code [ref=f1e125]: snap-22bfbd9
          - generic [ref=f1e126]: stopped
          - button "Draft matches run inputs" [ref=f1e127] [cursor=pointer]
      - generic [ref=f1e128]:
        - generic [ref=f1e129]:
          - generic [ref=f1e130]:
            - heading "Run results stopped" [level=2] [ref=f1e131]:
              - text: Run results
              - generic [ref=f1e132]: stopped
            - paragraph [ref=f1e133]:
              - code [ref=f1e134]: run-ba529c95-8dc0-4413-b4ef-043677a9d27f
              - generic [ref=f1e135]:
                - text: Snapshot
                - code [ref=f1e136]: snap-22bfbd94-905a
          - generic [ref=f1e137]:
            - generic [ref=f1e138]:
              - text: Recorded run
              - combobox "Recorded run" [ref=f1e139]:
                - option "run-ba529c95-8dc0-4413-b4ef-043677a9d27f · stopped" [selected]
            - button "Frozen inputs" [ref=f1e141] [cursor=pointer]
            - button "Rerun frozen inputs" [ref=f1e144] [cursor=pointer]
            - button "Refresh" [ref=f1e147] [cursor=pointer]
        - region "Run controls" [ref=f1e150]:
          - generic [ref=f1e151]:
            - generic [ref=f1e152]:
              - button "Stop" [disabled] [ref=f1e153]
              - generic [ref=f1e156]: Not available while the run is stopped.
            - generic [ref=f1e157]:
              - button "Cancel" [disabled] [ref=f1e158]
              - generic [ref=f1e159]: Not available while the run is stopped.
            - paragraph [ref=f1e160]: "Not admitted for this run: pause, resume, step, reset, set_parameter. The backend rejects them; absence of a button is not support."
        - generic [ref=f1e161]:
          - generic [ref=f1e162]:
            - heading "Fresh execution request" [level=3] [ref=f1e163]
            - generic [ref=f1e164]: rejected
          - paragraph [ref=f1e165]: A rerun creates a new run and snapshot after current admission checks. Recorded observation playback remains read-only.
          - group [ref=f1e166]:
            - generic "Inspect exact data" [ref=f1e167] [cursor=pointer]
        - generic [ref=f1e168]:
          - generic [ref=f1e169]:
            - text: Execution
            - strong [ref=f1e170]: stopped
            - text: Lifecycle outcome
          - generic [ref=f1e172]:
            - text: Assertion verdict
            - strong [ref=f1e173]: Not evaluated
            - text: Separate assessment result
          - generic [ref=f1e175]:
            - text: Cleanup
            - strong [ref=f1e176]: complete
            - text: Owned-resource release
          - generic [ref=f1e178]:
            - text: Evidence
            - strong [ref=f1e179]: complete
            - text: Integrity and completeness
        - generic [ref=f1e181]:
          - generic [ref=f1e182]: owned_reference
          - generic [ref=f1e183]: owned_reference · Source clocks retained · Browser presentation is bounded
          - generic [ref=f1e184]: Retained history available
        - tablist "Result sections" [ref=f1e186]:
          - tab "Observations" [selected] [ref=f1e187] [cursor=pointer]
          - tab "Events & logs 0" [ref=f1e188] [cursor=pointer]:
            - text: Events & logs
            - generic [ref=f1e189]: "0"
          - tab "Diagnosis" [ref=f1e190] [cursor=pointer]
          - tab "Evidence" [ref=f1e191] [cursor=pointer]
          - tab "Compare" [ref=f1e192] [cursor=pointer]
          - tab "Annotations" [ref=f1e193] [cursor=pointer]
        - generic [ref=f1e194]:
          - generic [ref=f1e195]:
            - generic [ref=f1e196]:
              - heading "Recorded observations" [level=3] [ref=f1e197]
              - paragraph [ref=f1e198]: Original source time and quantity semantics are preserved.
            - generic [ref=f1e199]:
              - button "Table view" [ref=f1e200] [cursor=pointer]
              - button "Replay observations" [ref=f1e201] [cursor=pointer]
          - generic [ref=f1e202]:
            - generic [ref=f1e203]:
              - generic [ref=f1e204]:
                - text: Element reference
                - combobox "Element reference" [ref=f1e205]:
                  - option "All elements" [selected]
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#controller"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#plant"
                  - option "xdl://org.xverse.studio.process-control/system/reference-loop#state-flow"
              - generic [ref=f1e206]:
                - text: Emitter provider
                - combobox "Emitter provider" [ref=f1e207]:
                  - option "All reported identities" [selected]
                  - option "studio.reference"
              - generic [ref=f1e208]:
                - text: Observer
                - combobox "Observer" [ref=f1e209]:
                  - option "All reported identities" [selected]
                  - option "state-observer"
              - generic [ref=f1e210]:
                - text: Observation field
                - combobox "Observation field" [ref=f1e211]:
                  - option "All reported fields" [selected]
                  - option "control"
                  - option "measured"
                  - option "target"
                  - option "value"
              - generic [ref=f1e212]:
                - text: Time basis
                - combobox "Time basis" [ref=f1e213]:
                  - option "No time window" [selected]
                  - option "Original source clock"
                  - option "Recorded receipt UTC"
            - paragraph [ref=f1e214]: The field predicate selects records and the returned value field. Original immutable payloads remain inspectable in Events.
            - generic [ref=f1e215]:
              - button "Apply evidence filters" [ref=f1e216] [cursor=pointer]
              - button "Reset evidence filters" [ref=f1e217] [cursor=pointer]
          - status "Evidence read quality" [ref=f1e218]:
            - generic [ref=f1e219]: "Matched: 2 · Returned: 2 · Omitted from page: 0"
            - generic [ref=f1e220]: "missingSourceTime: 0"
            - generic [ref=f1e221]: "malformedSourceTime: 0"
            - generic [ref=f1e222]: "otherClock: 0"
            - generic [ref=f1e223]: "missingReceiptTime: 0"
            - generic [ref=f1e224]: "unsupportedReceiptEncoding: 0"
            - generic [ref=f1e225]: "Reader integrity: valid"
          - generic [ref=f1e226]:
            - paragraph [ref=f1e227]: "Original clock: simulation-time · tick unit: microsecond. Exact endpoint ticks: 0 to 100000."
            - img "Recorded observation chart in simulation-time. Exact source ticks; missing time is not plotted." [ref=f1e228]:
              - generic [ref=f1e229]: "0.000"
              - generic [ref=f1e231]: "0.2500"
              - generic [ref=f1e233]: "0.5000"
              - generic [ref=f1e235]: "0.7500"
              - generic [ref=f1e237]: "1.000"
              - generic [ref=f1e239]: "0"
              - generic [ref=f1e240]: "100000"
            - generic [ref=f1e256]:
              - generic [ref=f1e257]: control
              - generic [ref=f1e259]: measured
              - generic [ref=f1e261]: target
              - generic [ref=f1e263]: value
          - generic [ref=f1e265]:
            - button "Previous observation page" [disabled] [ref=f1e266]
            - button "Next observation page" [disabled] [ref=f1e267]
          - generic [ref=f1e268]:
            - generic [ref=f1e269]:
              - text: "Clock:"
              - strong [ref=f1e270]: simulation-time
            - generic [ref=f1e271]:
              - text: "Unit:"
              - strong [ref=f1e272]: 1, 1, 1, 1
            - generic [ref=f1e273]:
              - text: "Reduction:"
              - strong [ref=f1e274]: page
        - generic [ref=f1e275]:
          - heading "Input and evidence provenance" [level=3] [ref=f1e276]
          - generic [ref=f1e277]:
            - generic [ref=f1e278]:
              - term [ref=f1e279]: Snapshot
              - definition [ref=f1e280]: snap-22bfbd94-905a-414d-9a71-d59436744e69
            - generic [ref=f1e281]:
              - term [ref=f1e282]: Plan digest
              - definition [ref=f1e283]: sha256:156f451a517a97b80580e49dcaa072278b8b523e4fffc294c1ea7507aab61467
            - generic [ref=f1e284]:
              - term [ref=f1e285]: Provider
              - definition [ref=f1e286]: studio.reference
            - generic [ref=f1e287]:
              - term [ref=f1e288]: Clock uncertainty
              - definition [ref=f1e289]: Not declared
            - generic [ref=f1e290]:
              - term [ref=f1e291]: Coverage
              - definition [ref=f1e292]: Unknown
          - group [ref=f1e293]:
            - generic "Inspect exact data" [ref=f1e294] [cursor=pointer]
      - generic [ref=f1e295]:
        - generic [ref=f1e296]: Local project · Saved on backend
        - generic [ref=f1e299]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e300]: 1 provider(s) available
```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test';
  2  | import {readFileSync} from 'node:fs';
  3  | import {createHash} from 'node:crypto';
  4  | import path from 'node:path';
  5  | import {connectStudio} from '../../tests/e2e/connect-studio';
  6  | import {traceApi} from '../../tests/e2e/trace-claims-flow';
  7  |
  8  | for(const width of [1024,1440]) test(`rejected rerun: actual capacity release permits explicit new admission at ${width}`,async({page},info)=>{
  9  |  test.setTimeout(90000);await page.setViewportSize({width,height:width===1024?768:900});await connectStudio(page,info);
  10 |  let project=(await traceApi(page,'/projects','POST',{name:'Native rejected rerun recovery '+width})).body;
  11 |  async function prepared(duration:number){
  12 |   const edited=await traceApi(page,`/projects/${project.projectId}/edits`,'POST',{baseRevision:project.revision,edits:[{kind:'set_parameter',parameterId:'duration',value:duration}]},project.revision);expect(edited.status).toBe(200);project=edited.body;
  13 |   const pf=await traceApi(page,`/projects/${project.projectId}/preflights`,'POST',{revision:project.revision});expect(pf.status).toBe(200);expect(pf.body.status).toBe('ready');return pf.body;
  14 |  }
  15 |  const originalInput=await prepared(0.2);
  16 |  const started=await traceApi(page,'/runs','POST',{snapshotId:originalInput.snapshotId,preflightId:originalInput.preflightId});expect(started.status).toBe(202);const original=started.body.runId;
  17 |  await expect.poll(async()=>(await traceApi(page,'/runs/'+original)).body.state,{timeout:20000}).toBe('stopped');
  18 |  const originalRun=(await traceApi(page,'/runs/'+original)).body;
  19 |  const files=[`runs/${original}/evidence.jsonl`,`snapshots/${originalRun.snapshotId}/snapshot.json`];
  20 |  const hash=(name:string)=>createHash('sha256').update(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!,name))).digest('hex');const before=Object.fromEntries(files.map(n=>[n,hash(n)]));
  21 |  await page.evaluate(({pid,rid})=>{localStorage.setItem('studio.projectId',pid);localStorage.setItem('studio.lastRun',rid);localStorage.setItem('studio.lastRun.'+pid,rid);},{pid:project.projectId,rid:original});
  22 |  await page.reload();await page.getByRole('tab',{name:'Results',exact:false}).click();await expect(page.getByLabel('Recorded run',{exact:true})).toHaveValue(original);
  23 |  const busyInput=await prepared(30);const busy:string[]=[];
  24 |  const attempts:{key:string;operationId?:string;status?:number}[]=[];
  25 |  page.on('request',request=>{if(request.method()==='POST' && request.url().endsWith(`/runs/${original}/reruns`))attempts.push({key:request.headers()['idempotency-key']||''});});
  26 |  page.on('response',async response=>{if(response.request().method()==='POST' && response.url().endsWith(`/runs/${original}/reruns`)){const body=await response.json();const row=attempts.find(a=>a.key===response.request().headers()['idempotency-key']&&a.operationId===undefined);if(row){row.operationId=body.operationId;row.status=response.status();}}});
  27 |  async function stopBusy(){for(const rid of busy){const run=(await traceApi(page,'/runs/'+rid)).body;if(run.state==='running'){const stop=await traceApi(page,`/runs/${rid}/commands`,'POST',{kind:'stop',expectedStateVersion:run.stateVersion});expect(stop.status).toBe(202);await expect.poll(async()=>(await traceApi(page,'/operations/'+stop.body.operationId)).body.status,{timeout:10000}).toBe('completed');}await expect.poll(async()=>(await traceApi(page,'/runs/'+rid)).body.state,{timeout:20000}).toBe('stopped');}}
  28 |  try{
  29 |   for(let i=0;i<4;i++){const result=await traceApi(page,'/runs','POST',{snapshotId:busyInput.snapshotId,preflightId:busyInput.preflightId});expect(result.status).toBe(202);busy.push(result.body.runId);}
  30 |   await expect.poll(async()=>Promise.all(busy.map(async rid=>(await traceApi(page,'/runs/'+rid)).body.state)),{timeout:20000}).toEqual(['running','running','running','running']);
  31 |   const button=page.getByRole('button',{name:'Rerun frozen inputs',exact:true});await button.focus();await page.keyboard.press('Enter');
  32 |   await expect.poll(()=>attempts[0]?.operationId).toBeTruthy();const first=(await traceApi(page,'/operations/'+attempts[0].operationId)).body;
  33 |   expect(first.status).toBe('rejected');expect(first.error.code).toBe('RESOURCE_BUSY');expect(first.sourceRunId).toBe(original);expect(first.parentSnapshotId).toBe(originalRun.snapshotId);expect(first.runId).toBeUndefined();expect(first.result).toBeUndefined();
  34 |   await expect(button).toBeEnabled();await expect(page.getByRole('alert')).toContainText('RESOURCE_BUSY');
  35 |   await stopBusy();
  36 |   await button.focus();await page.keyboard.press('Enter');await expect.poll(()=>attempts[1]?.operationId).toBeTruthy();
  37 |   const second=(await traceApi(page,'/operations/'+attempts[1].operationId)).body;
  38 |   const unchanged=files.every(n=>hash(n)===before[n]);
  39 |   await info.attach('native-rejected-rerun-recovery',{contentType:'application/json',body:JSON.stringify({scope:'Five actual owned runs; four reach running and are stopped through owned commands. No transport injection or canonical mutation.',width,original,originalSnapshotId:originalRun.snapshotId,busyRunIds:busy,first,second,attempts,canonicalOriginalBytesUnchanged:unchanged})});
  40 |   expect(unchanged).toBe(true);
> 41 |   expect(second.status,'Explicit rerun after verified rejection and real capacity release should receive fresh admission.').toBe('completed');
     |                                                                                                                             ^ Error: Explicit rerun after verified rejection and real capacity release should receive fresh admission.
  42 |   expect(second.operationId).not.toBe(first.operationId);expect(attempts[1].key).not.toBe(attempts[0].key);
  43 |   expect(second.result.runId).not.toBe(original);
  44 |   await expect.poll(async()=>(await traceApi(page,'/runs/'+second.result.runId)).body.state,{timeout:20000}).toBe('stopped');
  45 |   await expect(page.getByLabel('Recorded run',{exact:true})).toHaveValue(second.result.runId);
  46 |   const child=(await traceApi(page,`/runs/${second.result.runId}/snapshot`)).body;expect(child.integrity).toBe('valid');expect(child.snapshot.parentSnapshotId).toBe(originalRun.snapshotId);expect(child.snapshot.configuration.duration).toBe(0.2);
  47 |  } finally {await stopBusy();}
  48 | });
  49 |
```
