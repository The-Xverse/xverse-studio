/** Explicit live invocation only. The default fixture/browser suite excludes this directory. */
import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { readFileSync } from "node:fs";
import YAML from "yaml";
import { connectStudio } from "../e2e/connect-studio";

if (process.env.STUDIO_AUTOVERSE_LIVE !== "1") throw new Error("This test requires an explicitly enrolled native Autoverse backend and STUDIO_AUTOVERSE_LIVE=1.");

test("actual Autoverse: browser load, full start, driving, cruise, lease expiry and full stop", async ({ page }, info) => {
  await connectStudio(page, info);
  await page.bringToFront();
  await page.locator(".example-grid").getByRole("button", { name: /Autoverse complete demo/ }).click();
  await expect(page.locator(".project-header h1")).toHaveText("Autoverse complete demo");
  // This retained case explicitly selects historical browser mode. New examples
  // default to the original native Pygame window.
  const pid = await page.evaluate(() => localStorage.getItem("studio.projectId"));
  let project = await (await page.request.get(`/api/v1/projects/${pid}`)).json();
  const { csrfToken } = await (await page.request.get("/api/v1/session")).json();
  for (const [id, doc] of Object.entries(project.documents) as [string, any][]) {
    const source = YAML.parse(doc.content);
    if (source.kind === "Scenario") {
      source.spec.initialConditions.driverSurface = "studio-browser";
      source.spec.initialConditions.initialBrakingRequest = 1;
      source.extensions["io.xverse.studio.native-runtime"].inputSurface = "studio-browser";
    } else if (source.kind === "System") {
      source.spec.nodes.find((n: any) => n.id === "driver-node").roles = ["Browser driver controls"];
      source.spec.interfaces = source.spec.interfaces.filter((v: any) => v.id !== "driver-speed-inhibit");
      source.spec.endpoints = source.spec.endpoints.filter((v: any) => v.interfaceId !== "driver-speed-inhibit");
      source.spec.flows = source.spec.flows.filter((v: any) => v.interfaceId !== "driver-speed-inhibit");
    } else if (source.kind === "Component" && source.metadata.name === "driver") {
      source.spec.interfaces = source.spec.interfaces.filter((v: any) => v.id !== "driver-speed-inhibit");
    } else if (source.kind === "Deployment") {
      const contract = JSON.parse(readFileSync(path.resolve("services/studio-api/src/xverse_studio/blueprints/autoverse-contract.json"), "utf8"));
      const { createHash } = await import("node:crypto");
      source.spec.artifacts[0].digest = "sha256:" + createHash("sha256").update(readFileSync(path.resolve("services/studio-api/src/xverse_studio/blueprints/autoverse-contract.json"))).digest("hex");
      expect(contract.inputSurface).toBe("studio-browser");
    } else continue;
    const response = await page.request.put(`/api/v1/projects/${pid}/documents/${id}`, {
      headers: { "Origin": new URL(page.url()).origin, "X-CSRF-Token": csrfToken, "If-Match": String(project.revision) },
      data: { content: YAML.stringify(source), format: doc.format },
    });
    expect(response.ok()).toBe(true);
    project = await response.json();
  }
  await page.reload();
  await page.getByRole("button", { name: "Preflight & run", exact: true }).click();
  const start = page.getByRole("button", { name: "Start frozen snapshot", exact: true });
  await expect(start).toBeEnabled({ timeout: 45000 });
  const request = page.waitForResponse((r) => r.request().method() === "POST" && new URL(r.url()).pathname === "/api/v1/runs");
  await start.click();
  const accepted = await (await request).json();
  expect(accepted.runId).toBeTruthy();
  const rid = accepted.runId;
  const run = async () => (await page.request.get(`/api/v1/runs/${rid}`)).json();
  const observations: any[] = [];
  const adb = (args: string[]) => execFileSync("adb", ["-s", "localhost:6520", ...args], { timeout: 15000, maxBuffer: 1024 * 1024 });
  const androidNodes = () => {
    const target = `/sdcard/xverse-studio-${rid}-ui.xml`;
    adb(["shell", "uiautomator", "dump", target]);
    const xml = adb(["exec-out", "cat", target]).toString();
    const nodes = [...xml.matchAll(/<node\b[^>]*>/g)].map((match) => Object.fromEntries([...match[0].matchAll(/([a-z-]+)="([^"]*)"/g)].map((a) => [a[1], a[2]])));
    return { xml, nodes };
  };
  const tapNode = (node: Record<string, string>) => {
    const values = [...node.bounds.matchAll(/\d+/g)].map((m) => Number(m[0]));
    expect(values).toHaveLength(4);
    expect(values[2]).toBeLessThanOrEqual(1080); expect(values[3]).toBeLessThanOrEqual(600);
    adb(["shell", "input", "tap", String(Math.round((values[0] + values[2]) / 2)), String(Math.round((values[1] + values[3]) / 2))]);
  };
  try {
    await expect.poll(async () => {
      const value = await run();
      if (value.state === "failed") throw new Error("Native startup failed: " + value.reason);
      return value.state;
    }, { timeout: 540000, intervals: [1000] }).toBe("running");
    const openControls = page.getByRole("button", { name: "Open driving controls", exact: true });
    await expect(openControls).toBeVisible();
    await expect(openControls).toBeInViewport({ ratio: 0.5 });
    await openControls.click();
    await expect(page.getByRole("dialog", { name: "Vehicle driving controls" })).toBeVisible();
    const panel = page.getByRole("region", { name: "Browser driving controls", exact: true });
    await expect(panel).toBeVisible();
    const android = androidNodes();
    const gear = android.nodes.find((node) => node.text === "⚙");
    if (gear) tapNode(gear);
    const settings = androidNodes();
    expect(settings.nodes.some((node) => node.text === "Zenoh connection")).toBe(true);
    const installation = JSON.parse(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, "runs", rid, "request.json"), "utf8")).nativeInstallation;
    expect(settings.nodes.some((node) => node.text === `tcp/${installation.androidGateway}:7447`)).toBe(true);
    tapNode(settings.nodes.find((node) => node.text === "client (router)")!);
    tapNode(settings.nodes.find((node) => node.text === "Save")!);
    adb(["shell", "am", "force-stop", "com.example.digitalclusterapp"]);
    adb(["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER", "-p", "com.example.digitalclusterapp"]);
    await page.waitForTimeout(2000);
    const androidPid = adb(["shell", "pidof", "com.example.digitalclusterapp"]).toString().trim();
    expect(androidPid).toMatch(/^\d+$/);
    await info.attach("actual-android-connection-log.txt", { body: adb(["logcat", `--pid=${androidPid}`, "-d", "-t", "250"]), contentType: "text/plain" });
    await info.attach("native-browser-environment.json", { body: JSON.stringify({ browser: page.context().browser()?.version(), operatingSystem: process.platform, viewport: page.viewportSize() }), contentType: "application/json" });
    const inspectionSeconds = Number(process.env.STUDIO_ANDROID_INSPECT_SECONDS || 0);
    if (inspectionSeconds > 0 && inspectionSeconds <= 60) await page.waitForTimeout(inspectionSeconds * 1000);
    await panel.getByRole("button", { name: "Enable browser driver", exact: true }).click();
    await expect(panel.getByLabel("Throttle", { exact: true })).toBeEnabled();
    await panel.getByLabel("Throttle", { exact: true }).fill("0.65");
    await page.waitForTimeout(3000);
    try {
      await info.attach("actual-carla-applied-control.json", { body: execFileSync("/usr/bin/python3", ["-E", path.resolve("services/studio-api/src/xverse_studio/providers/autoverse/carla_probe.py"), "--vehicle-status"], { timeout: 15000 }), contentType: "application/json" });
    } catch (error) {
      await info.attach("independent-carla-probe-unavailable.txt", { body: String(error), contentType: "text/plain" });
    }
    await expect.poll(async () => {
      const value = await run();
      const sample = value.inputTelemetry?.items?.speed;
      observations.push({ state: value.state, telemetry: value.inputTelemetry });
      return sample?.status === "observed" ? sample.value : -1;
    }, { timeout: 30000, intervals: [300] }).toBeGreaterThan(12);
    const screen = adb(["exec-out", "screencap", "-p"]);
    const png = screen.indexOf(Buffer.from([137,80,78,71,13,10,26,10]));
    expect(png).toBeGreaterThanOrEqual(0);
    await info.attach("actual-android-speed-screen.png", { body: screen.subarray(png), contentType: "image/png" });
    await panel.getByRole("button", { name: "Coast / release pedals", exact: true }).click();
    const engage = panel.getByRole("button", { name: "Engage cruise", exact: true });
    await expect(engage).toBeEnabled();
    await engage.click();
    await expect.poll(async () => (await run()).inputTelemetry?.items?.cruiseEngaged?.value, { timeout: 15000 }).toBe(true);
    await expect.poll(async () => {
      const target = (await run()).inputTelemetry?.items?.cruiseTargetSpeed;
      return target?.status === "observed" ? target.value : -1;
    }, { timeout: 15000 }).toBeGreaterThan(0);
    const before = (await run()).inputTelemetry.items.cruiseTargetSpeed.value;
    await panel.getByRole("button", { name: "Cruise +5 km/h", exact: true }).click();
    await expect.poll(async () => (await run()).inputTelemetry?.items?.cruiseTargetSpeed?.value, { timeout: 15000 }).toBeGreaterThan(before + 4);
    observations.push(await run());
    const movingLog = adb(["logcat", `--pid=${androidPid}`, "-d", "-t", "3000"]).toString();
    await info.attach("actual-android-moving-log.txt", { body: movingLog, contentType: "text/plain" });
    const appSpeeds = [...movingLog.matchAll(/State after update: .*?speed=(\d+)/g)].map((match) => Number(match[1]));
    expect(appSpeeds.some((value) => value > 0), "Android updates its live cluster state from moving-vehicle data").toBe(true);

    // Simulate browser transport loss; the backend and adapter watchdog remain real.
    await page.route(`**/api/v1/runs/${rid}/input/**`, (route) => route.abort());
    await expect.poll(async () => (await run()).inputTelemetry?.driverLeaseActive, { timeout: 7000 }).toBe(false);
    await expect.poll(async () => (await run()).inputTelemetry?.items?.vcuBrakeCommand?.value, { timeout: 7000 }).toBe(1);
    await expect.poll(async () => (await run()).inputTelemetry?.items?.cruiseEngaged?.value, { timeout: 7000 }).toBe(false);
    await page.unroute(`**/api/v1/runs/${rid}/input/**`);
    await page.screenshot({ path: info.outputPath("actual-browser-driving.png"), fullPage: true });
  } finally {
    await info.attach("actual-interface-observations.json", { body: JSON.stringify(observations), contentType: "application/json" });
    await page.unroute(`**/api/v1/runs/${rid}/input/**`);
    const dialog = page.getByRole("dialog", { name: "Vehicle driving controls" });
    if (await dialog.isVisible()) await dialog.getByRole("button", { name: "Close dialog", exact: true }).click();
    const current = await run();
    if (["preparing", "ready", "running", "paused"].includes(current.state)) {
      const stop = page.getByRole("region", { name: "Run controls", exact: true }).getByRole("button", { name: "Stop", exact: true });
      if (await stop.isEnabled()) await stop.click();
      else await page.evaluate(async ({ rid, version }) => {
        const session = await fetch("/api/v1/session").then((r) => r.json());
        await fetch(`/api/v1/runs/${rid}/commands`, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken, "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ kind: "stop", expectedStateVersion: version }) });
      }, { rid, version: current.stateVersion });
    }
    await expect.poll(async () => (await run()).state, { timeout: 90000, intervals: [1000] }).toMatch(/^(stopped|failed)$/);
    expect((await run()).cleanup).toBe("complete");
    const evidence = await (await page.request.get(`/api/v1/runs/${rid}/evidence`)).json();
    expect(evidence.integrity).toBe("valid");
    await info.attach("terminal-native-evidence.json", { body: JSON.stringify({ run: await run(), evidence }), contentType: "application/json" });
  }
});
