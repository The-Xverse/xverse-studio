import { test, expect, type Locator, type Page, type TestInfo } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";
import { renderedContrast } from "../e2e/contrast";

const fixture = () => JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "fresh-campaign-keyboard.private.json"), "utf8"));
const planning = (page: Page) => page.getByRole("region", { name: "Campaign planning", exact: true });
const selected = (page: Page) => page.getByRole("region", { name: "Selected campaign", exact: true });
const selectedHeading = (page: Page) => selected(page).getByRole("heading", { name: "Selected campaign", exact: true });
async function tabTo(page: Page, control: Locator) {
  await expect(control).toBeVisible();
  for (let i = 0; i < 600; i++) {
    if (await control.evaluate(n => n === document.activeElement)) {
      const observation = await control.evaluate(n => {
        const r = n.getBoundingClientRect(), s = getComputedStyle(n);
        return { name: n.getAttribute("aria-label") || n.closest("label")?.textContent || n.textContent, rect: { left: r.left, right: r.right, top: r.top, bottom: r.bottom }, viewport: { width: innerWidth, height: innerHeight }, outlineStyle: s.outlineStyle, outlineWidth: s.outlineWidth,
          visible: s.outlineStyle !== "none" && parseFloat(s.outlineWidth) > 0 && r.left >= 0 && r.top >= 0 && r.right <= innerWidth + 1 && r.bottom <= innerHeight + 1 };
      });
      expect(observation, "Native focused control geometry and visible outline").toMatchObject({ visible: true });
      return;
    }
    await page.keyboard.press("Tab");
  }
  throw Error("Fresh campaign control is unreachable through native Tab order");
}
async function activate(page: Page, control: Locator) { await tabTo(page, control); await page.keyboard.press("Enter"); }
async function enter(page: Page, control: Locator, value: string) {
  await tabTo(page, control); await page.keyboard.press("ControlOrMeta+A"); await page.keyboard.insertText(value); await page.keyboard.press("Tab"); await expect(control).toHaveValue(value);
}
async function get(page: Page, route: string) { const r = await page.request.get("/api/v1" + route); expect(r.status()).toBe(200); return r.json(); }
async function open(page: Page, info: TestInfo, width: number) {
  await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 }); await connectStudio(page, info);
  const source = fixture()[String(width)];
  await page.evaluate(id => { localStorage.setItem("studio.projectId", id); }, source.projectId); await page.reload();
  const preflightResponse = page.waitForResponse(r => /\/api\/v1\/projects\/[^/]+\/preflights$/.test(new URL(r.url()).pathname) && r.request().method() === "POST");
  await activate(page, page.getByRole("button", { name: "Preflight & run", exact: true }));
  const preflight = await preflightResponse; expect(preflight.status()).toBe(200); expect((await preflight.json()).status).toBe("ready");
  await expect(page.getByRole("button", { name: "Start frozen snapshot", exact: true })).toBeEnabled();
  await activate(page, page.getByRole("button", { name: "Back to draft", exact: true }));
  await activate(page, page.getByRole("tab", { name: "Experiments", exact: true }));
  await activate(page, page.getByRole("tab", { name: "Campaigns", exact: true }));
  await activate(page, planning(page).getByRole("button", { name: "Use admitted parameter example", exact: true }));
  await expect(planning(page).getByLabel("Parameter matrix (JSON)")).toHaveValue(/durationSeconds/);
  return source;
}
async function configure(page: Page, values: number[], seconds: number) {
  await enter(page, planning(page).getByLabel("Parameter matrix (JSON)"), JSON.stringify({ durationSeconds: values }));
  await enter(page, planning(page).getByLabel("Maximum runs", { exact: true }), String(values.length));
  await enter(page, planning(page).getByLabel("Maximum total declared seconds", { exact: true }), String(seconds));
}
async function preview(page: Page) {
  const response = page.waitForResponse(r => new URL(r.url()).pathname === "/api/v1/campaigns/preview" && r.request().method() === "POST");
  await activate(page, planning(page).getByRole("button", { name: "Preview campaign", exact: true }));
  const r = await response; expect(r.status()).toBe(200); const value = await r.json();
  await expect(planning(page).getByRole("heading", { name: "Authoritative campaign preview", exact: true })).toBeFocused(); return value;
}
async function report(page: Page, info: TestInfo, width: number, facts: any) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await info.attach("fresh-campaign-keyboard", { body: JSON.stringify({ width, ...facts, browser: page.context().browser()?.version(), scope: "Actual admitted Autoverse campaign UI. Only explicitly named live case starts a complete renderer/sensors/Android child; no physical effects or AT certification." }), contentType: "application/json" });
}
async function diagnostic(page: Page, code: string) {
  const alert = page.getByRole("alert").filter({ hasText: code }); await expect(alert).toBeFocused();
  const contrast = await renderedContrast(alert, "Campaign diagnostic"); expect(contrast.supported).toBe(true);
  if (contrast.supported) expect(contrast.ratio).toBeGreaterThanOrEqual(4.5);
}

