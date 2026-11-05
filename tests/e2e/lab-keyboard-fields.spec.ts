import { test, expect, openLab, keyboard } from "./lab-fixture";
import type { Locator, Page } from "@playwright/test";
import { renderedContrast } from "./contrast";

async function tabTo(page: Page, target: Locator) {
  for (let i = 0; i < 200; i++) {
    if (await target.evaluate(n => n === document.activeElement)) {
      expect(await target.evaluate(n => {
        const r = n.getBoundingClientRect(), s = getComputedStyle(n);
        return r.left >= 0 && r.right <= innerWidth + 1 && r.top >= 0 && r.bottom <= innerHeight + 1 &&
          s.outlineStyle !== "none" && parseFloat(s.outlineWidth) >= 2;
      })).toBe(true);
      return;
    }
    await page.keyboard.press("Tab");
  }
  throw Error("Required labelled lab field is unreachable through native Tab order");
}
async function number(page: Page, label: string, value: string) {
  const input = page.getByLabel(label, { exact: true });
  await tabTo(page, input);
  await page.keyboard.press("ControlOrMeta+A");
  await page.keyboard.insertText(value);
  await expect(input).toHaveValue(value);
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test.describe(`lab native field entry at ${viewport.width}`, () => {
    test.use({ viewport });
    test("labelled duration constraints and scope support keyboard reserve renew release", async ({ page, labHost }, info) => {
      await openLab(page, labHost);
      const card = page.locator("section.panel").filter({ has: page.getByRole("heading", { name: "fixture:bench-sensor", exact: true }) });
      const mutations: { method: string; path: string; body: unknown }[] = [];
      page.on("request", r => { if (!["GET", "HEAD"].includes(r.method())) mutations.push({
        method: r.method(), path: new URL(r.url()).pathname, body: r.postData() ? r.postDataJSON() : null,
      }); });
      await keyboard(page, card.getByRole("button", { name: "Check reservation options", exact: true }));
      await expect(card).toContainText("Lease service: configured · Evidence scope: fixture");
      const scope = card.getByLabel("Reservation scope", { exact: true });
      await tabTo(page, scope);
      await page.keyboard.press("Home");
      await page.keyboard.press("Tab");
      await expect(scope).toHaveValue("observe");
      await number(page, "Reservation duration (seconds)", "0");
      await expect(card.getByRole("button", { name: "Reserve observe-only", exact: true })).toBeDisabled();
      expect(mutations).toEqual([]);
      await number(page, "Reservation duration (seconds)", "60");
      const contrast = await renderedContrast(page.getByText("Reservation duration (seconds)", { exact: true }), "Reservation duration label and units");
      expect(contrast.supported).toBe(true);
      if (contrast.supported) expect(contrast.ratio).toBeGreaterThanOrEqual(4.5);
      await keyboard(page, card.getByRole("button", { name: "Reserve observe-only", exact: true }));
      const history = page.getByRole("region", { name: "Reservation history", exact: true }), row = history.getByRole("article");
      await expect(row).toContainText("owned");
      const original = (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0];
      expect(original.scope).toBe("observe");
      await number(page, "Renewal duration (seconds)", "90");
      await keyboard(page, row.getByRole("button", { name: "Renew same scope", exact: true }));
      await expect.poll(async () => (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0].lastRenewal).not.toBeNull();
      const renewed = (await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items[0];
      expect(renewed.reservationId).toBe(original.reservationId);
      expect(renewed.fencingIdentity).toBe(original.fencingIdentity);
      expect(renewed.expiry).toBeGreaterThan(original.expiry);
      await keyboard(page, row.getByRole("button", { name: "Release reservation", exact: true }));
      await expect(row).toContainText("released");
      await expect(row).toContainText("Physical state remains unknown");
      expect(mutations.map(r => r.method)).toEqual(["POST", "POST", "DELETE"]);
      expect(mutations[0].body).toEqual({ scope: "observe", durationSeconds: 60 });
      expect(mutations[1].body).toEqual({ fencingIdentity: original.fencingIdentity, durationSeconds: 90 });
      expect((await (await page.request.get(labHost.origin + "/api/v1/runs")).json()).items).toEqual([]);
      expect((await (await page.request.get(labHost.origin + "/api/v1/projects")).json()).items).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      await info.attach("lab-native-fields", { body: JSON.stringify({ viewport, mutations, contrast,
        scope: "Native keyboard over owned in-memory lease callbacks only; no equipment, runtime admission or assistive-technology certification",
      }), contentType: "application/json" });
    });
  });
}
