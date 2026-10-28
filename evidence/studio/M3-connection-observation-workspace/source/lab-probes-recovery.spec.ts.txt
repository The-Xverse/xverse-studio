import { test, expect, openLab, keyboard } from "./probe-fixture";
import type { Page } from "@playwright/test";

const key = "studio.lab.observations.v1";
const postPath = "**/api/v1/assets/fixture%3Abench-sensor/probes";
const optionPath = "**/api/v1/assets/fixture%3Abench-sensor/probe-options";
const card = (p: Page) => p.locator("section.panel").filter({ has: p.getByRole("heading", { name: "fixture:bench-sensor", exact: true }) });
const requests = (p: Page) => p.getByRole("region", { name: "Connection observation requests", exact: true });
const result = (p: Page) => p.getByRole("region", { name: "Connection observation result", exact: true });
const history = (p: Page) => p.getByRole("region", { name: "Recorded connection observations", exact: true });
async function options(p: Page) {
  await keyboard(p, card(p).getByRole("button", { name: "Check connection options", exact: true }));
  await expect(card(p)).toContainText("Observation permission: allowed");
}
function mutations(p: Page) {
  const values: { key: string; body: object }[] = [];
  p.on("request", (r) => { if (r.method() === "POST" && new URL(r.url()).pathname.endsWith("/probes")) values.push({ key: r.headers()["idempotency-key"], body: r.postDataJSON() }); });
  return values;
}
async function held(p: Page, path: string) {
  let release!: () => void, fetched!: () => void;
  const waiting = new Promise<void>((resolve) => { release = resolve; }), observed = new Promise<void>((resolve) => { fetched = resolve; });
  const value: { body?: any } = {};
  await p.route(path, async (route) => {
    const response = await route.fetch(), body = await response.text();
    expect(response.status()).toBe(path === postPath ? 202 : 200);
    value.body = JSON.parse(body); fetched(); await waiting;
    await route.fulfill({ response, body });
  });
  return { observed, release, value };
}
async function moveFocus(p: Page) {
  const target = p.getByRole("button", { name: "Environment", exact: true });
  for (let i = 0; i < 200 && !(await target.evaluate((e) => document.activeElement === e)); i++) await p.keyboard.press("Tab");
  await expect(target).toBeFocused();
  return target;
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test.describe(`lab probe recovery at ${viewport.width}`, () => {
    test.use({ viewport });

    test("lost actual acknowledgement survives reload and retries the exact original identity", async ({ page, probeHost }) => {
      await openLab(page, probeHost); const posts = mutations(page); let original: any;
      await options(page);
      await page.route(postPath, async (route) => {
        const response = await route.fetch(); expect(response.status()).toBe(202); original = await response.json();
        await route.abort("failed");
      });
      await keyboard(page, card(page).getByRole("button", { name: "Observe connection", exact: true }));
      await expect(requests(page)).toContainText("unconfirmed in this workspace");
      expect(probeHost.count()).toBe(1); expect(posts).toHaveLength(1);
      await page.unrouteAll({ behavior: "wait" });
      await page.reload(); await page.getByRole("button", { name: "Laboratory", exact: true }).click();
      const retry = page.getByRole("button", { name: "Retry same observation request", exact: true });
      await expect(retry).toBeEnabled(); expect(posts).toHaveLength(1); expect(probeHost.count()).toBe(1);
      await keyboard(page, retry);
      await expect(result(page)).toContainText(original.operationId);
      expect(posts).toHaveLength(2); expect(posts[1]).toEqual(posts[0]); expect(probeHost.count()).toBe(1);
      expect(await page.evaluate((k) => JSON.parse(sessionStorage.getItem(k)!).pending, key)).toBeNull();
      await page.reload(); await page.getByRole("button", { name: "Laboratory", exact: true }).click();
      const inspect = history(page).getByRole("button", { name: `Inspect observation ${original.operationId}`, exact: true });
      await expect(inspect).toBeEnabled(); await keyboard(page, inspect);
      await expect(result(page)).toContainText(original.operationId); expect(probeHost.count()).toBe(1);
    });

    test("departure preserves the original pending operation without reopening the view", async ({ page, probeHost }) => {
      await openLab(page, probeHost); await options(page); const posts = mutations(page), gate = await held(page, postPath);
      try {
        await keyboard(page, card(page).getByRole("button", { name: "Observe connection", exact: true }));
        await gate.observed; expect(probeHost.count()).toBe(1);
        await keyboard(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
        gate.release(); await page.unrouteAll({ behavior: "wait" });
        await expect(page.locator(".lab-page")).toHaveCount(0);
        await expect(page.getByRole("button", { name: "X-Verse Studio home", exact: true })).toBeFocused();
        await page.getByRole("button", { name: "Laboratory", exact: true }).click();
        const retry = page.getByRole("button", { name: "Retry same observation request", exact: true });
        await expect(retry).toBeEnabled(); expect(posts).toHaveLength(1);
        await keyboard(page, retry); await expect(result(page)).toContainText(gate.value.body.operationId);
        expect(posts[1]).toEqual(posts[0]); expect(probeHost.count()).toBe(1);
      } finally { gate.release(); await page.unrouteAll({ behavior: "wait" }); }
    });

    test("departed options cannot restore stale eligibility or focus", async ({ page, probeHost }) => {
      await openLab(page, probeHost); const gate = await held(page, optionPath);
      try {
        await keyboard(page, card(page).getByRole("button", { name: "Check connection options", exact: true }));
        await gate.observed;
        await keyboard(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
        gate.release(); await page.unrouteAll({ behavior: "wait" });
        await expect(page.locator(".lab-page")).toHaveCount(0);
        await expect(page.getByRole("button", { name: "X-Verse Studio home", exact: true })).toBeFocused();
        await page.getByRole("button", { name: "Laboratory", exact: true }).click();
        await expect(card(page).getByRole("button", { name: "Observe connection", exact: true })).toBeDisabled();
        expect(probeHost.count()).toBe(0);
      } finally { gate.release(); await page.unrouteAll({ behavior: "wait" }); }
    });

    for (const path of [optionPath, postPath]) {
      test(`${path === postPath ? "acknowledgement" : "options"} preserves deliberate keyboard focus`, async ({ page, probeHost }) => {
        await openLab(page, probeHost); if (path === postPath) await options(page);
        const gate = await held(page, path);
        try {
          await keyboard(page, card(page).getByRole("button", { name: path === postPath ? "Observe connection" : "Check connection options", exact: true }));
          await gate.observed; const target = await moveFocus(page);
          gate.release(); await page.unrouteAll({ behavior: "wait" });
          if (path === postPath) await expect(result(page)).toContainText(gate.value.body.operationId);
          else await expect(card(page)).toContainText("Observation permission: allowed");
          await expect(target).toBeFocused(); expect(probeHost.count()).toBe(path === postPath ? 1 : 0);
        } finally { gate.release(); await page.unrouteAll({ behavior: "wait" }); }
      });
    }

    test("acknowledgement cannot steal focus from a labelled native dialog guard control", async ({ page, probeHost }) => {
      await openLab(page, probeHost); await options(page); const gate = await held(page, postPath);
      try {
        await keyboard(page, card(page).getByRole("button", { name: "Observe connection", exact: true })); await gate.observed;
        // Browser-only modal guard fixture, not a Studio dialog or AT acceptance claim.
        await page.evaluate(() => {
          const d = document.createElement("dialog"), b = document.createElement("button");
          d.setAttribute("role", "dialog"); d.setAttribute("aria-label", "Owned observation dialog guard");
          b.textContent = "Close owned dialog"; b.onclick = () => d.remove(); d.append(b); document.body.append(d); d.showModal(); b.focus();
        });
        gate.release(); await page.unrouteAll({ behavior: "wait" });
        await expect(result(page)).toContainText(gate.value.body.operationId);
        await expect(page.getByRole("dialog", { name: "Owned observation dialog guard" })).toBeVisible();
        await expect(page.getByRole("button", { name: "Close owned dialog" })).toBeFocused();
        await page.keyboard.press("Enter"); expect(probeHost.count()).toBe(1);
      } finally { gate.release(); await page.unrouteAll({ behavior: "wait" }); }
    });

    test("repeat pending Enter never creates another observation", async ({ page, probeHost }) => {
      await openLab(page, probeHost); await options(page); const posts = mutations(page), gate = await held(page, postPath);
      try {
        await keyboard(page, card(page).getByRole("button", { name: "Observe connection", exact: true })); await gate.observed;
        await page.keyboard.press("Enter"); await page.keyboard.press("Enter"); await page.keyboard.press("Enter");
        expect(posts).toHaveLength(1); expect(probeHost.count()).toBe(1);
        gate.release(); await page.unrouteAll({ behavior: "wait" });
        await expect(result(page)).toContainText(gate.value.body.operationId); expect(posts).toHaveLength(1);
      } finally { gate.release(); await page.unrouteAll({ behavior: "wait" }); }
    });

    for (const corruption of ["version", "asset", "authority"]) {
      test(`labelled malformed ${corruption} options remain unknown and disable contact`, async ({ page, probeHost }) => {
        await openLab(page, probeHost);
        await page.route(optionPath, async (route) => {
          const response = await route.fetch(), value = await response.json();
          if (corruption === "version") value.contractVersion = "999";
          if (corruption === "asset") value.assetId = "foreign-asset";
          if (corruption === "authority") value.runtimeAdmission = "ready";
          await route.fulfill({ response, json: value });
        });
        try {
          await keyboard(page, card(page).getByRole("button", { name: "Check connection options", exact: true }));
          await expect(card(page).getByRole("alert")).toContainText("eligibility is unknown");
          await expect(card(page).getByRole("alert")).toBeFocused();
          await expect(card(page).getByRole("button", { name: "Observe connection", exact: true })).toBeDisabled();
          expect(probeHost.count()).toBe(0);
        } finally { await page.unrouteAll({ behavior: "wait" }); }
      });
    }

    for (const corruption of ["binding", "authority"]) {
      test(`labelled malformed ${corruption} acknowledgement retains same-key recovery`, async ({ page, probeHost }) => {
        await openLab(page, probeHost); await options(page); const posts = mutations(page); let original: any;
        await page.route(postPath, async (route) => {
          const response = await route.fetch(), value = await response.json(); original = { ...value };
          if (corruption === "binding") value.bindingDigest = "sha256:" + "f".repeat(64);
          else value.runtimeAdmission = "ready";
          await route.fulfill({ response, json: value });
        });
        try {
          await keyboard(page, card(page).getByRole("button", { name: "Observe connection", exact: true }));
          await expect(requests(page)).toContainText("unconfirmed in this workspace"); expect(probeHost.count()).toBe(1);
        } finally { await page.unrouteAll({ behavior: "wait" }); }
        await keyboard(page, page.getByRole("button", { name: "Retry same observation request", exact: true }));
        await expect(result(page)).toContainText(original.operationId);
        expect(posts).toHaveLength(2); expect(posts[1]).toEqual(posts[0]); expect(probeHost.count()).toBe(1);
      });
    }

    for (const phase of ["before-send", "after-ack"]) {
      test(`storage failure ${phase} preserves original request and never duplicates provider work`, async ({ page, probeHost }) => {
        await page.addInitScript(({ phase, key }) => {
          const set = Storage.prototype.setItem;
          Storage.prototype.setItem = function (name, value) {
            if (name === key && (phase === "before-send" || JSON.parse(String(value)).pending === null)) throw new Error("Owned observation storage fault");
            return set.call(this, name, value);
          };
          (window as any).restoreOwnedObservationStorage = () => { Storage.prototype.setItem = set; };
        }, { phase, key });
        await openLab(page, probeHost); await options(page); const posts = mutations(page);
        await keyboard(page, card(page).getByRole("button", { name: "Observe connection", exact: true }));
        await expect(requests(page).getByRole("alert")).toContainText("Owned observation storage fault");
        expect(probeHost.count()).toBe(phase === "before-send" ? 0 : 1);
        await page.evaluate(() => (window as any).restoreOwnedObservationStorage());
        await keyboard(page, page.getByRole("button", { name: "Retry same observation request", exact: true }));
        await expect(result(page)).toContainText("completed"); expect(probeHost.count()).toBe(1);
        expect(posts).toHaveLength(phase === "before-send" ? 1 : 2);
        if (phase === "after-ack") expect(posts[1]).toEqual(posts[0]);
      });
    }

    test("unreadable saved metadata is preserved and cannot start another observation", async ({ page, probeHost }) => {
      await page.addInitScript((key) => sessionStorage.setItem(key, "owned unreadable pending metadata"), key);
      await openLab(page, probeHost); await options(page);
      await expect(requests(page).getByRole("alert")).toContainText("Saved observation request metadata is unavailable");
      await expect(card(page).getByRole("button", { name: "Observe connection", exact: true })).toBeDisabled();
      expect(probeHost.count()).toBe(0);
      expect(await page.evaluate((key) => sessionStorage.getItem(key), key)).toBe("owned unreadable pending metadata");
    });
  });
}
