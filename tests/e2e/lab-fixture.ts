import { test as base, expect, type Locator, type Page } from "@playwright/test";
import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

type Host = { origin: string; data: string };
export const test = base.extend<{ scenario: string; labHost: Host }>({
  scenario: ["observe", { option: true }],
  labHost: async ({ scenario }, use, info) => {
    const data = info.outputPath("owned-fixture.private"),
      python = process.env.STUDIO_TEST_PYTHON || path.resolve(process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python"),
      child = spawn(python, ["-I", "tests/fixtures/providers/physical/browser_host.py", "--data", data, "--scenario", scenario],
        { stdio: ["ignore", "pipe", "pipe"] });
    let diagnostic = "";
    child.stderr.on("data", (chunk) => { diagnostic = (diagnostic + String(chunk)).slice(-4000); });
    try {
      const origin = await new Promise<string>((resolve, reject) => {
        let buffer = "";
        // History prepares 51 real durable reserve/release pairs before serving.
        // Bound this fixture work separately; the HTTP readiness/interaction budgets stay unchanged.
        const preparationBudget = scenario === "history" ? 60000 : 15000;
        const timer = setTimeout(() => reject(new Error("Owned fixture preparation timed out.")), preparationBudget);
        child.once("error", (error) => { clearTimeout(timer); reject(error); });
        child.once("exit", (code) => { clearTimeout(timer); reject(new Error(`Owned fixture exited before readiness (${code}): ${diagnostic}`)); });
        child.stdout.on("data", (chunk) => {
          buffer += String(chunk);
          if (buffer.length > 4096) { clearTimeout(timer); reject(new Error("Fixture readiness exceeded its bound.")); return; }
          if (buffer.includes("\n")) {
            clearTimeout(timer);
            try { resolve(JSON.parse(buffer.split("\n")[0]).origin); } catch (e) { reject(e); }
          }
        });
      });
      await expect.poll(async () => {
        try { return (await fetch(origin + "/api/v1/session")).status; } catch { return 0; }
      }).toBe(401);
      await use({ origin, data });
    } finally {
      if (child.exitCode === null && child.signalCode === null) child.kill("SIGTERM");
      await new Promise<void>((resolve) => {
        if (child.exitCode !== null || child.signalCode !== null) { resolve(); return; }
        const timer = setTimeout(() => { child.kill("SIGKILL"); }, 10000);
        child.once("exit", () => { clearTimeout(timer); resolve(); });
      });
      const observation = path.join(data, "fixture-observation.json");
      if (existsSync(observation)) await info.attach("owned-provider-observation", {
        body: readFileSync(observation), contentType: "application/json",
      });
    }
  },
});
export { expect };

export async function openLab(page: Page, host: Host) {
  const bootstrap = JSON.parse(readFileSync(path.join(host.data, "bootstrap.json"), "utf8"));
  const response = await page.request.post(host.origin + "/api/v1/session", {
    headers: { Origin: host.origin }, data: { bootstrapToken: bootstrap.bootstrapToken },
  });
  expect(response.status()).toBe(200);
  await page.goto(host.origin);
  await page.getByRole("button", { name: "Laboratory", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Physical assets", exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "Reservation history", exact: true })).toContainText("Principal: local-operator");
}

export async function keyboard(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 200; i++) {
    if (await target.evaluate((n) => document.activeElement === n)) break;
    await page.keyboard.press("Tab");
  }
  await expect(target).toBeFocused();
  await page.keyboard.press("Enter");
}
