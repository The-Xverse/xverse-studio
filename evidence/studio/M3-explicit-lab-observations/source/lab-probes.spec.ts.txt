import { test, expect, openLab, keyboard } from "./lab-fixture";

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test.describe(`lab probes at ${viewport.width}`, () => {
    test.use({ viewport });
    test("lease installation alone shows explicit observation unavailable without contact", async ({ page, labHost }) => {
      await openLab(page, labHost);
      const card = page.locator("section.panel").filter({ has: page.getByRole("heading", { name: "fixture:bench-sensor", exact: true }) });
      const mutations: string[] = [];
      page.on("request", (request) => {
        if (request.method() !== "GET" && new URL(request.url()).pathname.endsWith("/probes")) mutations.push(request.url());
      });
      await keyboard(page, card.getByRole("button", { name: "Check connection options", exact: true }));
      await expect(card.getByRole("heading", { name: "Connection observation", exact: true })).toBeFocused();
      await expect(card).toContainText("PROBE_NOT_ADMITTED");
      await expect(card.getByRole("button", { name: "Observe connection", exact: true })).toBeDisabled();
      await expect(card).toContainText("Observation does not grant ownership or execution readiness.");
      expect(mutations).toEqual([]);
      const options = await page.request.get(labHost.origin + "/api/v1/assets/fixture%3Abench-sensor/probe-options");
      expect(options.status()).toBe(200);
      expect((await options.json()).allowed).toBe(false);
      expect((await (await page.request.get(labHost.origin + "/api/v1/reservations")).json()).items).toEqual([]);
      expect((await (await page.request.get(labHost.origin + "/api/v1/runs")).json()).items).toEqual([]);
    });
  });
}
