import {
  test as base,
  expect,
  type Page,
  type Locator,
} from "@playwright/test";
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";

type Host = { origin: string; data: string };
export const test = base.extend<{ scenario: string; failureHost: Host }>({
  scenario: ["mismatch", { option: true }],
  failureHost: async ({ scenario }, use, info) => {
    const data = info.outputPath("owned-startup.private"),
      python =
        process.env.STUDIO_TEST_PYTHON ||
        path.resolve(
          process.platform === "win32"
            ? ".venv/Scripts/python.exe"
            : ".venv/bin/python",
        );
    const child = spawn(
      python,
      [
        "-I",
        "tests/fixtures/providers/run_failures/host.py",
        "--data",
        data,
        "--scenario",
        scenario,
      ],
      { stdio: ["ignore", "pipe", "pipe"] },
    );
    let tail = "",
      served = false;
    child.stderr.on("data", (chunk) => {
      tail = (tail + String(chunk)).slice(-4000);
    });
    try {
      const origin = await new Promise<string>((resolve, reject) => {
        let buffer = "";
        const timer = setTimeout(
          () => reject(Error("Owned startup host readiness timed out")),
          15000,
        );
        child.once("error", (error) => {
          clearTimeout(timer);
          reject(error);
        });
        child.once("exit", (code) => {
          clearTimeout(timer);
          reject(Error(`Owned startup host exited ${code}: ${tail}`));
        });
        child.stdout.on("data", (chunk) => {
          buffer += String(chunk);
          if (buffer.length > 4096) {
            clearTimeout(timer);
            reject(Error("Owned readiness exceeded bound"));
            return;
          }
          if (buffer.includes("\n")) {
            clearTimeout(timer);
            try {
              resolve(JSON.parse(buffer.split("\n")[0]).origin);
            } catch (error) {
              reject(error);
            }
          }
        });
      });
      await expect
        .poll(async () => {
          try {
            return (await fetch(origin + "/api/v1/session")).status;
          } catch {
            return 0;
          }
        })
        .toBe(401);
      served = true;
      await use({ origin, data });
    } finally {
      if (child.exitCode === null && child.signalCode === null)
        child.kill("SIGTERM");
      await new Promise<void>((resolve) => {
        if (child.exitCode !== null || child.signalCode !== null) {
          resolve();
          return;
        }
        const timer = setTimeout(() => child.kill("SIGKILL"), 15000);
        child.once("exit", () => {
          clearTimeout(timer);
          resolve();
        });
      });
      if (served) {
        const observed = JSON.parse(
          readFileSync(path.join(data, "fixture-observation.json"), "utf8"),
        );
        expect(observed.scope).toBe("owned native fault fixture; no equipment");
        expect(observed.scenario).toBe(scenario);
        expect(observed.errors).toEqual([]);
        expect(observed.workerAttempts).toBe(
          scenario === "prepare_denied" ? 0 : 1,
        );
        expect(observed.preparationRefusals).toBe(
          scenario === "prepare_denied" ? 1 : 0,
        );
        expect(observed.journalOpenFaults).toBe(
          scenario === "journal_open" ? 1 : 0,
        );
        expect(observed.journalFinalizationFaults).toBe(
          scenario === "journal_finalize" ? 1 : 0,
        );
        expect(observed.cleanupObstructions).toBe(
          scenario === "cleanup_failure" ? 1 : 0,
        );
        expect(observed.corruptions).toBe(scenario === "mismatch" ? 1 : 0);
        expect(observed.launchRefusals).toBe(
          scenario === "launch_denied" ? 1 : 0,
        );
        expect(observed.interruptions).toBe(
          scenario === "active_failure" ? 1 : 0,
        );
        if (scenario === "ownership_recovery")
          expect(observed.ownershipDenials).toBeGreaterThan(0);
        else expect(observed.ownershipDenials).toBe(0);
        await info.attach("owned-native-fault-observation", {
          body: JSON.stringify(observed),
          contentType: "application/json",
        });
      }
    }
  },
});
export { expect };
export async function authenticate(page: Page, host: Host) {
  const boot = JSON.parse(
    readFileSync(path.join(host.data, "bootstrap.json"), "utf8"),
  );
  const response = await page.request.post(host.origin + "/api/v1/session", {
    headers: { Origin: host.origin },
    data: { bootstrapToken: boot.bootstrapToken },
  });
  expect(response.status()).toBe(200);
  await page.goto(host.origin);
}
export async function keyboard(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 220; i++) {
    if (await target.evaluate((node) => node === document.activeElement)) break;
    await page.keyboard.press("Tab");
  }
  await expect(target).toBeFocused();
  await page.keyboard.press("Enter");
}
