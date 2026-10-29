import { test as base, expect } from "@playwright/test";
import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
export { openLab, keyboard } from "./lab-fixture";

type Host = { origin: string; data: string; count: () => number };
export const test = base.extend<{ probeScenario: string; probeHost: Host }>({
  probeScenario: ["observe", { option: true }],
  probeHost: async ({ probeScenario }, use, info) => {
    const data = info.outputPath("owned-probe-fixture.private"),
      python = process.env.STUDIO_TEST_PYTHON || path.resolve(process.platform === "win32" ? ".venv/Scripts/python.exe" : ".venv/bin/python"),
      child = spawn(python, ["-I", "tests/fixtures/providers/physical/probe_browser_host.py", "--data", data, "--scenario", probeScenario], { stdio: ["ignore", "pipe", "pipe"] });
    let diagnostic = "", started = false;
    child.stderr.on("data", (chunk) => { diagnostic = (diagnostic + String(chunk)).slice(-4000); });
    try {
      const origin = await new Promise<string>((resolve, reject) => {
        let buffer = "";
        const timer = setTimeout(() => reject(new Error("Owned probe host preparation timed out.")), 15000);
        child.once("error", (e) => { clearTimeout(timer); reject(e); });
        child.once("exit", (code) => { clearTimeout(timer); reject(new Error(`Owned probe host exited (${code}): ${diagnostic}`)); });
        child.stdout.on("data", (chunk) => {
          buffer += String(chunk);
          if (buffer.length > 4096) { clearTimeout(timer); reject(new Error("Owned probe announcement exceeded its bound.")); return; }
          if (buffer.includes("\n")) {
            clearTimeout(timer);
            try { resolve(JSON.parse(buffer.split("\n")[0]).origin); } catch (e) { reject(e); }
          }
        });
      });
      await expect.poll(async () => { try { return (await fetch(origin + "/api/v1/session")).status; } catch { return 0; } }).toBe(401);
      started = true;
      await use({ origin, data, count: () => {
        const file = path.join(data, "probe-call-count.json");
        return existsSync(file) ? JSON.parse(readFileSync(file, "utf8")) : 0;
      } });
    } finally {
      if (child.exitCode === null && child.signalCode === null) child.kill("SIGTERM");
      await new Promise<void>((resolve) => {
        if (child.exitCode !== null || child.signalCode !== null) { resolve(); return; }
        const timer = setTimeout(() => child.kill("SIGKILL"), 10000);
        child.once("exit", () => { clearTimeout(timer); resolve(); });
      });
      if (started) {
        const file = path.join(data, "probe-fixture-observation.json");
        expect(existsSync(file), "Owned observation host must retain its shutdown witness").toBe(true);
        const value = JSON.parse(readFileSync(file, "utf8"));
        expect(Object.keys(value).sort()).toEqual(["scope", "scenario", "leaseCalls", "probeCalls", "reservationCount", "remainingProviderLeases", "operations"].sort());
        expect(value.scope).toBe("owned native observation fixture; no equipment");
        expect(value.scenario).toBe(probeScenario);
        expect(value.reservationCount).toBe(0); expect(value.remainingProviderLeases).toBe(0);
        expect(value.leaseCalls.length <= 1000 && value.leaseCalls.every((name: string) => name === "inventory")).toBe(true);
        expect(value.probeCalls.length <= 20 && new Set(value.probeCalls).size === value.probeCalls.length).toBe(true);
        expect(value.operations.length <= 20 && value.probeCalls.every((id: string) => value.operations.some((v: any) => v.operationId === id))).toBe(true);
        await info.attach("owned-observation-provider-witness", { body: readFileSync(file), contentType: "application/json" });
      }
    }
  },
});
export { expect };
