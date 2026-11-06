const tools=require('./autoverse-orca-tools.cjs')(process.argv[2]);
const {chromium,expect,fs,path,out,c,pause,key,replaceText,snapshot,spoken,speechText,focus}=tools;
const {parse}=require('yaml');
const button=(page,name)=>page.getByRole('button',{name,exact:true});
const documentFor=project=>Object.values(project.documents).find(d=>parse(d.content)?.kind==='Scenario');
const model=project=>parse(documentFor(project).content);
async function project(page) {
 const response=await page.request.get(`/api/v1/projects/${c.projectId}`);
 expect(response.status()).toBe(200);
 return response.json();
}
async function checkFocused(target,name,offset,checkpoint) {
 await expect(target).toBeFocused();
 await spoken(name,offset);
 const tree=await snapshot(checkpoint);
 if(tree.lastFocusEvent?.name!==name) throw Error('Actual AT focus did not follow '+name);
 return tree;
}
(async()=>{
 const browser=await chromium.launch({headless:false,args:['--disable-gpu','--disable-gpu-rasterization','--force-renderer-accessibility=complete','--password-store=basic']});
 try {
  const context=await browser.newContext({baseURL:c.url,viewport:{width:c.width,height:c.width===1024?768:900},storageState:JSON.parse(fs.readFileSync(path.join(out,'browser-session.private.json')))});
  const page=await context.newPage(),writes=[];
  page.on('request',request=>{if(request.method()!=='GET') writes.push({method:request.method(),path:new URL(request.url()).pathname,body:request.postDataJSON()});});
  await page.goto('/');
  await expect(button(page,'X-Verse Studio home')).toBeVisible();
  await page.bringToFront();
  await spoken('Page has'); await pause(300);
  await focus(page,button(page,'X-Verse Studio home'),'X-Verse Studio home','home-button');
  await key('Return');
  const open=page.locator(`.project-list-row[data-project-id="${c.projectId}"] .project-open`);
  await expect(open).toBeVisible();
  for(let i=0;i<100&&!await open.evaluate(n=>n===document.activeElement);i++){await key('Tab');await pause(80);}
  await expect(open).toBeFocused();await key('Return');
  const before=await project(page);
  await focus(page,page.getByRole('tab',{name:'Experiments',exact:true}),'Experiments','experiments-tab');await key('Return');
  await focus(page,page.getByRole('tab',{name:'Scenario',exact:true}),'Scenario','scenario-tab');await key('Return');
  await expect(page.getByRole('region',{name:'Scenario authoring',exact:true})).toBeVisible();
  const opener=button(page,'Edit initial conditions');
  await focus(page,opener,'Edit initial conditions','conditions-opener');
  const openOffset=speechText().length; await key('Return');
  const dialog=page.getByRole('dialog',{name:'Edit scenario conditions',exact:true});
  await expect(dialog).toBeVisible();
  const opened=await checkFocused(dialog.getByRole('button',{name:'Close dialog',exact:true}),'Close dialog',openOffset,'conditions-dialog');
  expect(opened.rows.some(r=>r.name==='Edit scenario conditions'&&r.role==='dialog')).toBe(true);
  const label='Initial conditions (JSON object)',field=page.getByLabel(label,{exact:true});
  await focus(page,field,label,'initial-field');
  await replaceText(page,field,'[]');
  await focus(page,button(page,'Save scenario conditions'),'Save scenario conditions','invalid-save');
  const invalidOffset=speechText().length; await key('Return');
  await expect(dialog.getByRole('alert')).toContainText('Supply a nonempty JSON object');
  await spoken('Supply a nonempty JSON object',invalidOffset);
  const rejected=await snapshot('invalid-announcement');
  expect(rejected.rows.some(r=>r.name.includes('Supply a nonempty JSON object'))).toBe(true);
  expect(await project(page)).toEqual(before); expect(writes).toEqual([]);
  const initial={...model(before).spec.initialConditions,orcaOpaque:{width:c.width,preserved:[1,'untouched']}};
  const text=JSON.stringify(initial).replace(/[\u007f-\uffff]/g,ch=>'\\u'+ch.charCodeAt(0).toString(16).padStart(4,'0'));
  await focus(page,field,label,'valid-field');
  await replaceText(page,field,text);
  const entered=await snapshot('native-text-entered');
  const actualText=entered.rows.filter(r=>r.name===label&&r.editable&&r.editableTextPrefix!==undefined);
  expect(actualText.length).toBeGreaterThan(0);
  expect(actualText.every(r=>!r.editableTextTruncated&&r.editableTextPrefix===text)).toBe(true);
  await focus(page,button(page,'Save scenario conditions'),'Save scenario conditions','valid-save');
  const saveOffset=speechText().length;
  const accepted=page.waitForResponse(r=>new URL(r.url()).pathname===`/api/v1/projects/${c.projectId}/edits`&&r.request().method()==='POST');
  await key('Return'); expect((await accepted).status()).toBe(200);
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await checkFocused(opener,'Edit initial conditions',saveOffset,'saved-focus');
  const after=await project(page);
  expect(after.revision).toBe(before.revision+1);
  const expected=parse(documentFor(before).content);expected.spec.initialConditions=initial;
  expect(model(after)).toEqual(expected);
  for(const [id,d] of Object.entries(before.documents)) if(d.path!==documentFor(before).path) expect(after.documents[id]).toEqual(d);
  const reopenOffset=speechText().length;await key('Return');
  await checkFocused(dialog.getByRole('button',{name:'Close dialog',exact:true}),'Close dialog',reopenOffset,'reopened-dialog');
  expect(JSON.parse(await field.inputValue())).toEqual(initial);
  const persisted=await snapshot('persisted-editable-value');
  const persistedFields=persisted.rows.filter(r=>r.name===label&&r.editable&&r.editableTextPrefix!==undefined);
  expect(persistedFields.length).toBeGreaterThan(0);
  for(const value of persistedFields) {expect(value.editableTextTruncated).toBe(false);expect(JSON.parse(value.editableTextPrefix)).toEqual(initial);}
  const cancelOffset=speechText().length;await key('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await checkFocused(opener,'Edit initial conditions',cancelOffset,'cancel-focus');
  expect(await project(page)).toEqual(after);
  expect(writes).toHaveLength(1);
  expect(writes[0].method).toBe('POST');expect(writes[0].path).toBe(`/api/v1/projects/${c.projectId}/edits`);
  expect(writes[0].body.baseRevision).toBe(before.revision);
  expect(writes[0].body.edits).toHaveLength(1);expect(writes[0].body.edits[0].kind).toBe('set_scenario_conditions');
  expect(writes[0].body.edits[0].properties.initialConditions).toEqual(initial);
  fs.writeFileSync(path.join(out,'browser-result.json'),JSON.stringify({suite:c.suite,version:browser.version(),width:c.width,commands:tools.keyCount,writes,initialConditions:initial,fromRevision:before.revision,toRevision:after.revision,invalidAnnouncement:true,persistedEditableTextVerified:true,cancelRetainsSavedProject:true},null,2));
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
