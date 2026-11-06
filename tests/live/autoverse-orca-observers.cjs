const tools=require('./autoverse-orca-tools.cjs')(process.argv[2]);
const {chromium,expect,fs,path,out,c,pause,key,replaceText,snapshot,spoken,speechText,focus}=tools;
const {parse}=require('yaml');
const button=(page,name)=>page.getByRole('button',{name,exact:true});
const scenario=project=>Object.values(project.documents).map(d=>parse(d.content)).find(d=>d?.kind==='Scenario');
async function project(page){const r=await page.request.get(`/api/v1/projects/${c.projectId}`);expect(r.status()).toBe(200);return r.json();}
async function focused(target,name,offset,checkpoint){await expect(target).toBeFocused();await spoken(name,offset);const tree=await snapshot(checkpoint);expect(tree.lastFocusEvent?.name).toBe(name);return tree;}
async function open(page,target,name,title,checkpoint){
 await focus(page,target,name,checkpoint+'-opener');const offset=speechText().length;await key('Return');
 const dialog=page.getByRole('dialog',{name:title,exact:true});await expect(dialog).toBeVisible();
 await focused(dialog.getByRole('button',{name:'Close dialog',exact:true}),'Close dialog',offset,checkpoint+'-dialog');return dialog;
}
async function enter(page,label,value,checkpoint){const field=page.getByLabel(label,{exact:true});await focus(page,field,label,checkpoint);await replaceText(page,field,value);}
async function submit(page,name,restore,restoreName,checkpoint,inspect){
 const tree=await focus(page,button(page,name),name,checkpoint+'-submit');if(inspect)inspect(tree);const offset=speechText().length;
 const response=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===`/api/v1/projects/${c.projectId}/edits`);
 await key('Return');expect((await response).status()).toBe(200);await expect(page.getByRole('dialog')).toHaveCount(0);await focused(restore,restoreName,offset,checkpoint+'-focus');
}
(async()=>{
 const browser=await chromium.launch({headless:false,args:['--disable-gpu','--disable-gpu-rasterization','--force-renderer-accessibility=complete','--password-store=basic']});
 try{
  const context=await browser.newContext({baseURL:c.url,viewport:{width:c.width,height:c.width===1024?768:900},storageState:JSON.parse(fs.readFileSync(path.join(out,'browser-session.private.json')))});
  const page=await context.newPage(),writes=[],history=[];
  page.on('request',r=>{if(r.method()!=='GET')writes.push({method:r.method(),path:new URL(r.url()).pathname,body:r.postDataJSON()});});
  await page.goto('/');await expect(button(page,'X-Verse Studio home')).toBeVisible();await page.bringToFront();await spoken('Page has');await pause(300);
  await focus(page,button(page,'X-Verse Studio home'),'X-Verse Studio home','home');await key('Return');
  const selected=page.locator(`.project-list-row[data-project-id="${c.projectId}"] .project-open`);await expect(selected).toBeVisible();
  for(let i=0;i<100&&!await selected.evaluate(n=>n===document.activeElement);i++){await key('Tab');await pause(80);}
  await expect(selected).toBeFocused();await key('Return');const before=await project(page);history.push(before);
  await focus(page,page.getByRole('tab',{name:'Experiments',exact:true}),'Experiments','experiments');await key('Return');
  await focus(page,page.getByRole('tab',{name:'Scenario',exact:true}),'Scenario','scenario');await key('Return');
  const original=scenario(before),observerId=`orca-observer-${c.width}`,metricId=`orca-metric-${c.width}`;
  const system=Object.values(before.documents).map(d=>parse(d.content)).find(d=>d?.kind==='System'&&d.metadata.name===original.spec.systemRef.name&&d.metadata.namespace===original.spec.systemRef.namespace);
  const target={apiVersion:system.apiVersion,kind:'System',namespace:system.metadata.namespace,name:system.metadata.name,element:system.spec.nodes[0].id};
  const sampling=`Opaque authored sampling ${c.width}; no live observation.`,acceptance=`Opaque authored acceptance ${c.width}; no verdict.`;
  const expectedObserver={id:observerId,targetRef:target,timeDomainId:system.spec.timeDomains[0].id,samplingIntent:sampling,payloadSchema:'urn:xverse:studio:normalized-scalar:v1',unitSemantics:'1',evidenceSinkRef:'urn:xverse:studio:reference:evidence'};
  const expectedMetric={id:metricId,observerIds:[observerId],calculationRef:'urn:example:metric:opaque',unitSemantics:'1',acceptance};
  const addObserver=button(page,'Add observer');await open(page,addObserver,'Add observer','Add observer','observer-add');
  await enter(page,'Scenario item identifier',observerId,'observer-id');
  const targetSelect=page.getByLabel('Declared target',{exact:true});await focus(page,targetSelect,'Declared target','observer-target');await key('Home');await key('Down');await key('Tab');
  await expect(targetSelect).toHaveValue(`xdl://${target.namespace}/system/${target.name}#${target.element}`);
  await enter(page,'Sampling intent',sampling,'sampling');
  await submit(page,'Add scenario item',addObserver,'Add observer','observer-created',tree=>expect(tree.rows.some(r=>r.editable&&r.name==='Sampling intent'&&r.editableTextPrefix===sampling&&!r.editableTextTruncated)).toBe(true));
  const first=await project(page);history.push(first);const expectedFirst=structuredClone(original);expectedFirst.spec.observers.push(expectedObserver);expect(scenario(first)).toEqual(expectedFirst);expect(first.revision).toBe(before.revision+1);
  const addMetric=button(page,'Add metric intent');const metricDialog=await open(page,addMetric,'Add metric intent','Add metric intent','metric-add');
  await enter(page,'Scenario item identifier',metricId,'metric-id');
  const choice=metricDialog.getByRole('group',{name:'Declared observers',exact:true}).getByLabel(observerId,{exact:true});
  await focus(page,choice,observerId,'observer-checkbox');await key('space');await expect(choice).toBeChecked();
  await enter(page,'Metric acceptance intent',acceptance,'acceptance');
  await submit(page,'Add scenario item',addMetric,'Add metric intent','metric-created',tree=>{
   expect(tree.rows.some(r=>r.editable&&r.name==='Metric acceptance intent'&&r.editableTextPrefix===acceptance&&!r.editableTextTruncated)).toBe(true);
   expect(tree.rows.some(r=>r.name===observerId&&r.role==='check box'&&r.checked)).toBe(true);
  });
  const second=await project(page);history.push(second);const expectedSecond=structuredClone(expectedFirst);expectedSecond.spec.metrics.push(expectedMetric);expect(scenario(second)).toEqual(expectedSecond);expect(second.revision).toBe(before.revision+2);
  const removeObserverName=`Remove observer ${observerId}`,removeObserver=button(page,removeObserverName);
  const removal=await open(page,removeObserver,removeObserverName,'Remove authored scenario item','reference-refusal');
  await focus(page,button(page,'Remove draft item'),'Remove draft item','refusal-submit');const rejectedOffset=speechText().length;
  const rejection=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===`/api/v1/projects/${c.projectId}/edits`);
  await key('Return');expect((await rejection).status()).toBe(422);const alert=removal.getByRole('alert');await expect(alert).toContainText(/reference|observer|valid/i);
  const error=(await alert.innerText()).trim();expect(error.length).toBeLessThanOrEqual(2048);await spoken(error,rejectedOffset);
  const rejected=await snapshot('reference-error');expect(rejected.rows.some(r=>r.name.includes(error))).toBe(true);expect(await project(page)).toEqual(second);
  const cancelOffset=speechText().length;await key('Escape');await expect(removal).toHaveCount(0);await focused(removeObserver,removeObserverName,cancelOffset,'refusal-cancel');expect(await project(page)).toEqual(second);
  const removeMetricName=`Remove metric ${metricId}`,removeMetric=button(page,removeMetricName);
  await open(page,removeMetric,removeMetricName,'Remove authored scenario item','metric-remove');
  await submit(page,'Remove draft item',addMetric,'Add metric intent','metric-removed');const third=await project(page);history.push(third);expect(scenario(third)).toEqual(expectedFirst);expect(third.revision).toBe(before.revision+3);await expect(removeMetric).toHaveCount(0);
  await open(page,removeObserver,removeObserverName,'Remove authored scenario item','observer-remove');
  await submit(page,'Remove draft item',addObserver,'Add observer','observer-removed');const fourth=await project(page);history.push(fourth);expect(scenario(fourth)).toEqual(original);expect(fourth.revision).toBe(before.revision+4);await expect(removeObserver).toHaveCount(0);
  expect(writes).toHaveLength(5);const kinds=['add_scenario_item','add_scenario_item','remove_scenario_item','remove_scenario_item','remove_scenario_item'];
  const items=['observer','metric','observer','metric','observer'],revisions=[0,1,2,2,3];
  for(let i=0;i<5;i++){expect(writes[i].path).toBe(`/api/v1/projects/${c.projectId}/edits`);expect(writes[i].method).toBe('POST');expect(writes[i].body.baseRevision).toBe(before.revision+revisions[i]);expect(writes[i].body.edits).toHaveLength(1);expect(writes[i].body.edits[0].kind).toBe(kinds[i]);expect(writes[i].body.edits[0].itemKind).toBe(items[i]);expect(writes[i].body.edits[0].itemId).toBe(items[i]==='observer'?observerId:metricId);}
  fs.writeFileSync(path.join(out,'authoring-history.private.json'),JSON.stringify(history,null,2));
  fs.writeFileSync(path.join(out,'browser-result.json'),JSON.stringify({suite:c.suite,width:c.width,version:browser.version(),commands:tools.keyCount,writes,expectedObserver,expectedMetric,referenceRefusalAnnounced:true,referenceRefusalProjectUnchanged:true,refusalCancelPreservesDraft:true,actualAtCheckedObserverVerified:true,actualAtIntentValuesVerified:true,finalScenarioSemanticsRestored:true,fromRevision:before.revision,toRevision:fourth.revision},null,2));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
