import { test, expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
import { renderedContrast } from "../e2e/contrast";

const recording = () => JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "playback-recording.private.json"), "utf8"));
const panel = (page: Page) => page.getByRole("region", { name: "Frozen assertions and metrics", exact: true });
const heading = (page: Page) => panel(page).getByRole("heading", { name: "Frozen assertions and metrics", exact: true });
const evaluate = (page: Page) => panel(page).getByRole("button", { name: "Evaluate assertion", exact: true });
const select = (page: Page) => panel(page).getByRole("combobox", { name: "Snapshot definition reference", exact: true });
const endpoint = () => `/api/v1/runs/${recording().runId}/evaluations`;
async function tabTo(page: Page, control: Locator) {
  await expect(control).toBeVisible();
  for (let i=0; i<600; i++) {
    if (await control.evaluate(n => n === document.activeElement)) {
      expect(await control.evaluate(n => { const r=n.getBoundingClientRect(), s=getComputedStyle(n);
        return s.outlineStyle !== "none" && parseFloat(s.outlineWidth)>0 && r.left>=0 && r.top>=0 && r.right<=innerWidth+1 && r.bottom<=innerHeight+1;
      })).toBe(true); return;
    }
    await page.keyboard.press("Tab");
  }
  throw Error("Evaluation control is unreachable through native Tab order");
}
async function activate(page: Page, control: Locator) { await tabTo(page,control); await page.keyboard.press("Enter"); }
async function choose(page: Page, value: string) {
  const control=select(page); await expect(control).toBeEnabled();
  await expect.poll(() => control.locator("option").evaluateAll(nodes => nodes.map(n => (n as HTMLOptionElement).value))).toContain(value);
  const options=await control.locator("option").evaluateAll(nodes => nodes.map(n => (n as HTMLOptionElement).value));
  await tabTo(page,control); await page.keyboard.press("Home");
  for(let i=0;i<options.indexOf(value);i++) await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Tab"); await expect(control).toHaveValue(value); await expect(evaluate(page)).toBeEnabled();
}
async function get(page: Page, route: string) { const r=await page.request.get("/api/v1"+route); expect(r.status()).toBe(200); return r.json(); }
async function open(page: Page, info: TestInfo, width: number) {
  await page.setViewportSize({width,height:width===1024?768:900}); await connectStudio(page,info);
  const source=recording();
  await page.evaluate(r => { localStorage.setItem("studio.projectId",r.projectId); localStorage.setItem("studio.lastRun",r.runId); localStorage.setItem("studio.lastRun."+r.projectId,r.runId); },source);
  await page.reload();
  await activate(page,page.getByRole("tab",{name:"Experiments",exact:true}));
  await activate(page,page.getByRole("tab",{name:"Assertions",exact:true}));
  await expect(select(page)).toBeEnabled();
  await expect(panel(page)).not.toContainText("EVALUATION_EVIDENCE_UNSUPPORTED");
  const support=await get(page,`/runs/${source.runId}/assessment-support`); expect(support.status).toBe("supported");
  return source;
}
async function submit(page: Page) {
  const reply=page.waitForResponse(r => new URL(r.url()).pathname===endpoint() && r.request().method()==="POST");
  await activate(page,evaluate(page)); const response=await reply; expect(response.status()).toBe(202); return response.json();
}
const signature=(row:any) => Object.fromEntries(["definitionRef","definitionDigest","status","verdict","value","unit","coverage","partial"].map(k=>[k,row[k]]));
async function result(page: Page, receipt:any, source:any) {
  const row=await get(page,`/evaluations/${receipt.evaluationId}`);
  expect(row.runId).toBe(source.runId); expect(row.snapshotId).toBe(source.snapshotId);
  expect(row.operationId).toBe(receipt.operationId); expect(row.evidenceMapping.status).toBe("supported");
  const historical=source.historicalEvaluations.find((r:any)=>r.definitionRef===row.definitionRef);
  expect(signature(row)).toEqual(signature(historical));
  const card=panel(page).locator("article.evaluation-card").filter({has:page.getByText(row.evaluationId,{exact:true})});
  await expect(card).toBeVisible(); await expect(card).toContainText(row.status);
  return row;
}
async function report(page:Page,info:TestInfo,width:number,details:any) {
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  await info.attach("actual-evaluation-keyboard",{body:JSON.stringify({width,...details,browser:page.context().browser()?.version(),
    scope:"Fresh actual installed Autoverse mapping; new derived evaluation of original frozen evidence only. No model/guest/provider operation or AT certification.",
  }),contentType:"application/json"});
}
async function error(page:Page,code:string) {
  const alert=page.getByRole("alert").filter({hasText:code}); await expect(alert).toBeVisible();
  const contrast=await renderedContrast(alert,"Evaluation submission diagnostic"); expect(contrast.supported).toBe(true);
  if(contrast.supported) expect(contrast.ratio).toBeGreaterThanOrEqual(4.5);
  await expect(evaluate(page)).toBeEnabled(); return contrast;
}

