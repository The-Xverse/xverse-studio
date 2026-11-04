import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "../e2e/connect-studio";

test("Actual Autoverse evidence imports preserve original claims and expose current integrity without admission", async ({ page }, info) => {
  const data = process.env.STUDIO_BROWSER_DATA!;
  const recorded = JSON.parse(readFileSync(path.join(data, "exchange-recording.private.json"), "utf8"));
  await connectStudio(page, info);
  await page.getByRole("button", { name: "X-Verse Studio home", exact: true }).click();
  for (const width of [1024, 1440]) {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    for (const [file, currentIntegrity] of [["evidence-valid.zip", "unavailable"], ["evidence-damaged.zip", "invalid"]]) {
      const response = page.waitForResponse((r) => r.url().endsWith("/api/v1/evidence/imports") && r.request().method() === "POST");
      await page.getByLabel("Import evidence archive", { exact: true }).setInputFiles(path.join(data, file));
      expect((await response).status()).toBe(201);
      const dialog = page.getByRole("dialog", { name: "Imported evidence inspection", exact: true });
      await expect(dialog).toBeVisible();
      const current = dialog.getByRole("region", { name: "Current imported evidence inspection", exact: true });
      const original = dialog.getByRole("region", { name: "Original imported evidence report", exact: true });
      await expect(current).toContainText(recorded.sourceRunId);
      await expect(current).toContainText(recorded.sourceSnapshotId);
      await expect(current.locator(".key-values > div").filter({ has: page.locator("dt", { hasText: /^Current integrity$/ }) })).toContainText(currentIntegrity);
      await expect(original.locator(".key-values > div").filter({ has: page.locator("dt", { hasText: /^Reported integrity$/ }) })).toContainText("valid");
      await expect(original).toContainText("available");
      await expect(original).toContainText("external_demo");
      await expect(dialog).toContainText("Import creates no run and grants no execution authority");
      await expect(dialog).toContainText("6 recorded evaluations and 2 annotations");
      if (currentIntegrity === "invalid") {
        await dialog.evaluate((element) => { element.scrollTop = 0; });
        await dialog.screenshot({ path: info.outputPath(`actual-exchange-state-${width}.png`) });
      }
      const dependencies = dialog.getByRole("region", { name: "Referenced dependencies", exact: true });
      await expect(dependencies).toContainText("Not included");
      await expect(dependencies).toContainText("not included, fetched or installed");
      const identity = dependencies.getByText("Inspect provider identity", { exact: true });
      await identity.focus(); await page.keyboard.press("Enter");
      await expect(dependencies).toContainText(recorded.installationDigest);
      await expect(identity).toBeFocused();
      const profile = dependencies.getByText("Inspect profile identity", { exact: true }).first();
      await profile.focus(); await page.keyboard.press("Enter");
      await expect(dependencies).toContainText(recorded.compiledProfileDigest);
      await expect(profile).toBeFocused();
      if (currentIntegrity === "invalid") {
        await expect(dialog).toContainText("ORIGINAL_JOURNAL_INVALID");
        await dialog.screenshot({ path: info.outputPath(`actual-exchange-dependencies-${width}.png`) });
      }
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await dialog.getByRole("button", { name: "Close dialog", exact: true }).click();
    }
  }
});
