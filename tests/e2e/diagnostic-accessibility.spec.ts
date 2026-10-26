import { test, expect, type Locator, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { connectStudio } from "./connect-studio";
import { renderedContrast } from "./contrast";

async function focusByTab(page: Page, target: Locator, reverse = false) {
  await expect(target).toBeVisible();
  for (let i = 0; i < (reverse ? 32 : 200); i++) {
    if (await target.evaluate((node) => node === document.activeElement)) return;
    await page.keyboard.press(reverse ? "Shift+Tab" : "Tab");
  }
  throw Error("Required diagnostic action is unreachable through native Tab order");
}
async function activate(page: Page, target: Locator, reverse = false) {
  await focusByTab(page, target, reverse);
  await expect(target).toBeFocused();
  await page.keyboard.press("Enter");
}
async function createFixtureProject(page: Page, name: string) {
  const project = await page.evaluate(async (name) => {
    const session = await fetch("/api/v1/session").then((r) => r.json());
    const response = await fetch("/api/v1/projects", { method: "POST", headers: {
      "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken,
    }, body: JSON.stringify({ name }) });
    if (!response.ok) throw Error("Owned test project setup failed");
    const project = await response.json();
    localStorage.setItem("studio.projectId", project.projectId);
    return project;
  }, name);
  await page.reload();
  await expect(page.locator(".project-header h1")).toHaveText(name);
  return project;
}
async function chooseResource(page: Page, id: string) {
  const resource = page.getByLabel("Resource", { exact: true });
  await focusByTab(page, resource);
  await page.keyboard.press("Home");
  for (let i = 0; i < 64 && await resource.inputValue() !== id; i++) await page.keyboard.press("ArrowDown");
  await expect(resource).toHaveValue(id);
}

test.afterEach(async ({ page }, testInfo) => {
  await testInfo.attach("native-browser-environment.json", {
    body: JSON.stringify({ platform: process.platform, architecture: process.arch,
      browser: await page.context().browser()?.version(), viewport: page.viewportSize(),
      scope: "Owned native browser wrapper; external/physical integrations not established" }),
    contentType: "application/json",
  });
});

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test(`diagnostic accessibility: real invalid-source keyboard recovery at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
    test.setTimeout(120000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    const project = await createFixtureProject(page, `Keyboard diagnostic recovery ${viewport.width}`);
    const documentId = Object.keys(project.documents)[0], original = project.documents[documentId].content;
    const measurements: Awaited<ReturnType<typeof renderedContrast>>[] = [];
    try {
      await activate(page, page.getByRole("button", { name: "XDL source", exact: true }));
      await chooseResource(page, documentId);
      const source = page.getByLabel("XDL source", { exact: true });
      await focusByTab(page, source);
      await page.keyboard.press("ControlOrMeta+A");
      await page.keyboard.insertText("invalid: [");
      await activate(page, page.getByRole("button", { name: "Save source revision", exact: true }));
      await expect(page.locator(".alerts[aria-live=polite]")).toContainText("Source revision saved");
      await page.keyboard.press("Escape");
      await activate(page, page.getByRole("button", { name: "Preflight & run", exact: true }));
      const explanation = page.getByRole("region", { name: "Readiness explanation" });
      await expect(explanation).toHaveAttribute("data-explanation-state", "loaded");
      const invalid = explanation.locator('[data-diagnostic-class="invalid_model"]');
      await expect(invalid).toContainText("Start is blocked");
      await expect(invalid).toContainText("authoritative validator");
      await expect(page.getByRole("button", { name: "Start frozen snapshot", exact: true })).toBeDisabled();
      measurements.push(await renderedContrast(invalid.locator("h4"), "Invalid-model finding title"));
      measurements.push(await renderedContrast(invalid.locator(".diagnostic-evidence li").first(), "Authoritative error/source evidence"));
      measurements.push(await renderedContrast(invalid.locator(".badge").first(), "Error severity text"));
      // Explicit source navigation remains available even if a next action is explanatory text.
      await page.keyboard.press("Escape");
      await expect(page.getByRole("button", { name: "Preflight & run", exact: true })).toBeFocused();
      await activate(page, page.getByRole("button", { name: "XDL source", exact: true }));
      await chooseResource(page, documentId);
      await expect(source).toHaveValue("invalid: [");
      await focusByTab(page, source);
      await page.keyboard.press("ControlOrMeta+A");
      await page.keyboard.insertText(original);
      await activate(page, page.getByRole("button", { name: "Save source revision", exact: true }));
      await expect(page.locator(".alerts[aria-live=polite]")).toContainText("Source revision saved");
      await page.keyboard.press("Escape");
      await activate(page, page.getByRole("button", { name: "Validate", exact: true }));
      await expect(page.locator(".alerts[aria-live=polite]")).toContainText("Authoritative platform validation passed");
      measurements.push(await renderedContrast(page.locator(".alerts .notice").first(), "Dynamic successful recovery status"));
      measurements.push(await renderedContrast(page.getByRole("button", { name: "Preflight & run", exact: true }), "Enabled primary execution button"));
      const result = await page.evaluate(async (id) => fetch("/api/v1/projects/" + id).then((r) => r.json()), project.projectId);
      expect(result.documents[documentId].content).toBe(original);
      expect(result.revision).toBe(project.revision + 2);
    } finally {
      await testInfo.attach("rendered-contrast.json", { body: JSON.stringify({ viewport, measurements, scope: "Native browser text contrast and keyboard source recovery; no assistive-technology or live-provider claim" }, null, 2), contentType: "application/json" });
    }
    for (const pair of measurements) {
      expect.soft(pair.supported, `${pair.label}: unsupported paint cannot pass`).toBe(true);
      if (pair.supported) expect.soft(pair.ratio, `${pair.label}: ${pair.color}, ratio ${pair.ratio}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  test(`diagnostic accessibility: recorded and labeled transport outcomes at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
    test.setTimeout(120000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    const project = await createFixtureProject(page, `Diagnostic presentation fixture ${viewport.width}`);
    const python = path.resolve(".venv/bin/python");
    const fixture = JSON.parse(execFileSync(python, ["-I", "tests/fixtures/evidence/create_recorded_evidence.py", "--data-dir", process.env.STUDIO_BROWSER_DATA!, "--project-id", project.projectId], { encoding: "utf8", timeout: 30000 }));
    const diagnosticUrl = `/api/v1/runs/${fixture.runId}/diagnostics`;
    // Transport-only outcome fixture: production explanation logic over synthetic state,
    // no mutation of the immutable journal, no claim that cleanup/ownership failed live.
    const synthetic = JSON.parse(execFileSync(python, ["-I", "-c", "import json,sys; from xverse_studio.diagnostics import explain_run; v=json.load(sys.stdin); print(json.dumps(explain_run({'runId':v['runId'],'state':'unknown','reason':'OWNERSHIP_UNKNOWN','cleanup':'failed','evidence':'unavailable'}, [], 'unavailable', element_refs=[v['systemRef']+'#plant'])))"], { input: JSON.stringify({ runId: fixture.runId, systemRef: "xdl://org.xverse.studio.process-control/system/reference-loop" }), encoding: "utf8", timeout: 30000 }));
    let transportFixture = false;
    await page.route("**" + diagnosticUrl, (route) => transportFixture ? route.fulfill({ json: synthetic }) : route.continue());
    await page.evaluate(({ projectId, runId }) => {
      localStorage.setItem("studio.projectId", projectId);
      localStorage.setItem("studio.lastRun." + projectId, runId);
      localStorage.setItem("studio.lastRun", runId);
    }, fixture);
    await page.reload();
    const measurements: Awaited<ReturnType<typeof renderedContrast>>[] = [];
    const writes: string[] = [];
    page.on("request", (r) => { if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method())) writes.push(r.method() + " " + new URL(r.url()).pathname); });
    try {
      await activate(page, page.getByRole("tab", { name: "Results", exact: false }));
      await activate(page, page.getByRole("tab", { name: "Diagnosis", exact: true }));
      const panel = page.getByRole("region", { name: "Run diagnosis" });
      await expect(panel).toHaveAttribute("data-explanation-state", "loaded");
      const clock = panel.locator('[data-diagnostic-class="incompatible_time_mapping"]');
      await expect(clock).toContainText("2 clock domains");
      await expect(panel.locator('[data-diagnostic-class="unavailable_evidence"]')).toContainText("EVIDENCE_PARTIAL");
      measurements.push(await renderedContrast(clock.locator("h4"), "Clock-diagnostic title"));
      measurements.push(await renderedContrast(clock.locator("h5").first(), "Observed-facts heading"));
      measurements.push(await renderedContrast(clock.locator(".diagnostic-evidence li").first(), "Retained diagnostic evidence text"));
      const inspect = panel.locator('[data-diagnostic-class="telemetry_gap"]').getByRole("button", { name: "Inspect the referenced retained events and logs.", exact: true });
      measurements.push(await renderedContrast(inspect, "Diagnostic next-action button"));
      await activate(page, inspect);
      await expect(page.getByRole("tab", { name: /Events & logs/ })).toHaveAttribute("aria-selected", "true");
      await testInfo.attach("focus-after-inspect.json", {
        body: JSON.stringify(await page.evaluate(() => {
          const node = document.activeElement;
          return { tag: node?.tagName, role: node?.getAttribute("role"), label: node?.getAttribute("aria-label"), text: node?.textContent?.trim().slice(0, 160), html: node?.outerHTML.slice(0, 300) };
        }), null, 2), contentType: "application/json",
      });
      await expect(page.getByRole("tab", { name: /Events & logs/ })).toBeFocused();
      transportFixture = true;
      await activate(page, page.getByRole("tab", { name: "Diagnosis", exact: true }));
      await expect(panel.locator('[data-diagnostic-class="failed_cleanup"]')).toContainText("CLEANUP_FAILED");
      const lost = panel.locator('[data-diagnostic-class="lost_connection"]');
      await expect(lost).toContainText("OWNERSHIP_UNKNOWN");
      await expect(lost).toContainText("Hypotheses · unconfirmed");
      await expect(panel.locator('[data-diagnostic-class="unavailable_evidence"]')).toContainText("EVIDENCE_UNAVAILABLE");
      measurements.push(await renderedContrast(lost.locator(".badge").first(), "Unknown-ownership warning severity"));
      measurements.push(await renderedContrast(panel.locator('[data-diagnostic-class="failed_cleanup"]').locator(".badge").first(), "Failed-cleanup error severity"));
      await activate(page, lost.getByRole("button", { name: "Reconcile ownership from the verified backend record.", exact: true }));
      await expect(panel.locator('[data-diagnostic-class="failed_cleanup"]')).toBeVisible();
      expect(writes).toEqual([]);
      for (const control of ["Stop", "Cancel"]) await expect(page.getByRole("button", { name: control, exact: true })).toHaveCount(0);
    } finally {
      await testInfo.attach("diagnostic-fixture-scope.json", { body: JSON.stringify({ viewport, fixture: fixture.evidenceScope, syntheticClasses: ["lost_connection", "failed_cleanup", "unavailable_evidence"], transportOnly: true, writes, measurements, limitations: ["Synthetic outcome display, not an observed provider/device failure", "No screen-reader or native Windows evidence"] }, null, 2), contentType: "application/json" });
    }
    for (const pair of measurements) {
      expect.soft(pair.supported, `${pair.label}: unsupported paint cannot pass`).toBe(true);
      if (pair.supported) expect.soft(pair.ratio, `${pair.label}: ${pair.color}, ratio ${pair.ratio}`).toBeGreaterThanOrEqual(4.5);
    }
  });

  test(`diagnostic accessibility: late preflight cannot reopen a departed workspace at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
    test.setTimeout(90000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    for (const destination of ["Home", "Workspace"]) {
      const project = await createFixtureProject(page, `Late preflight ${viewport.width} ${destination}`);
      await page.evaluate(async (id) => {
        const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
        const current = await fetch("/api/v1/projects/" + id).then((r) => r.json());
        const response = await fetch(`/api/v1/projects/${id}/edits`, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken, "If-Match": String(current.revision) }, body: JSON.stringify({ baseRevision: current.revision, edits: [{ kind: "set_parameter", parameterId: "gain", value: 0.7 }] }) });
        if (!response.ok) throw Error("Owned revision-race setup failed");
      }, project.projectId);
      let release!: () => void, prepared = false;
      const held = new Promise<void>((resolve) => { release = resolve; });
      let routeFinished: Promise<void> | undefined;
      const pattern = `**/api/v1/projects/${project.projectId}/preflights`;
      await page.route(pattern, async (route) => {
        let finish!: () => void;
        routeFinished = new Promise<void>((resolve) => { finish = resolve; });
        try {
          const response = await route.fetch();
          prepared = true;
          await held;
          await route.fulfill({ response });
        } finally { finish(); }
      });
      try {
        await activate(page, page.getByRole("button", { name: "Preflight & run", exact: true }));
        await expect.poll(() => prepared).toBe(true);
        const leave = destination === "Home"
          ? page.getByRole("button", { name: "X-Verse Studio home", exact: true })
          : page.locator(".breadcrumb").getByRole("button", { name: "Workspace", exact: true });
        await activate(page, leave, true);
        await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
        const completed = page.waitForResponse((response) => new URL(response.url()).pathname === `/api/v1/projects/${project.projectId}/preflights` && response.request().method() === "POST");
        release();
        await completed;
        await expect(page.locator(".notice.busy")).toHaveCount(0);
        await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
        await expect(page.getByRole("dialog", { name: "Execution preflight", exact: true })).toHaveCount(0);
      } finally { release(); if (routeFinished) await routeFinished; await page.unroute(pattern); }
    }
    await testInfo.attach("late-preflight-navigation.json", { body: JSON.stringify({ viewport, destinations: ["Home", "Workspace"], realSavedRevisionChange: true, delayedOwnedPreflight: true, lateModalSuppressed: true, runRequested: false }), contentType: "application/json" });
  });

  test(`diagnostic accessibility: real stale plan and labeled artifact recovery at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
    test.setTimeout(120000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    const project = await createFixtureProject(page, `Stale plan diagnostic ${viewport.width}`);
    let mode = "stale", frozen: any;
    const outcomes: unknown[] = [];
    const measurements: Awaited<ReturnType<typeof renderedContrast>>[] = [];
    const preflightPattern = `**/api/v1/projects/${project.projectId}/preflights`;
    await page.route(preflightPattern, async (route) => {
      const response = await route.fetch();
      frozen = await response.json();
      if (mode === "artifact") {
        frozen = { ...frozen, status: "blocked", readiness: { ...frozen.readiness, artifacts: {
          status: "unavailable", diagnosticCodes: ["ARTIFACT_UNAVAILABLE"],
          message: "Labeled missing-artifact transport fixture", elementRefs: ["xdl://org.xverse.studio.process-control/system/reference-loop#plant"],
        } }, diagnostics: [{ code: "ARTIFACT_UNAVAILABLE", severity: "error", message: "Labeled missing-artifact transport fixture", elementRef: "xdl://org.xverse.studio.process-control/system/reference-loop#plant", remediation: "Supply admitted exact artifact identities." }] };
        await route.fulfill({ response, json: frozen });
      } else await route.fulfill({ response });
    });
    await page.route(`**/api/v1/projects/${project.projectId}/preflights/*/diagnostics`, async (route) => {
      if (mode === "stale") {
        mode = "current";
        // Real mutable-input change after the frozen preflight, before its explanation read.
        await page.evaluate(async (projectId) => {
          const session = await fetch("/api/v1/session").then((r) => r.json());
          const project = await fetch("/api/v1/projects/" + projectId).then((r) => r.json());
          const response = await fetch(`/api/v1/projects/${projectId}/edits`, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken, "If-Match": String(project.revision) }, body: JSON.stringify({ baseRevision: project.revision, edits: [{ kind: "set_parameter", parameterId: "gain", value: 0.7 }] }) });
          if (!response.ok) throw Error("Owned stale-plan setup failed");
        }, project.projectId);
      }
      if (mode === "artifact") {
        const body = JSON.parse(execFileSync(path.resolve(".venv/bin/python"), ["-I", "-c", "import json,sys; from xverse_studio.diagnostics import explain_preflight; p=json.load(sys.stdin); print(json.dumps(explain_preflight(p,current_revision=p.get('revision',1),capability_digest=p.get('capabilityDigest'))))"], { input: JSON.stringify(frozen), encoding: "utf8", timeout: 30000 }));
        outcomes.push({ scope: "transport-only missing-artifact explanation", codes: body.findings.map((f: any) => f.code) });
        await route.fulfill({ json: body });
      } else {
        const response = await route.fetch();
        const body = await response.json();
        outcomes.push({ scope: "actual server explanation", codes: body.findings.map((f: any) => f.code) });
        await route.fulfill({ response });
      }
    });
    try {
      await activate(page, page.getByRole("button", { name: "Preflight & run", exact: true }));
      const panel = page.getByRole("region", { name: "Readiness explanation" });
      const stale = panel.locator('[data-diagnostic-class="stale_plan"]');
      await expect(stale).toContainText("PLAN_STALE");
      await expect(stale).toContainText("current inputs");
      await expect(stale.getByRole("button", { name: "Recheck readiness to freeze a fresh plan.", exact: true })).toBeVisible();
      measurements.push(await renderedContrast(stale.locator("h4"), "Stale-plan error finding"));
      await expect(page.getByRole("button", { name: "Start frozen snapshot", exact: true })).toBeDisabled();
      const stalePreflightId = frozen.preflightId;
      await activate(page, stale.getByRole("button", { name: "Recheck readiness to freeze a fresh plan.", exact: true }));
      await expect(page.getByRole("button", { name: "Start frozen snapshot", exact: true })).toBeEnabled();
      await expect(panel.locator('[data-diagnostic-class="stale_plan"]')).toHaveCount(0);
      expect(frozen.preflightId).not.toBe(stalePreflightId);
      await expect(page.getByRole("button", { name: "Recheck readiness", exact: true })).toBeFocused();
      mode = "artifact";
      await activate(page, page.getByRole("button", { name: "Recheck readiness", exact: true }));
      const missing = panel.locator('[data-diagnostic-class="missing_artifact"]');
      await expect(missing).toContainText("ARTIFACT_UNAVAILABLE");
      await expect(missing).toContainText("#plant");
      await expect(missing).toContainText("Supply admitted exact artifact identities.");
      await expect(page.getByRole("button", { name: "Start frozen snapshot", exact: true })).toBeDisabled();
      measurements.push(await renderedContrast(missing.locator(".badge").first(), "Missing-artifact error severity"));
      mode = "current";
      await activate(page, missing.getByRole("button", { name: "Recheck readiness to freeze a fresh plan.", exact: true }));
      await expect(page.getByRole("button", { name: "Start frozen snapshot", exact: true })).toBeEnabled();
      await expect(panel.locator('[data-diagnostic-class="missing_artifact"]')).toHaveCount(0);
      await page.keyboard.press("Escape");
    } finally {
      await testInfo.attach("stale-artifact-outcomes.json", { body: JSON.stringify({ viewport, outcomes, measurements, limitations: ["Stale plan is produced by an actual owned source edit and recovered by its offered Recheck action", "Artifact failure/recovery is a labeled transport fixture, not actual provider admission", "No run or physical action is requested"] }, null, 2), contentType: "application/json" });
    }
    for (const pair of measurements) {
      expect.soft(pair.supported, `${pair.label}: unsupported paint cannot pass`).toBe(true);
      if (pair.supported) expect.soft(pair.ratio, pair.label).toBeGreaterThanOrEqual(4.5);
    }
  });
}
