const {chromium,expect}=require('@playwright/test');
const fs=require('node:fs');
const path=require('node:path');
const out=process.argv[2];
const c=JSON.parse(fs.readFileSync(path.join(out,'context.private.json')));
for (const [name,field] of [['mnt','hostMount'],['pid','hostPid'],['ipc','hostIpc']]) {
 if(fs.readlinkSync('/proc/self/ns/'+name)===c[field]) throw Error('Private AT namespace required');
}
if(process.env.DISPLAY!==':71'||!process.env.DBUS_SESSION_BUS_ADDRESS) throw Error('Private AT display/session required');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
function writeJSON(name,value) {
 const destination=path.join(out,name);
 fs.writeFileSync(destination+'.tmp',JSON.stringify(value));
 fs.renameSync(destination+'.tmp',destination);
}
let keyId=0;
async function key(key) {
 const id=++keyId;
 writeJSON('key-request.json',{id,key});
 for(let i=0;i<100;i++) {
  const p=path.join(out,'key-ack.json');
  if(fs.existsSync(p)&&JSON.parse(fs.readFileSync(p)).id===id) return;
  await pause(20);
 }
 throw Error('Owned XTest key acknowledgement deadline');
}
async function snapshot(name) {
  writeJSON('snapshot-request.json',{name});
  for(let i=0;i<100;i++) {
    const p=path.join(out,name+'.atspi.private.json');
    if(fs.existsSync(p)) {
     const tree=JSON.parse(fs.readFileSync(p));
     if(tree.errors||tree.truncated||tree.droppedEvents||tree.eventErrors) throw Error('Incomplete actual AT-SPI observation');
     return tree;
    }
    await pause(100);
  }
  throw Error('Actual AT-SPI snapshot deadline');
}
async function spoken(text,offset=0) {
 const p=path.join(out,'speech-logs/speech-dispatcher.log');
 for(let i=0;i<100;i++) {
  const speech=fs.readFileSync(p,'utf8').slice(offset).replace(/<[^>]*>/g,'')
    .replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&apos;/g,"'").replace(/&amp;/g,'&');
  if(speech.includes(text)) return;
  await pause(100);
 }
 throw Error('Actual Orca SSIP utterance deadline: '+text);
}
const speechText=()=>fs.readFileSync(path.join(out,'speech-logs/speech-dispatcher.log'),'utf8');
async function focus(page,target,name,checkpoint) {
 await expect(target).toBeVisible();
 const offset=speechText().length;
 for(let i=0;i<100;i++) {
  if(await target.evaluate(n=>n===document.activeElement)) {
   if(!await target.evaluate(n=>{
    const r=n.getBoundingClientRect(),s=getComputedStyle(n);
    return r.left>=0&&r.top>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1&&s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>=2;
   })) throw Error('Focused AT control is clipped or lacks a visible outline: '+name);
   await spoken(name,offset);
   const tree=await snapshot(checkpoint);
   if(tree.lastFocusEvent?.name!==name) throw Error('AT-SPI focus mismatch for '+name);
   return tree;
  }
  await key('Tab');
  await pause(80);
 }
 throw Error('Native keyboard target unreachable: '+name);
}
(async()=>{
 const browser=await chromium.launch({headless:false,args:['--disable-gpu','--disable-gpu-rasterization','--force-renderer-accessibility=complete','--password-store=basic']});
 try {
  const context=await browser.newContext({baseURL:c.url,viewport:{width:c.width,height:c.width===1024?768:900},storageState:JSON.parse(fs.readFileSync(path.join(out,'browser-session.private.json')))});
  const page=await context.newPage();
  const writes=[];
  page.on('request',request=>{if(request.method()!=='GET') writes.push(new URL(request.url()).pathname);});
  await page.goto('/');
  await expect(page.getByRole('button',{name:'X-Verse Studio home',exact:true})).toBeVisible();
  await page.bringToFront();
  await spoken('Page has');
  await pause(300);
  const home=await snapshot('home');
  const homeButton=page.getByRole('button',{name:'X-Verse Studio home',exact:true});
  const focused=await focus(page,homeButton,'X-Verse Studio home','home-button');
  await key('Return');
  const open=page.locator(`.project-list-row[data-project-id="${c.projectId}"] .project-open`);
  const projectName=(await open.innerText()).trim();
  // Accessible names can contain the descriptive text of a project row.
  await expect(open).toBeVisible();
  for(let i=0;i<100 && !await open.evaluate(n=>n===document.activeElement);i++) {await key('Tab');await pause(80);}
  await expect(open).toBeFocused();
  const projectFocus=await snapshot('project-open');
  await key('Return');
  await expect(page.locator('.project-header h1')).toBeVisible();
  const results=page.getByRole('tab',{name:/^Results(?:\s+\d+)?$/});
  await focus(page,results,'Results','results-tab');
  await key('Return');
  const selector=page.getByLabel('Recorded run',{exact:true});
  await expect(selector).toHaveValue('');
  await expect(selector.locator(`option[value="${c.runId}"]`)).toHaveCount(1);
  await focus(page,selector,'Recorded run','recorded-run-select');
  await key('Down');
  await expect(page.getByLabel('Recorded run',{exact:true})).toHaveValue(c.runId);
  await expect(selector).toBeFocused();
  const diagnosis=page.getByRole('tab',{name:'Diagnosis',exact:true});
  await focus(page,diagnosis,'Diagnosis','diagnosis-tab');
  await key('Return');
  const panel=page.getByRole('region',{name:'Run diagnosis',exact:true});
  await expect(panel).toHaveAttribute('data-explanation-state','loaded');
  await expect(panel).toContainText('TIME_MAPPING_INCOMPATIBLE');
  const diagnosisTree=await snapshot('diagnosis-loaded');
  if(!diagnosisTree.rows.some(r=>r.name==='Run diagnosis'&&['section','landmark'].includes(r.role))) throw Error('Diagnosis missing from AT-SPI');
  if(!diagnosisTree.rows.some(r=>r.name.includes('TIME_MAPPING_INCOMPATIBLE'))) throw Error('Actual diagnostic code missing from AT-SPI');
  const actionName='Inspect the referenced retained events and logs.';
  await focus(page,panel.locator('[data-diagnostic-class="incompatible_time_mapping"]').getByRole('button',{name:actionName,exact:true}),actionName,'diagnostic-action');
  const actionOffset=speechText().length;
  await key('Return');
  const events=page.getByRole('tab',{name:/^Events & logs/});
  await expect(events).toBeFocused();
  await expect(events).toHaveAttribute('aria-selected','true');
  await spoken('Events & logs',actionOffset);
  const eventTree=await snapshot('events-navigation');
  if(!eventTree.lastFocusEvent?.name.startsWith('Events & logs')||eventTree.lastFocusEvent?.role!=='page tab') throw Error('Referenced events focus missing from AT-SPI');
  if(writes.length) throw Error('Unexpected mutating request in retained AT inspection');
  fs.writeFileSync(path.join(out,'browser-result.json'),JSON.stringify({version:browser.version(),width:c.width,homeRows:home.rows.length,focusedHome:focused.lastFocusEvent,projectFocus:projectFocus.lastFocusEvent,projectName,diagnosisRows:diagnosisTree.rows.length,eventsFocus:eventTree.lastFocusEvent,keys:keyId,writes},null,2));
  for(const tree of [home,focused,projectFocus,diagnosisTree]) if(tree.errors||tree.truncated) throw Error('Incomplete actual AT-SPI tree');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
