# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: probe.spec.ts >> actual rerun acknowledgement preserves a newer Model view at 1440
- Location: .studio-local/frozen-rerun-review/probe.spec.ts:6:7

# Error details

```
Error: expect(locator).toHaveAttribute(expected) failed

Locator:  getByRole('tab', { name: 'Model', exact: true })
Expected: "true"
Received: "false"
Timeout:  10000ms

Call log:
  - Expect "toHaveAttribute" getByRole('tab', { name: 'Model', exact: true }) with timeout 10000ms
  - waiting for getByRole('tab', { name: 'Model', exact: true })
    24 × locator resolved to <button class="" role="tab" aria-selected="false">…</button>
       - unexpected value "false"

```

```yaml
- tab "Model"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | import { connectStudio } from '../../tests/e2e/connect-studio';
  3  | import { traceApi } from '../../tests/e2e/trace-claims-flow';
  4  |
  5  | for (const width of [1024, 1440]) {
  6  |   test(`actual rerun acknowledgement preserves a newer Model view at ${width}`, async ({page}, info) => {
  7  |     await page.setViewportSize({width, height:width === 1024 ? 768 : 900});
  8  |     await connectStudio(page, info);
  9  |     let project = (await traceApi(page, '/projects', 'POST', {name:'Owned rerun view probe '+width})).body;
  10 |     const edited = await traceApi(page, `/projects/${project.projectId}/edits`, 'POST', {
  11 |       baseRevision:project.revision, edits:[{kind:'set_parameter',parameterId:'duration',value:0.2}],
  12 |     },project.revision);
  13 |     expect(edited.status).toBe(200); project=edited.body;
  14 |     const pf = (await traceApi(page, `/projects/${project.projectId}/preflights`, 'POST', {revision:project.revision})).body;
  15 |     expect(pf.status).toBe('ready');
  16 |     const accepted = await traceApi(page,'/runs','POST',{snapshotId:pf.snapshotId,preflightId:pf.preflightId});
  17 |     expect(accepted.status).toBe(202); const original=accepted.body.runId;
  18 |     await expect.poll(async ()=>(await traceApi(page,'/runs/'+original)).body.state,{timeout:20000}).toBe('stopped');
  19 |     await page.evaluate(({pid,rid})=>{
  20 |       localStorage.setItem('studio.projectId',pid);
  21 |       localStorage.setItem('studio.lastRun',rid);
  22 |       localStorage.setItem('studio.lastRun.'+pid,rid);
  23 |     },{pid:project.projectId,rid:original});
  24 |     await page.reload();
  25 |     await page.getByRole('tab',{name:'Results',exact:false}).click();
  26 |     await expect(page.getByLabel('Recorded run',{exact:true})).toHaveValue(original);
  27 |     let release!:()=>void, ready!:()=>void, completed!:()=>void;
  28 |     const held=new Promise<void>(resolve=>release=resolve);
  29 |     const actual=new Promise<void>(resolve=>ready=resolve);
  30 |     const delivered=new Promise<void>(resolve=>completed=resolve);
  31 |     let acknowledged:any;
  32 |     await page.route(`**/api/v1/runs/${original}/reruns`,async route=>{
  33 |       const response=await route.fetch();
  34 |       acknowledged=await response.json();
  35 |       expect(response.status()).toBe(202);
  36 |       ready(); await held;
  37 |       await route.fulfill({response}); completed();
  38 |     });
  39 |     const rerun=page.getByRole('button',{name:'Rerun frozen inputs',exact:true});
  40 |     await rerun.focus(); await page.keyboard.press('Enter');
  41 |     await actual;
  42 |     const operation=(await traceApi(page,'/operations/'+acknowledged.operationId)).body;
  43 |     expect(operation.status).toBe('completed');
  44 |     const child=operation.result.runId; expect(child).not.toBe(original);
  45 |     await expect.poll(async ()=>(await traceApi(page,'/runs/'+child)).body.state,{timeout:20000}).toBe('stopped');
  46 |     await page.getByRole('tab',{name:'Model',exact:true}).click();
  47 |     const focus=page.getByRole('button',{name:'Parameters',exact:true});
  48 |     await focus.focus();
  49 |     expect(await page.evaluate(()=>localStorage.getItem('studio.lastRun'))).toBe(original);
  50 |     release(); await delivered;
  51 |     await expect.poll(async()=>page.evaluate(()=>localStorage.getItem('studio.pendingRerun.'+localStorage.getItem('studio.lastRun'))),{timeout:10000}).toBeNull();
  52 |     await info.attach('actual-rerun-view-context',{contentType:'application/json',body:JSON.stringify({
  53 |       scope:'Actual native owned rerun; only its real HTTP202 delivery was held. No provider or evidence fixture substituted.',
  54 |       originalRunId:original,childRunId:child,operationId:acknowledged.operationId,
  55 |       intendedView:'Model',currentView:await page.getByRole('tab',{name:'Model',exact:true}).getAttribute('aria-selected'),
  56 |       currentRunId:await page.evaluate(()=>localStorage.getItem('studio.lastRun')),
  57 |     })});
> 58 |     await expect(page.getByRole('tab',{name:'Model',exact:true})).toHaveAttribute('aria-selected','true');
     |                                                                   ^ Error: expect(locator).toHaveAttribute(expected) failed
  59 |     await expect(focus).toBeFocused();
  60 |     expect(await page.evaluate(()=>localStorage.getItem('studio.lastRun'))).toBe(original);
  61 |   });
  62 | }
  63 |
```
