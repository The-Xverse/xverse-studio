# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: expanded.spec.ts >> frozen input inspection back at 1024
- Location: .studio-local/frozen-input-read-context/expanded.spec.ts:10:6

# Error details

```
Error: expect(locator).toHaveValue(expected) failed

Locator:  getByLabel('Recorded run', { exact: true })
Expected: "run-ee36d7be-f5df-4d35-97be-178fa7e83056"
Received: "run-2d56ca4a-c7e4-478f-978b-465ab7efce11"
Timeout:  10000ms

Call log:
  - Expect "toHaveValue" getByLabel('Recorded run', { exact: true }) with timeout 10000ms
  - waiting for getByLabel('Recorded run', { exact: true })
    24 × locator resolved to <select aria-label="Recorded run">…</select>
       - unexpected value "run-2d56ca4a-c7e4-478f-978b-465ab7efce11"

```

```yaml
- combobox "Recorded run":
  - option "run-2d56ca4a-c7e4-478f-978b-465ab7efce11 · stopped" [selected]
  - option "run-ee36d7be-f5df-4d35-97be-178fa7e83056 · stopped"
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
> 72  |    if(mode==='back') {await selected.focus();await page.keyboard.press('Home');await page.keyboard.press('Enter');await expect(selected).toHaveValue(original.runId);}
      |                                                                                                                                          ^ Error: expect(locator).toHaveValue(expected) failed
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
  92  |     expect(await dialog.getByRole('option',{name:'Complete authored revision · unavailable',exact:true}).isDisabled()).toBe(true);
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
