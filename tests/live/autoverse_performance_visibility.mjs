import { chromium } from "@playwright/test";
import fs from 'node:fs';
// Contributor-only readback of a selected, authenticated local benchmark root.
// Private session/cookie material is never written to the report or URL.
const [url, data, output] = process.argv.slice(2);
const selected = new URL(url);
if (selected.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(selected.hostname) || selected.username || selected.password) throw new Error('Select an explicit local native Studio origin');
const context = JSON.parse(fs.readFileSync(data + '/performance-context.private.json', 'utf8'));
const session = JSON.parse(fs.readFileSync(data + '/browser-session.private.json', 'utf8'));
const browser = await chromium.launch({ headless: true,
 ...(process.env.STUDIO_BROWSER_CPU_ONLY === '1'
   ? { args: ['--disable-gpu', '--disable-gpu-rasterization'] } : {}),
});
const observations = [];
try {
 const bc = await browser.newContext({ storageState: session });
 const page = await bc.newPage();
 const failures=[];
 page.on('pageerror',e=>failures.push({type:'pageerror',message:e.message.slice(0,1000)}));
 page.on('requestfailed',r=>failures.push({type:'requestfailed',path:new URL(r.url()).pathname,message:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)failures.push({type:'http',path:new URL(r.url()).pathname,status:r.status()});});
 for (const width of [1024,1440]) {
  await page.setViewportSize({width,height:width===1024?768:900});
  await page.goto(url);
  await page.getByRole('button',{name:'X-Verse Studio home',exact:true}).waitFor();
  await page.getByRole('button',{name:'X-Verse Studio home',exact:true}).click();
  await page.locator('.project-list').getByRole('button').filter({hasText:context.model.projectName}).click();
  try {
    await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node-element').length===200 && document.querySelectorAll('.react-flow__edge').length===400);
  } catch(error) {
    const state=await page.evaluate(()=>({title:document.querySelector('h1')?.textContent,nodes:document.querySelectorAll('.react-flow__node-element').length,edges:document.querySelectorAll('.react-flow__edge').length,body:document.body.textContent?.slice(0,1000)}));
    fs.writeFileSync(output+'.failure.json',JSON.stringify({state,failures},null,2));
    await page.screenshot({path:output+'.failure.png',fullPage:true});
    throw error;
  }
  await page.waitForFunction(()=>{
    const canvas=document.querySelector('.react-flow'); if(!canvas)return false;
    const c=canvas.getBoundingClientRect();
    return [...document.querySelectorAll('.react-flow__node-element')].every(n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n);return s.visibility==='visible'&&s.display!=='none'&&Number(s.opacity)!==0&&r.width>0&&r.height>0&&r.right>=c.left&&r.left<=c.right&&r.bottom>=c.top&&r.top<=c.bottom;});
  });
  const v=await page.evaluate(()=>{
    const nodes=[...document.querySelectorAll('.react-flow__node-element')],canvas=document.querySelector('.react-flow').getBoundingClientRect();
    return {visibleCssNodes:nodes.filter(n=>{const s=getComputedStyle(n);return s.visibility==='visible'&&s.display!=='none'&&Number(s.opacity)!==0;}).length,
      nodesIntersectingViewport:nodes.filter(n=>{const r=n.getBoundingClientRect();return r.width>0&&r.height>0&&r.right>=0&&r.left<=innerWidth&&r.bottom>=0&&r.top<=innerHeight;}).length,
      nodesIntersectingCanvas:nodes.filter(n=>{const r=n.getBoundingClientRect();return r.width>0&&r.height>0&&r.right>=canvas.left&&r.left<=canvas.right&&r.bottom>=canvas.top&&r.top<=canvas.bottom;}).length,
      uniqueNodeIds:new Set(nodes.map(n=>n.getAttribute('data-id'))).size,
      connections:document.querySelectorAll('.react-flow__edge').length,
      explorerElements:document.querySelectorAll('.tree-list button').length,
      horizontalPageOverflow:document.documentElement.scrollWidth>innerWidth+1};
  });
  if(v.visibleCssNodes!==200||v.nodesIntersectingViewport!==200||v.nodesIntersectingCanvas!==200||v.uniqueNodeIds!==200||v.connections!==400||v.explorerElements!==200||v.horizontalPageOverflow)throw Error('Actual visible-workload readback mismatch');
  observations.push({viewport:page.viewportSize(),...v});
 }
 await bc.close();
} finally { await browser.close(); }
fs.writeFileSync(output,JSON.stringify({scope:'Separate same-agent actual rendered-workload readback; no timings or execution',observations},null,2)+'\n');
