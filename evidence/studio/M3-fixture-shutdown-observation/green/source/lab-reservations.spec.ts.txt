import { test, expect, openLab, keyboard } from "./lab-fixture";
import type { Page } from "@playwright/test";

const card = (page: Page) => page.locator("section.panel").filter({ has: page.getByRole("heading", { name: "fixture:bench-sensor", exact: true }) });
const history = (page: Page) => page.getByRole("region", { name: "Reservation history", exact: true });
const record = (page: Page) => history(page).getByRole("article");
async function options(page: Page) {
  await keyboard(page, card(page).getByRole("button", { name: "Check reservation options", exact: true }));
  await expect(card(page).getByText("Lease service: configured · Evidence scope: fixture", { exact: true })).toBeVisible();
  await expect(card(page).getByRole("heading", { name: "Reservation eligibility", exact: true })).toBeFocused();
}
async function reserve(page: Page) {
  await options(page);
  await keyboard(page, card(page).getByRole("button", { name: "Reserve observe-only", exact: true }));
  await expect(record(page)).toHaveCount(1);
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test.describe(`lab reservations at ${viewport.width}`, () => {
    test.use({ viewport });
    test("a failed saved-request deletion reports the refusal and preserves explicit retry", async ({ page, labHost }) => {
      await page.addInitScript(() => {
        const remove = Storage.prototype.removeItem;
        Storage.prototype.removeItem = function (key) {
          if (key === "studio.lab.pending-request.v1") throw new Error("Owned storage deletion failure");
          return remove.call(this, key);
        };
        (window as any).restoreOwnedStorage = () => { Storage.prototype.removeItem = remove; };
      });
      const errors: string[] = [];
      page.on("pageerror", (error) => errors.push(error.message));
      await openLab(page, labHost);
      const pattern = "**/api/v1/assets/fixture:bench-sensor/reservations";
      await page.route(pattern, (route) => route.continue({ postData: JSON.stringify({ scope: "labelled-invalid-transport-scope" }) }));
      try {
        await options(page);
        await keyboard(page, card(page).getByRole("button", { name: "Reserve observe-only", exact: true }));
        await expect(page.getByRole("region", { name: "Reservation requests", exact: true })).toContainText("The saved request could not be cleared");
        await expect(page.getByRole("region", { name: "Reservation requests", exact: true })).toContainText("REQUEST_INVALID");
        expect(errors).toEqual([]);
        expect((await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items).toHaveLength(0);
        await page.evaluate(() => (window as any).restoreOwnedStorage());
        await page.unrouteAll({ behavior: "wait" });
        await keyboard(page, page.getByRole("button", { name: "Retry same reservation request", exact: true }));
        await expect(page.getByRole("region", { name: "Reservation requests", exact: true })).toContainText("completed");
        expect(errors).toEqual([]);
      } finally { await page.unrouteAll({ behavior: "wait" }); }
    });
    test("expired deadline removes renewal eligibility and explicit refresh retains terminal history", async ({ page, labHost }) => {
      await openLab(page, labHost);
      await options(page);
      await card(page).getByLabel("Reservation duration (seconds)", { exact: true }).fill("1");
      await keyboard(page, card(page).getByRole("button", { name: "Reserve observe-only", exact: true }));
      await expect(record(page)).toHaveCount(1);
      await expect(record(page)).toContainText("The observed deadline has passed");
      await expect(record(page).getByRole("button", { name: "Renew same scope", exact: true })).toBeDisabled();
      await keyboard(page, history(page).getByRole("button", { name: "Refresh reservations", exact: true }));
      await expect(record(page)).toContainText("expired");
      await expect(record(page).getByRole("button", { name: "Reconcile original ownership", exact: true })).toBeDisabled();
      const result = await (await page.request.get(labHost.origin + "/api/v1/reservations")).json();
      expect(result.items[0].status).toBe("expired");
    });

    test("ungranted scope is explicit and invalid option authority never enables reservation", async ({ page, labHost }) => {
      await openLab(page, labHost);
      await options(page);
      await card(page).getByLabel("Reservation scope", { exact: true }).selectOption("stimulate");
      await expect(card(page)).toContainText("This scope is unavailable: FORBIDDEN");
      await expect(card(page).getByRole("button", { name: "Reserve stimulate scope", exact: true })).toBeDisabled();
      const pattern = "**/api/v1/assets/fixture%3Abench-sensor/reservation-options";
      await page.route(pattern, async (route) => {
        const response = await route.fetch(), value = await response.json();
        value.runtimeAdmission = "ready";
        await route.fulfill({ response, json: value });
      });
      try {
        await keyboard(page, card(page).getByRole("button", { name: "Check reservation options", exact: true }));
        await expect(card(page).getByRole("alert")).toContainText("Reservation eligibility is unknown");
        await expect(card(page).getByRole("alert")).toBeFocused();
        await expect(card(page).getByRole("button", { name: "Reserve stimulate scope", exact: true })).toBeDisabled();
        expect((await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items).toHaveLength(0);
      } finally { await page.unrouteAll({ behavior: "wait" }); }
    });

    for (const status of [200, 503]) {
      test(`departed options ignore held actual response with labelled status ${status}`, async ({ page, labHost }) => {
        await openLab(page, labHost);
        let release!: () => void, fetched!: () => void;
        const held = new Promise<void>((resolve) => { release = resolve; }),
          observed = new Promise<void>((resolve) => { fetched = resolve; });
        const pattern = "**/api/v1/assets/fixture%3Abench-sensor/reservation-options";
        await page.route(pattern, async (route) => {
          const response = await route.fetch(), body = await response.text();
          expect(response.status()).toBe(200); fetched(); await held;
          await route.fulfill({ response, status, body: status === 200 ? body : JSON.stringify({ code: "FIXTURE_LATE_READ", message: "Labelled late transport failure." }) });
        });
        try {
          await keyboard(page, card(page).getByRole("button", { name: "Check reservation options", exact: true }));
          await observed;
          await keyboard(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
          release(); await page.unrouteAll({ behavior: "wait" });
          await expect(page.locator(".lab-page")).toHaveCount(0);
          await expect(page.getByRole("button", { name: "X-Verse Studio home", exact: true })).toBeFocused();
          await page.getByRole("button", { name: "Laboratory", exact: true }).click();
          await expect(card(page).getByRole("button", { name: "Reserve observe-only", exact: true })).toBeDisabled();
          await expect(page.getByRole("alert")).toHaveCount(0);
        } finally { release(); await page.unrouteAll({ behavior: "wait" }); }
      });
    }

    for (const target of ["moved focus", "labelled native dialog"]) {
      test(`options completion preserves ${target}`, async ({ page, labHost }) => {
        await openLab(page, labHost);
        let release!: () => void, fetched!: () => void;
        const held = new Promise<void>((resolve) => { release = resolve; }),
          observed = new Promise<void>((resolve) => { fetched = resolve; });
        await page.route("**/api/v1/assets/fixture%3Abench-sensor/reservation-options", async (route) => {
          const response = await route.fetch(), body = await response.text();
          fetched(); await held; await route.fulfill({ response, body });
        });
        try {
          await keyboard(page, card(page).getByRole("button", { name: "Check reservation options", exact: true }));
          await observed;
          const environment = page.getByRole("button", { name: "Environment", exact: true });
          if (target === "labelled native dialog") {
            // Explicit browser-only focus control: Environment navigates to Settings.
            // This native modal probes the guard; it is not a Studio feature or AT acceptance.
            await page.evaluate(() => {
              const dialog = document.createElement("dialog"), close = document.createElement("button");
              dialog.setAttribute("role", "dialog");
              dialog.setAttribute("aria-label", "Labelled native dialog guard control");
              close.textContent = "Close labelled dialog";
              close.addEventListener("click", () => dialog.remove());
              dialog.append(close); document.body.append(dialog); dialog.showModal(); close.focus();
            });
          }
          else {
            for (let i = 0; i < 200 && !(await environment.evaluate((n) => document.activeElement === n)); i++) await page.keyboard.press("Tab");
            await expect(environment).toBeFocused();
          }
          release(); await page.unrouteAll({ behavior: "wait" });
          await expect(card(page)).toContainText("Lease service: configured");
          if (target === "labelled native dialog") {
            await expect(page.getByRole("dialog")).toBeVisible();
            expect(await page.getByRole("dialog").evaluate((n) => n.contains(document.activeElement))).toBe(true);
            await page.keyboard.press("Enter");
            await expect(page.getByRole("dialog")).toHaveCount(0);
          } else await expect(environment).toBeFocused();
        } finally { release(); await page.unrouteAll({ behavior: "wait" }); }
      });
    }

    test("late mutation after Home retains original request for explicit recovery", async ({ page, labHost }) => {
      await openLab(page, labHost);
      let release!: () => void, fetched!: () => void, key = "", calls = 0;
      const held = new Promise<void>((resolve) => { release = resolve; }),
        observed = new Promise<void>((resolve) => { fetched = resolve; });
      await page.route("**/api/v1/assets/fixture:bench-sensor/reservations", async (route) => {
        calls++;
        const response = await route.fetch(), body = await response.text();
        expect(response.status()).toBe(202);
        if (calls === 1) { key = route.request().headers()["idempotency-key"]; fetched(); await held; }
        else expect(route.request().headers()["idempotency-key"]).toBe(key);
        await route.fulfill({ response, body });
      });
      try {
        await options(page);
        await keyboard(page, card(page).getByRole("button", { name: "Reserve observe-only", exact: true }));
        await observed;
        for (let i = 0; i < 3; i++) await page.keyboard.press("Enter");
        expect(calls).toBe(1);
        await keyboard(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
        release();
        await expect(page.locator(".lab-page")).toHaveCount(0);
        await expect(page.getByRole("button", { name: "X-Verse Studio home", exact: true })).toBeFocused();
        await page.getByRole("button", { name: "Laboratory", exact: true }).click();
        await keyboard(page, page.getByRole("button", { name: "Retry same reservation request", exact: true }));
        await expect(page.getByRole("region", { name: "Reservation requests", exact: true })).toContainText("completed");
        expect(calls).toBe(2);
        expect((await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items).toHaveLength(1);
      } finally { release(); await page.unrouteAll({ behavior: "wait" }); }
    });

    test("native keyboard reserve renew release preserves identity and runtime boundary", async ({ page, labHost }) => {
      await openLab(page, labHost);
      await expect(card(page).getByRole("button", { name: "Reserve observe-only", exact: true })).toBeDisabled();
      await reserve(page);
      const original = (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0];
      await expect(record(page)).toContainText("owned");
      await expect(record(page)).toContainText(original.fencingIdentity);
      await keyboard(page, record(page).getByRole("button", { name: "Renew same scope", exact: true }));
      await expect(record(page)).toContainText("owned");
      await expect.poll(async () => (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0].lastRenewal).not.toBeNull();
      const renewed = (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0];
      expect(renewed.reservationId).toBe(original.reservationId);
      expect(renewed.fencingIdentity).toBe(original.fencingIdentity);
      expect(renewed.expiry).toBeGreaterThan(original.expiry);
      await keyboard(page, record(page).getByRole("button", { name: "Release reservation", exact: true }));
      await expect(record(page)).toContainText("released");
      await expect(record(page).getByRole("button", { name: "Renew same scope", exact: true })).toBeDisabled();
      const caps = await (await page.request.get(labHost.origin + "/api/v1/capabilities")).json();
      expect(caps.labReservations.runtimeAdmission).toBe("unavailable");
      expect(caps.labReservations.physicalCommands).toEqual([]);
      expect(caps.labReservations.automaticRunRenewal).toBe(false);
      expect((await (await page.request.get(labHost.origin + "/api/v1/projects")).json()).items).toEqual([]);
      expect((await (await page.request.get(labHost.origin + "/api/v1/runs")).json()).items).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)).toBe(false);
    });

    test("refused retry and foreign receipt cannot erase an earlier unconfirmed operation", async ({ page, labHost }) => {
      await openLab(page, labHost);
      let key = "", attempts = 0;
      await page.route("**/api/v1/assets/fixture:bench-sensor/reservations", async (route) => {
        attempts++;
        const received = route.request().headers()["idempotency-key"];
        if (!key) key = received;
        expect(received).toBe(key);
        if (attempts === 2) {
          await route.fulfill({ status: 401, contentType: "application/json", json: { code: "FIXTURE_AUTH_REQUIRED", message: "Labelled refused retry." } });
        } else {
          const response = await route.fetch(), value = await response.json();
          expect(response.status()).toBe(202);
          if (attempts === 1) await route.abort("failed");
          else if (attempts === 3) await route.fulfill({ response, json: { ...value, principal: "another-fixture-operator" } });
          else await route.fulfill({ response, json: value });
        }
      });
      try {
        await options(page);
        await keyboard(page, card(page).getByRole("button", { name: "Reserve observe-only", exact: true }));
        const retry = page.getByRole("button", { name: "Retry same reservation request", exact: true });
        await expect(retry).toBeEnabled();
        await keyboard(page, retry);
        await expect(page.getByRole("region", { name: "Reservation requests", exact: true })).toContainText("FIXTURE_AUTH_REQUIRED");
        await expect(retry).toBeEnabled();
        await keyboard(page, retry);
        await expect(page.getByRole("region", { name: "Reservation requests", exact: true })).toContainText("belongs to another request");
        await expect(retry).toBeEnabled();
        await keyboard(page, retry);
        await expect(page.getByRole("region", { name: "Reservation requests", exact: true })).toContainText("completed");
        expect(attempts).toBe(4);
        expect((await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items).toHaveLength(1);
      } finally { await page.unrouteAll({ behavior: "wait" }); }
    });

    test.describe("local history pages", () => {
      test.use({ scenario: "history" });
      test("bounded independent pages preserve released ownership", async ({ page, labHost }) => {
        await openLab(page, labHost);
        await expect(record(page)).toHaveCount(50);
        await keyboard(page, history(page).getByRole("button", { name: "Next reservation page", exact: true }));
        await expect(record(page)).toHaveCount(1);
        await expect(history(page)).toContainText("Page 2 · 1 reservations");
        await expect(record(page)).toContainText("released");
        await expect(history(page).getByRole("button", { name: "Next reservation page", exact: true })).toBeDisabled();
        await keyboard(page, history(page).getByRole("button", { name: "Previous reservation page", exact: true }));
        await expect(record(page)).toHaveCount(50);
        await expect(history(page)).toContainText("Page 1 · 50 reservations");
        expect((await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items).toHaveLength(51);
      });
    });

    test("lost HTTP response retries the original accepted key after leaving and reopening", async ({ page, labHost }) => {
      await openLab(page, labHost);
      let firstKey = "", retries = 0;
      const pattern = "**/api/v1/assets/fixture:bench-sensor/reservations";
      await page.route(pattern, async (route) => {
        expect(route.request().method()).toBe("POST");
        const key = route.request().headers()["idempotency-key"];
        if (!firstKey) {
          firstKey = key;
          const accepted = await route.fetch();
          expect(accepted.status()).toBe(202);
          expect((await accepted.json()).status).toBe("completed");
          await route.abort("failed");
        } else {
          retries++;
          expect(key).toBe(firstKey);
          await route.continue();
        }
      });
      try {
        await options(page);
        await keyboard(page, card(page).getByRole("button", { name: "Reserve observe-only", exact: true }));
        await expect(page.getByText("The response is unconfirmed.", { exact: false })).toBeVisible();
        await expect(record(page)).toHaveCount(1);
        const original = (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0];
        await page.getByRole("button", { name: "X-Verse Studio home", exact: true }).click();
        await page.getByRole("button", { name: "Laboratory", exact: true }).click();
        await expect(history(page)).toContainText("Principal: local-operator");
        await keyboard(page, page.getByRole("button", { name: "Retry same reservation request", exact: true }));
        await expect(page.getByRole("region", { name: "Reservation requests", exact: true })).toContainText("completed");
        expect(retries).toBe(1);
        const current = (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items;
        expect(current).toHaveLength(1);
        expect(current[0].reservationId).toBe(original.reservationId);
        expect(current[0].fencingIdentity).toBe(original.fencingIdentity);
      } finally { await page.unrouteAll({ behavior: "wait" }); }
    });

    for (const scenario of ["reserve-unknown", "release-unknown", "revoked", "restart", "scopes"]) {
      test.describe(scenario, () => {
        test.use({ scenario });
        test("actual configured ownership and independent permission states", async ({ page, labHost }) => {
          await openLab(page, labHost);
          if (scenario === "restart") {
            await expect(record(page)).toContainText("Ownership is unknown");
            await expect(record(page).getByRole("button", { name: "Renew same scope", exact: true })).toBeDisabled();
            const before = (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0];
            await keyboard(page, record(page).getByRole("button", { name: "Reconcile original ownership", exact: true }));
            await expect(record(page)).toContainText("owned");
            const after = (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0];
            expect(after.reservationId).toBe(before.reservationId);
            expect(after.fencingIdentity).toBe(before.fencingIdentity);
          } else if (scenario === "scopes") {
            await options(page);
            const select = card(page).getByLabel("Reservation scope", { exact: true });
            await expect(select).toHaveValue("observe");
            await select.selectOption("destructive");
            await keyboard(page, card(page).getByRole("button", { name: "Reserve destructive scope", exact: true }));
            await expect(record(page)).toContainText("destructive");
            expect((await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0].scope).toBe("destructive");
          } else {
            await reserve(page);
            if (scenario === "release-unknown") {
              await keyboard(page, record(page).getByRole("button", { name: "Release reservation", exact: true }));
              await expect(record(page)).toContainText("Ownership is unknown");
            }
            if (scenario === "revoked") {
              await expect(record(page)).toContainText("owned");
              await expect(record(page).getByRole("button", { name: "Renew same scope", exact: true })).toBeDisabled();
              await expect(record(page).getByRole("button", { name: "Release reservation", exact: true })).toBeEnabled();
              await keyboard(page, record(page).getByRole("button", { name: "Release reservation", exact: true }));
              await expect(record(page)).toContainText("released");
            } else {
              await expect(record(page)).toContainText("Ownership is unknown");
              await expect(record(page).getByRole("button", { name: "Renew same scope", exact: true })).toBeDisabled();
              await expect(record(page).getByRole("button", { name: "Release reservation", exact: true })).toBeDisabled();
              if (scenario === "reserve-unknown") {
                await expect(record(page)).toContainText("Unknown");
                await keyboard(page, record(page).getByRole("button", { name: "Reconcile original ownership", exact: true }));
                await expect(record(page)).toContainText("Ownership is unknown");
              }
            }
          }
          await expect(page.getByRole("region", { name: "Reservation requests", exact: true })).toContainText("physical commands and automatic run renewal are unavailable");
        });
      });
    }
  });
}
