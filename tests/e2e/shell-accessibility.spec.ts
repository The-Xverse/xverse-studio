import { test, expect, type Locator, type Page } from "@playwright/test";
import { connectStudio } from "./connect-studio";
import { renderedContrast } from "./contrast";

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let step = 0; step < 160; step++) {
    if (await target.evaluate((node) => document.activeElement === node)) return;
    await page.keyboard.press("Tab");
  }
  throw new Error("Shell operation is unreachable through native Tab order");
}

async function activate(page: Page, target: Locator) {
  await tabTo(page, target);
  await page.keyboard.press("Enter");
}

type Pair = Awaited<ReturnType<typeof renderedContrast>>;
function checkPairs(pairs: Pair[]) {
  for (const pair of pairs) {
    expect.soft(pair.supported, pair.label).toBe(true);
    if (pair.supported) expect.soft(pair.ratio, pair.label).toBeGreaterThanOrEqual(4.5);
  }
}

test.afterEach(async ({ page }, testInfo) => {
  await testInfo.attach("native-browser-environment.json", {
    body: JSON.stringify({ platform: process.platform, architecture: process.arch,
      browser: await page.context().browser()?.version(), viewport: page.viewportSize(),
      scope: "Selected native browser semantics; no screen-reader or Windows claim" }),
    contentType: "application/json",
  });
});

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test(`shell accessibility: login instructions and real rejected-token recovery at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
    await page.setViewportSize(viewport);
    // Fresh browser context: no launcher secret is read or submitted in this journey.
    await page.goto("/");
    const panel = page.locator(".login-panel"), token = page.getByLabel("Bootstrap token", { exact: true });
    await expect(token).toBeVisible();
    const pairs = [
      await renderedContrast(panel.locator(":scope > p"), "Login instructions"),
      await renderedContrast(panel.locator("label"), "Bootstrap token label"),
      await renderedContrast(panel.locator(".login-help span"), "Local token handling help"),
      await renderedContrast(panel.getByRole("button", { name: "Open workspace", exact: true }), "Open workspace button"),
    ];
    await expect.soft(token).toHaveAccessibleDescription(/one-use bootstrap token/);
    await tabTo(page, token);
    await page.keyboard.insertText("owned-invalid-token-fixture");
    const rejected = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/v1/session" && response.request().method() === "POST");
    await activate(page, page.getByRole("button", { name: "Open workspace", exact: true }));
    expect((await rejected).status()).toBe(401);
    const error = panel.getByRole("alert");
    await expect(error).toBeVisible();
    await expect(token).toHaveValue("");
    await expect.soft(token).toHaveAttribute("aria-invalid", "true");
    await expect.soft(token).toHaveAccessibleDescription(/bootstrap token.*invalid|invalid.*bootstrap token/i);
    const rejectedState = { description: await token.getAttribute("aria-describedby"),
      invalid: await token.getAttribute("aria-invalid"), error: await error.innerText() };
    pairs.push(await renderedContrast(error, "Rejected-token error text"));
    await tabTo(page, token);
    await expect(token).toBeFocused();
    await page.keyboard.insertText("replacement-fixture");
    await expect(token).toHaveAttribute("aria-invalid", "false");
    await expect(error).toHaveCount(0);
    await expect(token).toHaveAccessibleDescription(/one-use bootstrap token/);
    await page.keyboard.press("ControlOrMeta+A");
    await page.keyboard.press("Backspace");
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)).toBe(false);
    // Empty password field only: no private bootstrap/cookie values in evidence.
    await testInfo.attach("login-semantics.json", { body: JSON.stringify({ viewport,
      rejectedHTTP: 401, submittedFixture: "invalid synthetic token", clearedPassword: true,
      inputName: "Bootstrap token", rejectedState,
      recoveredState: { description: await token.getAttribute("aria-describedby"), invalid: await token.getAttribute("aria-invalid") },
      keyboardRecovery: true, staleErrorClearedOnEditing: true, measurements: pairs }), contentType: "application/json" });
    checkPairs(pairs);
  });

  test(`shell accessibility: navigation state, form and real busy response at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
    test.setTimeout(90000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    await activate(page, page.getByRole("button", { name: "X-Verse Studio home", exact: true }));
    const rail = page.locator(".rail"), pairs: Pair[] = [];
    await expect.soft(page.getByRole("navigation", { name: "Main navigation", exact: true })).toHaveCount(1);
    for (const name of ["Workspace", "Catalog", "Laboratory", "Compatibility and environment"]) {
      const button = rail.getByRole("button", { name, exact: true });
      pairs.push(await renderedContrast(button.locator("span"), `Navigation ${name}`));
    }
    await expect.soft(rail.getByRole("button", { name: "Workspace", exact: true })).toHaveAttribute("aria-current", "page");
    await activate(page, rail.getByRole("button", { name: "Catalog", exact: true }));
    await expect.soft(rail.getByRole("button", { name: "Catalog", exact: true })).toHaveAttribute("aria-current", "page");
    await expect.soft(rail.locator('[aria-current="page"]')).toHaveCount(1);
    pairs.push(await renderedContrast(rail.getByRole("button", { name: "Catalog", exact: true }).locator("span"), "Selected Catalog navigation"));
    for (const name of ["Laboratory", "Compatibility and environment"]) {
      const destination = rail.getByRole("button", { name, exact: true });
      await activate(page, destination);
      await expect(destination).toHaveAttribute("aria-current", "page");
      await expect(rail.locator('[aria-current="page"]')).toHaveCount(1);
      await expect(destination).toBeFocused();
      const focus = await destination.evaluate((node) => {
        const style = getComputedStyle(node), rect = node.getBoundingClientRect();
        return { outline: style.outlineStyle, width: parseFloat(style.outlineWidth),
          rect: rect.toJSON(), viewport: { width: innerWidth, height: innerHeight } };
      });
      await testInfo.attach(`navigation-focus-${name}.json`, { body: JSON.stringify(focus), contentType: "application/json" });
      expect(focus.outline).not.toBe("none");
      expect(focus.width).toBeGreaterThanOrEqual(2);
      expect(focus.rect.left).toBeGreaterThanOrEqual(0);
      expect(focus.rect.top).toBeGreaterThanOrEqual(0);
      expect(focus.rect.right).toBeLessThanOrEqual(viewport.width);
      expect(focus.rect.bottom).toBeLessThanOrEqual(viewport.height);
    }
    await activate(page, rail.getByRole("button", { name: "Workspace", exact: true }));
    const newProject = page.getByRole("button", { name: "New project", exact: true });
    await activate(page, newProject);
    const dialog = page.getByRole("dialog", { name: "Create a System workspace", exact: true });
    await expect(dialog).toBeVisible();
    const input = dialog.getByRole("textbox", { name: "Project name", exact: true });
    await expect(input).toHaveAccessibleName("Project name");
    pairs.push(await renderedContrast(input.locator("xpath=.."), "Project name label"));
    await tabTo(page, input);
    await page.keyboard.insertText(`Keyboard shell ${viewport.width}`);
    await page.keyboard.press("Escape");
    await expect(newProject).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(dialog).toBeVisible();
    let release!: () => void;
    const held = new Promise<void>((resolve) => { release = resolve; });
    let prepared = false, routeFinished: Promise<void> | undefined;
    await page.route("**/api/v1/projects", async (route) => {
      if (route.request().method() !== "POST") return route.continue();
      let finish!: () => void;
      routeFinished = new Promise<void>((resolve) => { finish = resolve; });
      try {
        const response = await route.fetch();
        prepared = true;
        await held;
        await route.fulfill({ response });
      } finally { finish(); }
    });
    try {
      await activate(page, dialog.getByRole("button", { name: "Create project", exact: true }));
      await expect.poll(() => prepared).toBe(true);
      const busy = page.locator(".alerts[aria-live=polite] .notice.busy");
      await expect(busy).toContainText("Creating project");
      pairs.push(await renderedContrast(busy, "Creating project busy notice"));
      const submitted = page.waitForResponse((response) => new URL(response.url()).pathname === "/api/v1/projects" && response.request().method() === "POST");
      release();
      const response = await submitted;
      expect(response.status()).toBe(201);
      const created = await response.json();
      await expect.poll(() => page.evaluate(() => localStorage.getItem("studio.projectId"))).toBe(created.projectId);
      await expect(dialog).toHaveCount(0);
      await expect(page.locator(".notice.busy")).toHaveCount(0);
    } finally { release(); if (routeFinished) await routeFinished; await page.unroute("**/api/v1/projects"); }
    expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)).toBe(false);
    await testInfo.attach("shell-semantics.json", { body: JSON.stringify({ viewport,
      navigationLandmark: await rail.getAttribute("role") || await rail.evaluate((el) => el.tagName),
      navigationSnapshot: await rail.ariaSnapshot(), realProjectCreation: true,
      busyResponseHeldForObservation: true, liveRegion: "polite", keyboardModalReturn: true,
      measurements: pairs, limitations: ["Browser accessibility semantics, not actual assistive-technology execution"] }), contentType: "application/json" });
    checkPairs(pairs);
  });
}
