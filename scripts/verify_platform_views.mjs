/** Read-only linked-view verification against actual retained evidence. No execution request is sent. */
import { chromium, expect } from '@playwright/test';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const [dataArg,url]=process.argv.slice(2);
assert(dataArg && /^http:\/\/127\.0\.0\.1:\d+$/.test(url), 'Usage: node scripts/verify_platform_views.mjs private-data-dir loopback-url');
const data=path.resolve(dataArg);
const identities=JSON.parse(readFileSync(path.join(data,'platform-view-selection.private.json'),'utf8'));
const session=path.join(data,'browser-session.private.json');
const reuse=existsSync(session)&&JSON.parse(readFileSync(session,'utf8')).cookies.length>0;
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({...reuse?{storageState:session}:{},baseURL:url,viewport:{width:1440,height:900}});
const page=await context.newPage();page.setDefaultTimeout(15000);
const report={scope:'actual historical complete backend experiment, linked browser read projection only; reconstructed Studio metadata envelope; no browser Start/Stop or driving claim',outcome:'failed',runId:identities.runId,responses:[],errors:[]};
page.on('pageerror',e=>report.errors.push(e.message));
page.on('response',async r=>{if(r.url().includes('/platform?')&&r.ok()){const b=await r.json();report.responses.push({view:b.view,snapshotId:b.snapshotId,sourceWitness:b.sourceWitness,identity:b.identity,counts:b.counts,filter:b.effectiveFilter,evidence:b.evidence});}});
try{
 await page.goto('/');
 if(!reuse){
 const token=JSON.parse(readFileSync(path.join(data,'bootstrap.json'),'utf8')).bootstrapToken;
 await page.getByLabel('Bootstrap token').fill(token);await page.getByRole('button',{name:'Open workspace',exact:true}).click();await expect(page.getByRole('button',{name:'X-Verse Studio home',exact:true})).toBeVisible();
 }
 await page.evaluate(({projectId,runId})=>{localStorage.setItem('studio.projectId',projectId);localStorage.setItem('studio.lastRun.'+projectId,runId);localStorage.setItem('studio.lastRun',runId);},identities);
 await page.reload();await page.getByRole('tab',{name:/^Results/}).click();
 const panel=page.getByRole('region',{name:'Linked platform views',exact:true});
 await page.getByRole('tab',{name:'Communications',exact:true}).click();
 await expect(panel.getByRole('button',{name:'Original cause',exact:true}).first()).toBeVisible();
 await expect(panel).toContainText('Sequence: not supplied');
 await expect(panel).toContainText('Upstream cause: unknown');
 await panel.getByRole('button',{name:'Original cause',exact:true}).first().focus();await page.keyboard.press('Enter');
 await expect(panel.getByRole('heading',{name:'Evidence · X-Verse platform',exact:true})).toBeFocused();
 await expect(panel.getByText('Native ingress fact',{exact:true})).toBeVisible();
 await panel.getByRole('button',{name:'Correlated orchestration',exact:true}).click();
 await expect(panel.getByRole('heading',{name:'Orchestration · X-Verse platform',exact:true})).toBeFocused();
 await panel.getByRole('button',{name:'Clear platform selection',exact:true}).click();
 await expect(panel.getByRole('button',{name:'Next platform page',exact:true})).toBeEnabled();
 await panel.getByRole('button',{name:'Next platform page',exact:true}).click();
 await expect(panel.getByText(/^51–/)).toBeVisible();
 await page.getByRole('tab',{name:'Communications',exact:true}).click();
 await expect(panel.getByRole('button',{name:'Original cause',exact:true}).first()).toBeVisible();
 await expect(panel.getByText(`1–50 of ${identities.expectedCounts.communications} matching records`,{exact:true})).toBeVisible();
 await page.getByRole('tab',{name:'Evidence',exact:true}).click();
 await expect(panel.getByText(`1–50 of ${identities.expectedCounts.retained} matching records`,{exact:true})).toBeVisible();
 await panel.getByRole('button',{name:'Evidence record',exact:true}).first().click();
 await expect(panel.getByText('1–1 of 1 matching records',{exact:true})).toBeVisible();
 assert.equal(new Set(report.responses.map(r=>r.snapshotId)).size,1);
 assert.equal(new Set(report.responses.map(r=>r.sourceWitness)).size,1);
 assert(report.responses.every(r=>r.identity.runId===identities.runId));
 assert(report.responses.every(r=>r.counts.retained===identities.expectedCounts.retained&&r.counts.orchestration===identities.expectedCounts.orchestration&&r.counts.communications===identities.expectedCounts.communications));
 assert(report.responses.every(r=>r.evidence.recorded===identities.expectedEvidence.recorded&&r.evidence.assessed===identities.expectedEvidence.assessed));
 await panel.getByRole('button',{name:'Clear platform selection',exact:true}).click();
 await expect(panel.getByText(`1–50 of ${identities.expectedCounts.retained} matching records`,{exact:true})).toBeVisible();
 const scroll=panel.getByRole('region',{name:'Platform record table',exact:true});
 await scroll.focus();await page.keyboard.press('PageDown');
 await expect.poll(()=>scroll.evaluate(el=>el.scrollTop)).toBeGreaterThan(0);
 await page.screenshot({path:path.join(data,'linked-views-1440.png'),fullPage:true});
 await page.setViewportSize({width:1024,height:768});
 await page.getByRole('tab',{name:'Communications',exact:true}).click();
 if(await panel.getByRole('button',{name:'Clear platform selection',exact:true}).count()) await panel.getByRole('button',{name:'Clear platform selection',exact:true}).click();
 await expect(panel.getByRole('button',{name:'Original cause',exact:true}).first()).toBeVisible();
 const bounds=await panel.boundingBox();assert(bounds.x>=0&&bounds.x+bounds.width<=1025);
 await page.screenshot({path:path.join(data,'linked-views-1024.png'),fullPage:true});
 assert.equal(report.errors.length,0,report.errors.join('\n'));
 report.outcome='passed';console.log('ACTUAL_HISTORICAL_LINKED_BROWSER_VIEWS_PASS',identities.runId);
}catch(e){report.failure=e.message;console.log('FAILURE',e.message);await page.screenshot({path:path.join(data,'failure.png'),fullPage:true});process.exitCode=1;}
finally{writeFileSync(path.join(data,'browser-verification.json'),JSON.stringify(report,null,2)+'\n',{mode:0o600});await context.storageState({path:path.join(data,'browser-session.private.json')});await browser.close();}
