import { test, expect } from "@playwright/test";
import { connectStudio } from "./connect-studio";

test("native window instructions replace browser driving controls", async ({ page }, info) => {
  await connectStudio(page, info);
  // Presentation fixture only: the separate native check proves the actual window.
  await page.route("**/api/v1/runs/*", async (route) => {
    if (route.request().method() !== "GET") return route.continue();
    const response = await route.fetch();
    const run = await response.json();
    if (!run.runId) return route.fulfill({ response });
    await route.fulfill({ response, json: { ...run, inputSurface: {
      kind: "native-window", version: "1.0", title: "Vehicle Manual Control",
      instructions: "Focus the Pygame window on the Studio host. W: throttle; C: cruise.",
      companionUrl: "https://localhost:8443",
    } } });
  });
  await page.locator(".example-grid").getByRole("button").first().click();
  await page.getByRole("button", { name: "Preflight & run", exact: true }).click();
  await page.getByRole("button", { name: "Start frozen snapshot", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Vehicle Manual Control", exact: true })).toBeVisible();
  await expect(page.locator(".native-window-controls")).toContainText("Focus the Pygame window");
  await expect(page.getByRole("button", { name: "Open driving controls", exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Android digital cluster", exact: true })).toHaveAttribute("href", "https://localhost:8443");
  await page.getByRole("region", { name: "Run controls", exact: true }).getByRole("button", { name: "Stop", exact: true }).click();
});