for (const width of [1024, 1440]) {
  test(`fresh campaign preview bounds and explicit transport retry at ${width}`, async ({ page }, info) => {
    await open(page, info, width);
    await enter(page, planning(page).getByLabel("Parameter matrix (JSON)"), "{");
    await expect(planning(page).getByRole("button", { name: "Preview campaign", exact: true })).toBeDisabled();
    await expect(planning(page).getByRole("status")).toContainText(/JSON|property|position|Expected/i);
    await configure(page, [30, 31], 30);
    const rejected = page.waitForResponse(r => new URL(r.url()).pathname === "/api/v1/campaigns/preview" && r.request().method() === "POST");
    await activate(page, planning(page).getByRole("button", { name: "Preview campaign", exact: true }));
    const refusal = await rejected; expect(refusal.status()).toBe(422); const refusalBody = await refusal.json(); await diagnostic(page, refusalBody.code);
    await expect(planning(page).getByRole("button", { name: "Create campaign", exact: true })).toBeDisabled();
    await configure(page, [30, 31], 62);
    await page.route("**/api/v1/campaigns/preview", route => route.fulfill({ status: 503, json: { code: "CAMPAIGN_PREVIEW_FIXTURE", message: "Labelled transport refusal", retryable: true } }), { times: 1 });
    await activate(page, planning(page).getByRole("button", { name: "Preview campaign", exact: true })); await diagnostic(page, "CAMPAIGN_PREVIEW_FIXTURE");
    const value = await preview(page); expect(value.cardinality).toBe(2); expect(value.estimatedTotalSeconds).toBe(61);
    await expect(page.getByRole("alert")).toHaveCount(0); await expect(planning(page).getByRole("button", { name: "Create campaign", exact: true })).toBeEnabled();
    await report(page, info, width, { realBudgetRefusal: refusalBody.code, cardinality: value.cardinality, createdCampaigns: 0, fixture: "One labelled503; actual backend budget refusal and unchanged retry" });
  });
  for (const intent of ["Home", "focus", "source dialog"] as const) {
    test(`held fresh campaign preview preserves newer ${intent} at ${width}`, async ({ page }, info) => {
      await open(page, info, width); await configure(page, [30], 30);
      let release!: () => void, ready = false; const gate = new Promise<void>(r => release = r);
      await page.route("**/api/v1/campaigns/preview", async route => { const response = await route.fetch(); expect(response.status()).toBe(200); ready = true; await gate; await route.fulfill({ response }); }, { times: 1 });
      try {
        await activate(page, planning(page).getByRole("button", { name: "Preview campaign", exact: true })); await expect.poll(() => ready).toBe(true);
        const home = page.getByRole("button", { name: "X-Verse Studio home", exact: true });
        if (intent === "Home") await activate(page, home);
        else if (intent === "focus") await tabTo(page, home);
        else { await activate(page, page.getByRole("button", { name: "Edit scenario XDL", exact: true })); await expect(page.getByRole("dialog").getByRole("textbox", { name: "XDL source", exact: true })).toBeFocused(); }
        release(); await page.unrouteAll({ behavior: "wait" }); await page.waitForLoadState("networkidle");
        if (intent === "Home") await expect(page.getByRole("heading", { name: "Start with an example", exact: true })).toBeVisible();
        else if (intent === "focus") await expect(home).toBeFocused();
        else await expect(page.getByRole("dialog").getByRole("textbox", { name: "XDL source", exact: true })).toBeFocused();
        await report(page, info, width, { intent, createdCampaigns: 0, fixture: "Actual side-effect-free preview response held; identity and payload unchanged" });
      } finally { release(); await page.unrouteAll({ behavior: "wait" }); }
    });
  }

  test(`live fresh campaign native creation retry child inputs and cancellation at ${width}`, async ({ page }, info) => {
    test.setTimeout(720000);
    const source = await open(page, info, width); await configure(page, [60, 61], 122); const frozen = await preview(page);
    const create = planning(page).getByRole("button", { name: "Create campaign", exact: true });
    const submissions: any[] = []; let firstAccepted: any;
    await page.route("**/api/v1/campaigns", async route => {
      if (route.request().method() !== "POST") { await route.continue(); return; }
      submissions.push({ key: route.request().headers()["idempotency-key"], body: route.request().postDataJSON() });
      if (width === 1440) { const r = await route.fetch(); expect(r.status()).toBe(202); firstAccepted = await r.json(); }
      await route.fulfill({ status: 503, json: { code: "CAMPAIGN_CREATE_FIXTURE", message: "Labelled refusal before or after actual acceptance", retryable: true } });
    }, { times: 1 });
    await activate(page, create); await diagnostic(page, "CAMPAIGN_CREATE_FIXTURE");
    const receiptResponse = page.waitForResponse(r => new URL(r.url()).pathname === "/api/v1/campaigns" && r.request().method() === "POST");
    await activate(page, create); const acceptedResponse = await receiptResponse; expect(acceptedResponse.status()).toBe(202);
    const accepted = await acceptedResponse.json(); const request = acceptedResponse.request();
    expect(request.headers()["idempotency-key"]).toBe(submissions[0].key); expect(request.postDataJSON()).toEqual(submissions[0].body);
    if (firstAccepted) expect(accepted).toEqual(firstAccepted);
    await expect(selectedHeading(page)).toBeFocused(); await expect(page.getByRole("alert")).toHaveCount(0);
    let campaign: any, run: any, child: any;
    await expect.poll(async () => {
      campaign = await get(page, `/campaigns/${accepted.campaignId}`); child = campaign.children.find((c: any) => c.runId);
      if (!child) return "awaiting child";
      run = await get(page, `/runs/${child.runId}`);
      if (["failed", "stopped", "unknown"].includes(run.state)) throw Error(`Complete child did not reach running: ${run.state}; ${JSON.stringify(run.diagnostics)}`);
      return run.state;
    }, { timeout: 540000, intervals: [1000] }).toBe("running");
    expect(run.runtimeStatus.components.android).toBe("booted_apk_started"); expect(run.inputTelemetry.items.speed.status).toBe("observed");
    const session = await get(page, "/session"), headers = { "X-CSRF-Token": session.csrfToken, Origin: new URL(page.url()).origin };
    const acquired = await page.request.post(`/api/v1/runs/${run.runId}/input/acquire`, { headers, data: {} }); expect(acquired.status()).toBe(200); const lease = await acquired.json();
    let speed = 0, sequence = 0;
    for (let i = 0; i < 200 && speed <= .1; i++) {
      const frame = await page.request.post(`/api/v1/runs/${run.runId}/input/frame`, { headers, data: { leaseToken: lease.leaseToken, generation: lease.generation, frame: { sequence: ++sequence, throttle: .5, brake: 0, steer: 0 } } }); expect(frame.status()).toBe(200);
      run = await get(page, `/runs/${run.runId}`); const item = run.inputTelemetry.items.speed; if (item.status === "observed" && typeof item.value === "number") speed = item.value;
      await page.waitForTimeout(100);
    }
    expect(speed).toBeGreaterThan(.1);
    const brake = await page.request.post(`/api/v1/runs/${run.runId}/input/frame`, { headers, data: { leaseToken: lease.leaseToken, generation: lease.generation, frame: { sequence: ++sequence, throttle: 0, brake: 1, steer: 0 } } }); expect(brake.status()).toBe(200);
    await activate(page, selected(page).getByRole("button", { name: `Inspect child inputs ${run.runId}`, exact: true }));
    await expect(selected(page).getByRole("heading", { name: "Verified child inputs", exact: true })).toBeFocused();
    const input = await get(page, `/runs/${run.runId}/snapshot`); expect(input.integrity).toBe("valid"); expect(input.snapshot.parentSnapshotId).toBe(frozen.baseSnapshotId); expect(input.snapshot.campaignId).toBe(accepted.campaignId); expect(input.snapshot.configuration.durationSeconds).toBe(60);
    const stop = selected(page).getByRole("button", { name: "Stop scheduling", exact: true });
    const cancelResponse = page.waitForResponse(r => new URL(r.url()).pathname === `/api/v1/campaigns/${accepted.campaignId}/cancel` && r.request().method() === "POST");
    await activate(page, stop); const cancel = await cancelResponse; expect(cancel.status()).toBe(202); const cancelReceipt = await cancel.json(); expect(cancelReceipt.operationStatus).toBe("completed");
    await expect(selectedHeading(page)).toBeFocused();
    await expect.poll(async () => { campaign = await get(page, `/campaigns/${accepted.campaignId}`); return campaign.status; }, { timeout: 120000, intervals: [500] }).toBe("cancelled");
    expect(campaign.children.map((c: any) => c.state)).toEqual(["stopped", "cancelled"]);
    run = await get(page, `/runs/${run.runId}`); expect(run.state).toBe("stopped"); expect(run.cleanup).toBe("complete");
    const listed = await get(page, `/runs?projectId=${source.projectId}`); expect(listed.items).toHaveLength(1);
    const sameInputs = await get(page, `/runs/${run.runId}/snapshot`); expect(sameInputs).toEqual(input);
    await report(page, info, width, { campaignId: accepted.campaignId, runId: run.runId, baseSnapshotId: frozen.baseSnapshotId, childSnapshotId: run.snapshotId, sameRequestAndKey: true, createdCampaigns: 1, createdChildren: 1, fullAndroidAndVehicleSpeedObserved: true, speed, simulatedInputFrames: sequence, childStates: campaign.children.map((c: any) => c.state), cleanup: run.cleanup, fixture: `One create503 ${width === 1440 ? "after actual acceptance" : "before acceptance"}; simulated input is an explicitly approved owned backend observation probe` });
  });
}
