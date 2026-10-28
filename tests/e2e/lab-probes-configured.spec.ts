import { test, expect, openLab, keyboard } from "./probe-fixture";
import type { Page } from "@playwright/test";

const storageKey = "studio.lab.observations.v1";
const card = (page: Page) => page.locator("section.panel").filter({ has: page.getByRole("heading", { name: "fixture:bench-sensor", exact: true }) });
const result = (page: Page) => page.getByRole("region", { name: "Connection observation result", exact: true });
const requests = (page: Page) => page.getByRole("region", { name: "Connection observation requests", exact: true });
const history = (page: Page) => page.getByRole("region", { name: "Recorded connection observations", exact: true });
async function options(page: Page, allowed = true) {
  await keyboard(page, card(page).getByRole("button", { name: "Check connection options", exact: true }));
  await expect(card(page).getByRole("heading", { name: "Connection observation", exact: true })).toBeFocused();
  await expect(card(page)).toContainText(`Observation permission: ${allowed ? "allowed" : "unavailable"}`);
}
async function observe(page: Page) {
  await options(page);
  const response = page.waitForResponse((r) => r.request().method() === "POST" && new URL(r.url()).pathname.endsWith("/probes"));
  await keyboard(page, card(page).getByRole("button", { name: "Observe connection", exact: true }));
  const actual = await response;
  expect(actual.status()).toBe(202);
  const body = await actual.json();
  await expect(result(page)).toBeVisible();
  return body;
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test.describe(`configured lab probes at ${viewport.width}`, () => {
    test.use({ viewport });
    test("explicit observation preserves clocks, private boundaries and canonical run state", async ({ page, probeHost }) => {
      const errors: string[] = [], posts: any[] = [];
      page.on("pageerror", (e) => errors.push(e.message));
      page.on("request", (r) => { if (r.method() === "POST" && new URL(r.url()).pathname.endsWith("/probes")) posts.push({ body: r.postDataJSON(), key: r.headers()["idempotency-key"] }); });
      await openLab(page, probeHost);
      expect(probeHost.count()).toBe(0);
      const projects = await (await page.request.get(probeHost.origin + "/api/v1/projects")).json();
      const op = await observe(page);
      expect(op.status).toBe("completed"); expect(op.result.status).toBe("observed");
      await expect(result(page).getByRole("heading", { name: "Connection observation result", exact: true })).toBeFocused();
      await expect(result(page)).toContainText("-9007199254740993 ns");
      await expect(result(page)).toContainText("fixture-probe-clock");
      await expect(result(page)).toContainText("fixture-observation-r3");
      await expect(result(page)).toContainText("fixture-image-v2");
      await expect(result(page)).toContainText("Unknown");
      await expect(result(page)).toContainText("Execution readiness");
      await expect(result(page)).toContainText("Unavailable");
      expect(JSON.stringify(op)).not.toContain("owned-fixture-private-payload");
      expect(JSON.stringify(op)).not.toContain("owned-loopback-fixture-handle");
      expect(posts).toHaveLength(1); expect(Object.keys(posts[0].body).sort()).toEqual(["expectedBindingDigest", "scope"]);
      expect(posts[0].body.scope).toBe("observe"); expect(posts[0].key).toBeTruthy(); expect(probeHost.count()).toBe(1);
      await keyboard(page, history(page).getByRole("button", { name: `Inspect observation ${op.operationId}`, exact: true }));
      await expect(result(page)).toContainText(op.operationId); expect(probeHost.count()).toBe(1);
      expect((await (await page.request.get(probeHost.origin + "/api/v1/projects")).json())).toEqual(projects);
      expect((await (await page.request.get(probeHost.origin + "/api/v1/runs")).json()).items).toEqual([]);
      expect((await (await page.request.get(probeHost.origin + "/api/v1/reservations")).json()).items).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)).toBe(false);
      expect(errors).toEqual([]);
    });

    test.describe("observation grant is independent", () => {
      test.use({ probeScenario: "forbidden" });
      test("lease observe permission cannot enable a probe or bypass backend authority", async ({ page, probeHost }) => {
        await openLab(page, probeHost); await options(page, false);
        await expect(card(page)).toContainText("FORBIDDEN");
        await expect(card(page).getByRole("button", { name: "Observe connection", exact: true })).toBeDisabled();
        const option = await (await page.request.get(probeHost.origin + "/api/v1/assets/fixture%3Abench-sensor/probe-options")).json();
        const session = await (await page.request.get(probeHost.origin + "/api/v1/session")).json();
        const response = await page.request.post(probeHost.origin + "/api/v1/assets/fixture%3Abench-sensor/probes", {
          headers: { Origin: probeHost.origin, "X-CSRF-Token": session.csrfToken, "Idempotency-Key": "owned-direct-forbidden-observation" },
          data: { expectedBindingDigest: option.installation.bindingDigest },
        });
        expect(response.status()).toBe(403); expect((await response.json()).code).toBe("FORBIDDEN");
        const lease = await (await page.request.get(probeHost.origin + "/api/v1/assets/fixture%3Abench-sensor/reservation-options")).json();
        expect(lease.scopes.find((v: any) => v.scope === "observe").eligible).toBe(true);
        expect(probeHost.count()).toBe(0);
      });
    });

    for (const scenario of ["unavailable", "unknown", "revoked", "timeout"]) {
      test.describe(scenario, () => {
        test.use({ probeScenario: scenario });
        test("negative or uncertain observation remains separate from readiness and is never repeated by inspection", async ({ page, probeHost }) => {
          await openLab(page, probeHost);
          const op = await observe(page);
          expect(op.status).toBe(scenario === "unavailable" ? "completed" : "unknown");
          expect(op.result?.status || null).toBe(scenario === "unavailable" ? "unavailable" : null);
          await expect(result(page)).toContainText("Unknown");
          await expect(result(page)).toContainText("Unavailable");
          expect(probeHost.count()).toBe(1);
          await keyboard(page, history(page).getByRole("button", { name: `Inspect observation ${op.operationId}`, exact: true }));
          await expect(result(page)).toContainText(op.operationId); expect(probeHost.count()).toBe(1);
          if (scenario === "revoked") {
            expect(op.code).toBe("FORBIDDEN");
            await options(page, false); await expect(card(page).getByRole("button", { name: "Observe connection", exact: true })).toBeDisabled();
          }
        });
      });
    }

    test.describe("changed host binding", () => {
      test.use({ probeScenario: "stale-binding" });
      test("typed predelegation refusal settles the first request without a provider call", async ({ page, probeHost }) => {
        await openLab(page, probeHost); await options(page);
        await keyboard(page, card(page).getByRole("button", { name: "Observe connection", exact: true }));
        await expect(requests(page).getByRole("alert")).toContainText("PROBE_BINDING_CHANGED");
        expect(probeHost.count()).toBe(0);
        expect(await page.evaluate((key) => JSON.parse(sessionStorage.getItem(key)!).pending, storageKey)).toBeNull();
        await options(page, false); await expect(card(page)).toContainText("PROBE_BINDING_CHANGED");
      });
    });
  });
}
