const tools=require('./autoverse-orca-tools.cjs')(process.argv[2]);
const {chromium,expect,fs,path,out,c,pause,key,replaceText,snapshot,observedSnapshot,spoken,speechText,focus}=tools;
const {parse}=require('yaml');
const button=(page,name)=>page.getByRole('button',{name,exact:true});
const scenario=project=>Object.values(project.documents).map(d=>parse(d.content)).find(d=>d?.kind==='Scenario');
function selectedMapping(text){
 const lines=text.split('\n'),rest=lines.slice(1).filter(line=>line.trim());
 const indent=rest.length?Math.min(...rest.map(line=>line.match(/^\s*/)[0].length)):0;
 return parse([lines[0],...lines.slice(1).map(line=>line.trim()?line.slice(indent):line)].join('\n'));
}
async function project(page){const r=await page.request.get(`/api/v1/projects/${c.projectId}`);expect(r.status()).toBe(200);return r.json();}
async function focused(target,name,offset,checkpoint){await expect(target).toBeFocused();await spoken(name,offset);const tree=await snapshot(checkpoint);expect(tree.lastFocusEvent?.name).toBe(name);return tree;}
async function open(page,target,name,title,checkpoint){
 await focus(page,target,name,checkpoint+'-opener');const offset=speechText().length;await key('Return');
 const dialog=page.getByRole('dialog',{name:title,exact:true});await expect(dialog).toBeVisible();
 const tree=await focused(dialog.getByRole('button',{name:'Close dialog',exact:true}),'Close dialog',offset,checkpoint+'-dialog');return {dialog,tree};
}
async function enter(page,label,value,checkpoint){const field=page.getByLabel(label,{exact:true});const tree=await focus(page,field,label,checkpoint);await replaceText(page,field,value);return tree;}
function editable(tree,name,value){expect(tree.rows.some(r=>r.editable&&r.name===name&&r.editableTextPrefix===value&&!r.editableTextTruncated)).toBe(true);}
async function submit(page,name,restore,restoreName,checkpoint,inspect){
 const tree=await focus(page,button(page,name),name,checkpoint+'-submit');if(inspect)inspect(tree);const offset=speechText().length;
 const response=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===`/api/v1/projects/${c.projectId}/edits`);
 await key('Return');expect((await response).status()).toBe(200);await expect(page.getByRole('dialog')).toHaveCount(0);await focused(restore,restoreName,offset,checkpoint+'-focus');
}
(async()=>{
 const browser=await chromium.launch({headless:false,args:['--disable-gpu','--disable-gpu-rasterization','--force-renderer-accessibility=complete','--password-store=basic']});
 try{
  const sourceOnly=c.suite==='scenario-fault-source';expect(['scenario-fault','scenario-fault-source']).toContain(c.suite);
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
  const original=scenario(before),resources=Object.values(before.documents).map(d=>parse(d.content)),id=`orca-fault-${c.width}`;
  const system=resources.find(d=>d?.kind==='System'&&d.metadata.name===original.spec.systemRef.name&&d.metadata.namespace===original.spec.systemRef.namespace);
  const profile=resources.find(d=>d?.kind==='Profile'&&d.metadata?.version==='0.1.0'&&d.spec?.extensionNamespace==='io.xverse.experiment'&&d.spec?.schemaRef==='https://xverse.io/profiles/experiment-lite/v0.1/schema.json');
  expect(profile,'The selected recording must retain its declared experiment-lite timing profile').toBeTruthy();
  const target={apiVersion:system.apiVersion,kind:'System',namespace:system.metadata.namespace,name:system.metadata.name,element:system.spec.nodes[0].id};
  const clock=system.spec.defaultTimeDomainId||system.spec.timeDomains[0].id;
  const activation=`Opaque activation ${c.width}; no runtime permission.`,recovery=`Opaque recovery ${c.width}; no runtime permission.`,editedRecovery=`Edited opaque recovery ${c.width}; no runtime permission.`;
  const expectedFault={id,targetRef:target,faultKind:'provider-defined',activation,recovery,maturity:'prototype',extensions:{'io.xverse.experiment':{schemaVersion:'0.1',kind:'fault-intent',target:{apiVersion:original.apiVersion,kind:'Scenario',namespace:original.metadata.namespace,name:original.metadata.name,element:id},trigger:{kind:'time',at:2,unit:'s'},duration:{value:2,unit:'s'},timeDomainId:clock}}};
  const add=button(page,'Add fault intent'),createdDialog=await open(page,add,'Add fault intent','Add fault intent','fault-add');
  const notice='No compatible provider fault choices are declared.';
  await expect(createdDialog.dialog).toContainText(notice);expect(createdDialog.tree.rows.some(r=>r.name.includes(notice))).toBe(true);
  await expect(page.getByLabel('Provider fault choice',{exact:true}).locator('option')).toHaveCount(1);
  await enter(page,'Scenario item identifier',id,'fault-id');
  const targetSelect=page.getByLabel('Declared target',{exact:true});await focus(page,targetSelect,'Declared target','fault-target');await key('Home');await key('Down');await key('Tab');
  await expect(targetSelect).toHaveValue(`xdl://${target.namespace}/system/${target.name}#${target.element}`);
  const clockSelect=page.getByLabel('Fault clock',{exact:true});await focus(page,clockSelect,'Fault clock','fault-clock');await expect(clockSelect).toHaveValue(clock);
  await enter(page,'Fault activation time','2','fault-activation-time');
  const atUnit=page.getByLabel('Fault activation unit',{exact:true});await focus(page,atUnit,'Fault activation unit','fault-activation-unit');await expect(atUnit).toHaveValue('s');
  await enter(page,'Fault duration',sourceOnly?'2':'0','fault-duration');
  const durationUnit=page.getByLabel('Fault duration unit',{exact:true});await focus(page,durationUnit,'Fault duration unit','fault-duration-unit');await expect(durationUnit).toHaveValue('s');
  await enter(page,'Activation intent',activation,'activation-intent');await enter(page,'Recovery intent',recovery,'recovery-intent');
  await expect(page.getByLabel('Fault maturity',{exact:true})).toHaveValue('prototype');
  function values(tree,duration,expectedRecovery=recovery){editable(tree,'Activation intent',activation);editable(tree,'Recovery intent',expectedRecovery);editable(tree,'Fault activation time','2');editable(tree,'Fault duration',duration);}
  if(!sourceOnly){
   const invalid=await focus(page,button(page,'Add scenario item'),'Add scenario item','invalid-duration-submit');values(invalid,'0');const rejectedOffset=speechText().length;await key('Return');
   const message='Choose a declared fault clock and finite nonnegative activation time with positive duration.';
   await expect(createdDialog.dialog.getByRole('alert')).toHaveText(message);await spoken(message,rejectedOffset);expect(await project(page)).toEqual(before);expect(writes).toEqual([]);
   const corrected=await enter(page,'Fault duration','2','correct-duration');expect(corrected.rows.some(r=>r.name.includes(message))).toBe(true);
  }
  await submit(page,'Add scenario item',add,'Add fault intent','fault-created',tree=>values(tree,'2'));
  const first=await project(page);history.push(first);const expectedFirst=structuredClone(original);expectedFirst.spec.faults.push(expectedFault);expect(scenario(first)).toEqual(expectedFirst);expect(first.revision).toBe(before.revision+1);
  let current=first;
  if(sourceOnly){
   const sourceName=`View source for fault ${id}`,source=button(page,sourceName);await focus(page,source,sourceName,'fault-source');const offset=speechText().length;await key('Return');
   const dialog=page.getByRole('dialog',{name:'Authored XDL source',exact:true});await expect(dialog).toBeVisible();await expect(page.getByLabel('XDL source',{exact:true})).toBeFocused();await spoken('XDL source',offset);
   const anchored=await observedSnapshot('selected-fault-source',tree=>tree.rows.some(r=>r.name==='XDL source'&&r.selectedTextPrefix?.includes(id)));
   const selections=anchored.rows.filter(r=>r.name==='XDL source'&&r.selectedTextPrefix!==undefined);expect(selections.length).toBeGreaterThan(0);
   for(const row of selections){expect(row.selectedTextTruncated).toBe(false);expect(selectedMapping(row.selectedTextPrefix)).toEqual(expectedFault);}
   await expect(dialog.getByRole('button',{name:'Save source revision',exact:true})).toBeDisabled();const cancelOffset=speechText().length;await key('Escape');await expect(dialog).toHaveCount(0);await focused(source,sourceName,cancelOffset,'fault-source-return');expect(await project(page)).toEqual(first);
  }else{
   const editName=`Edit fault ${id}`,edit=button(page,editName);await open(page,edit,editName,'Edit fault intent','fault-edit');
   await expect(page.getByLabel('Scenario item identifier',{exact:true})).toBeDisabled();await enter(page,'Recovery intent',editedRecovery,'edited-recovery');
   await submit(page,'Save scenario item',edit,editName,'fault-updated',tree=>values(tree,'2',editedRecovery));
   current=await project(page);history.push(current);const expectedUpdated=structuredClone(expectedFirst);expectedUpdated.spec.faults.at(-1).recovery=editedRecovery;expect(scenario(current)).toEqual(expectedUpdated);expect(current.revision).toBe(before.revision+2);
  }
  const removeName=`Remove fault ${id}`,remove=button(page,removeName);const removal=await open(page,remove,removeName,'Remove authored scenario item','fault-remove');
  const cancelOffset=speechText().length;await key('Escape');await expect(removal.dialog).toHaveCount(0);await focused(remove,removeName,cancelOffset,'fault-keep');expect(await project(page)).toEqual(current);
  const reopenOffset=speechText().length;await key('Return');await focused(page.getByRole('dialog').getByRole('button',{name:'Close dialog',exact:true}),'Close dialog',reopenOffset,'fault-remove-reopen');
  await submit(page,'Remove draft item',add,'Add fault intent','fault-removed');const removed=await project(page);history.push(removed);expect(scenario(removed)).toEqual(original);expect(removed.revision).toBe(before.revision+(sourceOnly?2:3));await expect(remove).toHaveCount(0);
  const kinds=sourceOnly?['add_scenario_item','remove_scenario_item']:['add_scenario_item','update_scenario_item','remove_scenario_item'];expect(writes).toHaveLength(kinds.length);
  for(let i=0;i<kinds.length;i++){expect(writes[i].method).toBe('POST');expect(writes[i].path).toBe(`/api/v1/projects/${c.projectId}/edits`);expect(writes[i].body.baseRevision).toBe(before.revision+i);expect(writes[i].body.edits).toHaveLength(1);expect(writes[i].body.edits[0].kind).toBe(kinds[i]);expect(writes[i].body.edits[0].itemKind).toBe('fault');expect(writes[i].body.edits[0].itemId).toBe(id);}
  fs.writeFileSync(path.join(out,'authoring-history.private.json'),JSON.stringify(history,null,2));
  fs.writeFileSync(path.join(out,'browser-result.json'),JSON.stringify({suite:c.suite,width:c.width,version:browser.version(),commands:tools.keyCount,writes,expectedFault,actualTimedFieldsAndIntentTextVerified:true,providerChoicesUnavailableThroughAt:true,zeroDurationRefusalTested:!sourceOnly,zeroDurationRefusalAnnounced:sourceOnly?null:true,zeroDurationRefusalProjectUnchanged:sourceOnly?null:true,sourceInspectionTested:sourceOnly,selectedSourceVerifiedThroughAtSpi:sourceOnly,sourceDirectEscapeFocusAndSpeechVerified:sourceOnly,removalCancelPreservesDraft:true,finalScenarioSemanticsRestored:true,fromRevision:before.revision,toRevision:removed.revision},null,2));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