for(const width of [1024,1440]) {
  test(`all six frozen outcomes submit through native evaluation keys at ${width}`,async({page},info)=>{
    const source=await open(page,info,width), rows=[];
    for(const historical of source.historicalEvaluations) {
      await choose(page,historical.definitionRef); const receipt=await submit(page); rows.push(await result(page,receipt,source));
      await expect(heading(page)).toBeFocused();
    }
    await report(page,info,width,{rows:rows.map(signature),allSixOutcomeKindsPreserved:true});
  });
  for(const mode of ["before acceptance","after acceptance"] as const) {
    test(`evaluation native retry preserves identity ${mode} at ${width}`,async({page},info)=>{
      const source=await open(page,info,width), keys:string[]=[], bodies:any[]=[]; let accepted:any;
      await choose(page,source.historicalEvaluations[0].definitionRef);
      await page.route("**"+endpoint(),async route=>{
        keys.push(route.request().headers()["idempotency-key"]); bodies.push(route.request().postDataJSON());
        if(mode==="after acceptance") {const response=await route.fetch(); expect(response.status()).toBe(202); accepted=await response.json();}
        await route.fulfill({status:503,json:{code:"EVALUATION_KEYBOARD_FIXTURE",message:`Labelled response refusal ${mode}`,retryable:true}});
      },{times:1});
      const listener=(r:import("@playwright/test").Request)=>{if(new URL(r.url()).pathname===endpoint()&&r.method()==="POST"&&keys.length===1){keys.push(r.headers()["idempotency-key"]);bodies.push(r.postDataJSON());}};
      await activate(page,evaluate(page)); const contrast=await error(page,"EVALUATION_KEYBOARD_FIXTURE");
      page.on("request",listener); const receipt=await submit(page); page.off("request",listener);
      expect(keys).toHaveLength(2); expect(keys[1]).toBe(keys[0]); expect(bodies[1]).toEqual(bodies[0]);
      if(accepted) expect(receipt).toEqual(accepted);
      const row=await result(page,receipt,source); await expect(heading(page)).toBeFocused();
      await report(page,info,width,{mode,keys,bodies,row:signature(row),contrast,fixture:"One labelled503; accepted-response case first executes actual native POST"});
    });
  }
  for(const intent of ["Home","focus","source dialog"] as const) {
    test(`held actual evaluation preserves newer ${intent} at ${width}`,async({page},info)=>{
      const source=await open(page,info,width); await choose(page,source.historicalEvaluations[0].definitionRef);
      let release!:()=>void,ready=false,receipt:any; const gate=new Promise<void>(r=>release=r);
      await page.route("**"+endpoint(),async route=>{const response=await route.fetch();expect(response.status()).toBe(202);receipt=await response.json();ready=true;await gate;await route.fulfill({response});},{times:1});
      try {
        await activate(page,evaluate(page)); await expect.poll(()=>ready).toBe(true);
        const home=page.getByRole("button",{name:"X-Verse Studio home",exact:true});
        if(intent==="Home") await activate(page,home);
        else if(intent==="focus") await tabTo(page,home);
        else {
          await activate(page,page.getByRole("button",{name:"Edit scenario XDL",exact:true}));
          await expect(page.getByRole("dialog").getByRole("textbox",{name:"XDL source",exact:true})).toBeFocused();
        }
        release();await page.unrouteAll({behavior:"wait"}); await page.waitForLoadState("networkidle");
        if(intent==="Home") await expect(page.getByRole("heading",{name:"Start with an example",exact:true})).toBeVisible();
        else if(intent==="focus") {await result(page,receipt,source);await expect(home).toBeFocused();}
        else {await result(page,receipt,source);await expect(page.getByRole("dialog").getByRole("textbox",{name:"XDL source",exact:true})).toBeFocused();}
        const row=await get(page,`/evaluations/${receipt.evaluationId}`);expect(row.snapshotId).toBe(source.snapshotId);
        await report(page,info,width,{intent,receipt,newDerivedResultOnly:true});
      } finally {release();await page.unrouteAll({behavior:"wait"});}
    });
  }
  test(`actual frozen digest refusal and native evaluation recovery at ${width}`,async({page},info)=>{
    const source=await open(page,info,width);await choose(page,source.historicalEvaluations[0].definitionRef);
    await page.route("**"+endpoint(),route=>route.continue({postData:JSON.stringify({...route.request().postDataJSON(),definitionDigest:"sha256:"+"0".repeat(64)})}),{times:1});
    const refused=page.waitForResponse(r=>new URL(r.url()).pathname===endpoint()&&r.request().method()==="POST");
    await activate(page,evaluate(page));expect((await refused).status()).toBe(422);
    const contrast=await error(page,"DEFINITION_DIGEST_MISMATCH");
    const receipt=await submit(page);const row=await result(page,receipt,source);await expect(heading(page)).toBeFocused();
    await report(page,info,width,{actualBackendRefusal:true,receipt,row:signature(row),contrast,fixture:"One explicitly labelled outbound digest corruption; backend refuses before acceptance"});
  });
}
