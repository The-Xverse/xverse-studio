import { expect, type Page, type TestInfo } from "@playwright/test";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
/** Private launcher data only; no authentication state goes in test reports or exports. */
export async function connectStudio(page: Page, testInfo: TestInfo) {
  const data =
      process.env.STUDIO_BROWSER_DATA || path.resolve("test-results/backend"),
    session = path.join(data, "browser-session.private.json");
  if (existsSync(session)) {
    const state = JSON.parse(readFileSync(session, "utf8"));
    await page.context().addCookies(state.cookies);
  }
  await page.goto("/");
  if (!existsSync(session)) {
    await expect(
      page.getByRole("heading", { name: "Connect to Studio", exact: true }),
    ).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath("login.png"),
      fullPage: true,
    });
    const bootstrap = JSON.parse(
      readFileSync(path.join(data, "bootstrap.json"), "utf8"),
    );
    await page.getByLabel("Bootstrap token").fill(bootstrap.bootstrapToken);
    await page
      .getByRole("button", { name: "Open workspace", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Start with an example", exact: true }),
    ).toBeVisible();
    writeFileSync(
      session,
      JSON.stringify(await page.context().storageState()),
      { mode: 0o600 },
    );
  }
  await expect(
    page.getByRole("button", { name: "X-Verse Studio home", exact: true }),
  ).toBeVisible();
}
