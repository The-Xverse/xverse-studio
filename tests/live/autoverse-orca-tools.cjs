module.exports = function createOrcaTools(out) {
const {chromium,expect}=require('@playwright/test');
const fs=require('node:fs');
const path=require('node:path');
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
async function command(payload,attempts=100) {
 const id=++keyId;
 writeJSON('key-request.json',{id,...payload});
 for(let i=0;i<attempts;i++) {
  const p=path.join(out,'key-ack.json');
  if(fs.existsSync(p)&&JSON.parse(fs.readFileSync(p)).id===id) return;
  await pause(20);
 }
 throw Error('Owned XTest key acknowledgement deadline');
}
async function key(key) {return command({key});}
async function replaceText(page,target,text) {
 await expect(target).toBeFocused();
 if(!text.length||text.length>2048||!/^[\x20-\x7e]+$/.test(text)) throw Error('Bounded printable ASCII required for this native-key test');
 await command({chord:'Control+a'});
 await command({text},500);
 await expect(target).toHaveValue(text);
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

return {chromium,expect,fs,path,out,c,pause,key,replaceText,snapshot,spoken,speechText,focus,writeJSON,get keyCount(){return keyId;}};
};
