/** Explicit approved Linux simulation check. Real browser/HTTP/components only.
 * Run against a fresh isolated launcher with both native provider CLI options.
 * Data contains credentials; only the final sanitized report is shareable.
 */
import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, chmodSync } from 'node:fs';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import assert from 'node:assert/strict';
const [dataArg, url, python] = process.argv.slice(2);
assert(dataArg && /^http:\/\/127\.0\.0\.1:\d+$/.test(url) && python, 'Usage: node scripts/verify_platform_browser.mjs private-data-dir loopback-url enrolled-python');
const data = path.resolve(dataArg);
const browser = await chromium.launch({headless: true});
const context = await browser.newContext({ baseURL: url, ...(process.env.STUDIO_RESUME_RUN ? {storageState:path.join(data,'browser-session.private.json')} : {}), viewport: {width:1440,height:900} });
const page = await context.newPage();
page.setDefaultTimeout(20000);
let runId, completed = false;
const report = {scope:'actual complete Autoverse browser start/stop, owned Pygame input and linked public platform evidence', outcome:'failed', responses:[], errors:[]};
page.on('pageerror', error => report.errors.push(error.message));
page.on('response', async response => {
  if (response.url().includes('/platform?') && response.ok()) {
    const body = await response.json();
    report.responses.push({view:body.view,snapshotId:body.snapshotId,sourceWitness:body.sourceWitness,runId:body.identity.runId,counts:body.counts});
  }
});
const getRun = async () => (await page.request.get(`/api/v1/runs/${runId}`)).json();
try {
  await page.goto(url);
  if (process.env.STUDIO_RESUME_RUN) {
    const state = JSON.parse(readFileSync(path.join(data,'browser-session.private.json'),'utf8'));
    await context.addCookies(state.cookies);
    await page.reload();
  } else {
    const token = JSON.parse(readFileSync(path.join(data,'bootstrap.json'),'utf8')).bootstrapToken;
    await page.getByLabel('Bootstrap token').fill(token);
    await page.getByRole('button',{name:'Open workspace',exact:true}).click();
    await expect(page.getByRole('button',{name:'X-Verse Studio home',exact:true})).toBeVisible();
    await context.storageState({path:path.join(data,'browser-session.private.json')});
  chmodSync(path.join(data,'browser-session.private.json'),0o600);
  }
  if (!process.env.STUDIO_RESUME_RUN) {
  await page.locator('.example-grid').getByRole('button',{name:/Autoverse with X-Verse platform/}).click();
  await page.getByRole('button',{name:'Preflight & run',exact:true}).click();
  await expect(page.getByRole('button',{name:'Start frozen snapshot',exact:true})).toBeEnabled({timeout:30000});
  await page.getByRole('button',{name:'Start frozen snapshot',exact:true}).click();
  await expect.poll(() => page.evaluate(() => localStorage.getItem('studio.lastRun')), {timeout:30000}).toBeTruthy();
  runId = await page.evaluate(() => localStorage.getItem('studio.lastRun'));
  await context.storageState({path:path.join(data,'browser-session.private.json')});
  chmodSync(path.join(data,'browser-session.private.json'),0o600);
  } else {
    runId=process.env.STUDIO_RESUME_RUN;
  }
  report.runId=runId;
  writeFileSync(path.join(data,'browser-run.private.json'),JSON.stringify({runId}),{mode:0o600});
  console.log('ACTUAL_BROWSER_START',runId);
  let previous;
  await expect.poll(async () => {
    const run=await getRun();
    const state=JSON.stringify([run.state,run.runtimeStatus?.phase,run.reason]);
    if (state!==previous) {console.log('OBSERVED',state);previous=state;}
    assert(!['failed','stopped'].includes(run.state),`Start ended ${state}`);
    return run.state;
  }, {timeout:900000,intervals:[1000]}).toBe('running');
  await expect(page.getByRole('heading',{name:'Vehicle Manual Control',exact:true})).toBeVisible();
  // The helper verifies the exact owned Pygame process/window before every key.
  const driven = await promisify(execFile)(python,['-I','scripts/verify_platform_keyboard.py','--data-dir',data,'--run-id',runId],{timeout:90000});
  console.log(driven.stdout.trim());
  report.driving=JSON.parse(readFileSync(path.join(data,'keyboard-verification.json'),'utf8'));
  assert.equal(report.driving.outcome,'passed');
  const panel=page.getByRole('region',{name:'Linked platform views',exact:true});
  await page.getByRole('tab',{name:'Communications',exact:true}).click();
  await expect(panel.getByRole('heading',{name:'Communications · X-Verse platform',exact:true})).toBeVisible();
  await expect(panel.getByRole('button',{name:'Correlated orchestration',exact:true}).first()).toBeVisible();
  await panel.getByRole('button',{name:'Correlated orchestration',exact:true}).first().click();
  await expect(panel.getByRole('heading',{name:'Orchestration · X-Verse platform',exact:true})).toBeFocused();
  await expect(panel.getByText('Selected links:',{exact:false})).toBeVisible();
  await panel.getByRole('button',{name:'Clear platform selection',exact:true}).click();
  await expect(panel.getByRole('button',{name:'Next platform page',exact:true})).toBeEnabled();
  await panel.getByRole('button',{name:'Next platform page',exact:true}).click();
  await expect(panel.getByText(/^51–/)).toBeVisible();
  // Changing outer tabs must discard another view's cursor, keeping the capture.
  await page.getByRole('tab',{name:'Communications',exact:true}).click();
  const cause=panel.getByRole('button',{name:'Original cause',exact:true}).first();
  await expect(cause).toBeVisible();
  await cause.focus(); await page.keyboard.press('Enter');
  await expect(panel.getByRole('heading',{name:'Evidence · X-Verse platform',exact:true})).toBeFocused();
  await expect(panel.getByText('Native ingress fact',{exact:true})).toBeVisible();
  assert.equal(new Set(report.responses.map(r=>r.snapshotId)).size,1);
  assert.equal(new Set(report.responses.map(r=>r.sourceWitness)).size,1);
  assert(report.responses.every(r=>r.runId===runId));
  report.sharedSnapshotVerified=true;
  await page.screenshot({path:path.join(data,'linked-evidence.png'),fullPage:true});
  await page.getByRole('region',{name:'Run controls',exact:true}).getByRole('button',{name:'Stop',exact:true}).click();
  await expect.poll(async()=> (await getRun()).state,{timeout:120000,intervals:[1000]}).toBe('stopped');
  const terminal = await getRun();
  assert.equal(terminal.cleanup,'complete');
  report.terminal={state:terminal.state,cleanup:terminal.cleanup,evidence:terminal.evidence};
  const previousSnapshot=report.responses.at(-1).snapshotId;
  await panel.getByRole('button',{name:'Refresh all platform views',exact:true}).click();
  await expect.poll(()=>report.responses.at(-1)?.snapshotId,{timeout:15000}).not.toBe(previousSnapshot);
  await expect(panel.getByRole('button',{name:'Clear platform selection',exact:true})).toBeVisible();
  await panel.getByRole('button',{name:'Clear platform selection',exact:true}).click();
  await page.getByRole('tab',{name:'Orchestration',exact:true}).click();
  await expect(panel.getByRole('table')).toBeVisible();
  assert.equal(report.errors.length,0,report.errors.join('\n'));
  report.outcome='passed';completed=true;
  console.log('ACTUAL_BROWSER_LINKED_VIEWS_AND_STOP_PASS',runId);
} catch(error) {
  report.failure=error.message;
  console.log('BROWSER_FAILURE',error.message);
  await page.screenshot({path:path.join(data,'browser-failure.png'),fullPage:true}).catch(()=>{});
  process.exitCode=1;
} finally {
  if(runId && !completed) {
    const run=await getRun().catch(()=>null);
    if(run && ['running','preparing','ready','unknown'].includes(run.state)) {
      await page.evaluate(async ({runId,version})=> {
        const session=await fetch('/api/v1/session').then(r=>r.json());
        await fetch(`/api/v1/runs/${runId}/commands`,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrfToken,'Idempotency-Key':'explicit-browser-check-cleanup'},body:JSON.stringify({kind:'stop',expectedStateVersion:version})});
      },{runId,version:run.stateVersion});
    }
  }
  writeFileSync(path.join(data,'browser-verification.json'),JSON.stringify(report,null,2)+'\n',{mode:0o600});
  await context.storageState({path:path.join(data,'browser-session.private.json')});
  chmodSync(path.join(data,'browser-session.private.json'),0o600);
  await browser.close();
}
