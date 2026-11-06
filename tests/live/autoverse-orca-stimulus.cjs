const tools=require('./autoverse-orca-tools.cjs')(process.argv[2]);
const {chromium,expect,fs,path,out,c,pause,key,replaceText,snapshot,observedSnapshot,spoken,speechText,focus}=tools;
const {parse}=require('yaml');
const button=(page,name)=>page.getByRole('button',{name,exact:true});
const scenario=project=>Object.values(project.documents).map(d=>parse(d.content)).find(d=>d?.kind==='Scenario');
function selectedMapping(text){
 const lines=text.split('\n'),rest=lines.slice(1).filter(line=>line.trim());
 const indent=rest.length?Math.min(...rest.map(line=>line.match(/^\s*/)[0].length)):0;
 // An AST mapping range starts after its enclosing sequence/indent prefix.
 // Restore a standalone mapping for comparison without changing saved bytes.
 return parse([lines[0],...lines.slice(1).map(line=>line.trim()?line.slice(indent):line)].join('\n'));
}
async function project(page){const r=await page.request.get(`/api/v1/projects/${c.projectId}`);expect(r.status()).toBe(200);return r.json();}
async function focused(target,name,offset,checkpoint){await expect(target).toBeFocused();await spoken(name,offset);const tree=await snapshot(checkpoint);expect(tree.lastFocusEvent?.name).toBe(name);return tree;}
async function enter(page,label,value,checkpoint){const field=page.getByLabel(label,{exact:true});await focus(page,field,label,checkpoint);await replaceText(page,field,value);}
async function submit(page,name,restore,restoreName,checkpoint){
 await focus(page,button(page,name),name,checkpoint+'-button');const offset=speechText().length;
 const response=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===`/api/v1/projects/${c.projectId}/edits`);
 await key('Return');expect((await response).status()).toBe(200);await expect(page.getByRole('dialog')).toHaveCount(0);await focused(restore,restoreName,offset,checkpoint+'-focus');
}
(async()=>{
 const browser=await chromium.launch({headless:false,args:['--disable-gpu','--disable-gpu-rasterization','--force-renderer-accessibility=complete','--password-store=basic']});
 try {
  const context=await browser.newContext({baseURL:c.url,viewport:{width:c.width,height:c.width===1024?768:900},storageState:JSON.parse(fs.readFileSync(path.join(out,'browser-session.private.json')))});
  const page=await context.newPage(),writes=[],history=[];
  page.on('request',r=>{if(r.method()!=='GET') writes.push({method:r.method(),path:new URL(r.url()).pathname,body:r.postDataJSON()});});
  await page.goto('/');await expect(button(page,'X-Verse Studio home')).toBeVisible();await page.bringToFront();await spoken('Page has');await pause(300);
  await focus(page,button(page,'X-Verse Studio home'),'X-Verse Studio home','home');await key('Return');
  const open=page.locator(`.project-list-row[data-project-id="${c.projectId}"] .project-open`);await expect(open).toBeVisible();
  for(let i=0;i<100&&!await open.evaluate(n=>n===document.activeElement);i++){await key('Tab');await pause(80);}
  await expect(open).toBeFocused();await key('Return');const before=await project(page);history.push(before);
  await focus(page,page.getByRole('tab',{name:'Experiments',exact:true}),'Experiments','experiments');await key('Return');
  await focus(page,page.getByRole('tab',{name:'Scenario',exact:true}),'Scenario','scenario');await key('Return');
  const original=scenario(before), id=`orca-step-${c.width}`,add=button(page,'Add stimulus step');
  const system=Object.values(before.documents).map(d=>parse(d.content)).find(d=>d?.kind==='System'&&d.metadata.name===original.spec.systemRef.name&&d.metadata.namespace===original.spec.systemRef.namespace);
  const target={apiVersion:system.apiVersion,kind:'System',namespace:system.metadata.namespace,name:system.metadata.name,element:system.spec.nodes[0].id};
  const action={parameter:'target',value:1,opaque:{retained:c.width}};
  const expectedStep={id,targetRef:target,timeDomainId:system.spec.timeDomains[0].id,actionKind:'set_parameter',schedule:{at:0,unit:'s'},action};
  await focus(page,add,'Add stimulus step','add-step');const openOffset=speechText().length;await key('Return');
  const dialog=page.getByRole('dialog',{name:'Add stimulus step',exact:true});await expect(dialog).toBeVisible();await focused(dialog.getByRole('button',{name:'Close dialog',exact:true}),'Close dialog',openOffset,'add-dialog');
  await enter(page,'Scenario item identifier',id,'identifier');
  const targetSelect=page.getByLabel('Declared target',{exact:true});await focus(page,targetSelect,'Declared target','target');await key('Home');await key('Down');await key('Tab');
  await expect(targetSelect).toHaveValue(`xdl://${target.namespace}/system/${target.name}#${target.element}`);
  await enter(page,'Action payload (JSON object)','[]','invalid-payload');
  await focus(page,button(page,'Add scenario item'),'Add scenario item','invalid-submit');const rejectedOffset=speechText().length;await key('Return');
  await expect(dialog.getByRole('alert')).toContainText('Supply a nonempty JSON object');await spoken('Supply a nonempty JSON object',rejectedOffset);
  const rejected=await snapshot('validation-error');expect(rejected.rows.some(r=>r.name.includes('Supply a nonempty JSON object'))).toBe(true);expect(await project(page)).toEqual(before);expect(writes).toEqual([]);
  await enter(page,'Action payload (JSON object)',JSON.stringify(action),'valid-payload');
  await submit(page,'Add scenario item',add,'Add stimulus step','created');const created=await project(page);history.push(created);
  const expectedCreated=structuredClone(original);expectedCreated.spec.steps.push(expectedStep);expect(scenario(created)).toEqual(expectedCreated);expect(created.revision).toBe(before.revision+1);
  const sourceName=`View source for step ${id}`,source=button(page,sourceName);await focus(page,source,sourceName,'source-button');const sourceOffset=speechText().length;await key('Return');
  const sourceDialog=page.getByRole('dialog',{name:'Authored XDL source',exact:true});await expect(sourceDialog).toBeVisible();const text=page.getByLabel('XDL source',{exact:true});
  await expect(text).toBeFocused();await spoken('XDL source',sourceOffset);
  const anchored=await observedSnapshot('selected-source',tree=>tree.rows.some(r=>r.name==='XDL source'&&r.selectedTextPrefix?.includes(id)));
  const selections=anchored.rows.filter(r=>r.name==='XDL source'&&r.selectedTextPrefix!==undefined);expect(selections.length).toBeGreaterThan(0);
  for(const r of selections){expect(r.selectedTextTruncated).toBe(false);expect(selectedMapping(r.selectedTextPrefix)).toEqual(expectedStep);}
  await expect(sourceDialog.getByRole('button',{name:'Save source revision',exact:true})).toBeDisabled();
  if(c.sourceExit==='close-button') await focus(page,sourceDialog.getByRole('button',{name:'Close dialog',exact:true}),'Close dialog','source-close-button');
  const sourceCancelOffset=speechText().length;await key(c.sourceExit==='close-button'?'Return':'Escape');await expect(sourceDialog).toHaveCount(0);await focused(source,sourceName,sourceCancelOffset,'source-return');expect(await project(page)).toEqual(created);
  const editName=`Edit step ${id}`,edit=button(page,editName);await focus(page,edit,editName,'edit-button');const editOffset=speechText().length;await key('Return');
  const editDialog=page.getByRole('dialog',{name:'Edit stimulus step',exact:true});await focused(editDialog.getByRole('button',{name:'Close dialog',exact:true}),'Close dialog',editOffset,'edit-dialog');
  await expect(page.getByLabel('Scenario item identifier',{exact:true})).toBeDisabled();await enter(page,'Scheduled at','0.5','edit-schedule');
  const scheduleReadback=await snapshot('edited-schedule-value');expect(scheduleReadback.rows.some(r=>r.editable&&r.name==='Scheduled at'&&r.editableTextPrefix==='0.5'&&!r.editableTextTruncated)).toBe(true);
  await submit(page,'Save scenario item',edit,editName,'updated');const updated=await project(page);history.push(updated);
  const expectedUpdated=structuredClone(expectedCreated);expectedUpdated.spec.steps.at(-1).schedule.at=0.5;expect(scenario(updated)).toEqual(expectedUpdated);expect(updated.revision).toBe(before.revision+2);
  const removeName=`Remove step ${id}`,remove=button(page,removeName);await focus(page,remove,removeName,'remove-button');const removeOffset=speechText().length;await key('Return');
  const removeDialog=page.getByRole('dialog',{name:'Remove authored scenario item',exact:true});await focused(removeDialog.getByRole('button',{name:'Close dialog',exact:true}),'Close dialog',removeOffset,'remove-dialog');
  const keepOffset=speechText().length;await key('Escape');await expect(removeDialog).toHaveCount(0);await focused(remove,removeName,keepOffset,'keep-focus');expect(await project(page)).toEqual(updated);
  const reopenOffset=speechText().length;await key('Return');await focused(removeDialog.getByRole('button',{name:'Close dialog',exact:true}),'Close dialog',reopenOffset,'remove-reopen');
  await submit(page,'Remove draft item',add,'Add stimulus step','removed');const removed=await project(page);history.push(removed);
  expect(scenario(removed)).toEqual(original);expect(removed.revision).toBe(before.revision+3);await expect(remove).toHaveCount(0);
  expect(writes).toHaveLength(3);const kinds=['add_scenario_item','update_scenario_item','remove_scenario_item'];
  for(let i=0;i<3;i++){expect(writes[i].path).toBe(`/api/v1/projects/${c.projectId}/edits`);expect(writes[i].method).toBe('POST');expect(writes[i].body.baseRevision).toBe(before.revision+i);expect(writes[i].body.edits).toHaveLength(1);expect(writes[i].body.edits[0].kind).toBe(kinds[i]);expect(writes[i].body.edits[0].itemId).toBe(id);}
  fs.writeFileSync(path.join(out,'authoring-history.private.json'),JSON.stringify(history,null,2));
  fs.writeFileSync(path.join(out,'browser-result.json'),JSON.stringify({suite:c.suite,sourceExit:c.sourceExit,width:c.width,version:browser.version(),commands:tools.keyCount,writes,expectedStep,selectedSourceVerifiedThroughAtSpi:true,invalidJsonAnnounced:true,removalCancelPreservesDraft:true,finalScenarioSemanticsRestored:true,fromRevision:before.revision,toRevision:removed.revision},null,2));
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
