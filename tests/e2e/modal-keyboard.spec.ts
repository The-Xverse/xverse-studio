import { test, expect, type Page, type TestInfo } from "@playwright/test";
import { connectStudio } from "./connect-studio";

type EarlyEscape = {
  title: string;
  fired: boolean;
  mounted: boolean;
  prevented: boolean;
  activeElement: string | null;
};

async function armEarlyEscape(page: Page, title: string) {
  await page.evaluate((expectedTitle) => {
    const state = {
      title: expectedTitle,
      fired: false,
      mounted: false,
      prevented: false,
      activeElement: null as string | null,
    };
    (window as unknown as { earlyModalEscape: typeof state }).earlyModalEscape =
      state;
    const observer = new MutationObserver(() => {
      const dialog = Array.from(
        document.querySelectorAll('[role="dialog"]'),
      ).find((node) => node.getAttribute("aria-label") === expectedTitle);
      if (!dialog || state.fired) return;
      observer.disconnect();
      queueMicrotask(() => {
        state.mounted = dialog.isConnected;
        state.activeElement = document.activeElement?.tagName || null;
        const escape = new KeyboardEvent("keydown", {
          key: "Escape",
          code: "Escape",
          bubbles: true,
          cancelable: true,
        });
        // Deliberate earliest post-mount input in actual Chromium. No listener
        // replacement, application patch, mocked modal or fixed timing delay.
        dialog.dispatchEvent(escape);
        state.prevented = escape.defaultPrevented;
        state.fired = true;
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }, title);
}

async function observedEscape(
  page: Page,
  testInfo: TestInfo,
): Promise<EarlyEscape> {
  await expect
    .poll(() =>
      page.evaluate(
        () =>
          (window as unknown as { earlyModalEscape: EarlyEscape })
            .earlyModalEscape?.fired,
      ),
    )
    .toBe(true);
  const observation = await page.evaluate(
    () =>
      (window as unknown as { earlyModalEscape: EarlyEscape }).earlyModalEscape,
  );
  await testInfo.attach("early-escape-observation", {
    body: JSON.stringify(observation, null, 2),
    contentType: "application/json",
  });
  expect(observation.mounted).toBe(true);
  return observation;
}

test("modal early keyboard: New dialog handles Escape immediately after mount", async ({
  page,
}, testInfo) => {
  await connectStudio(page, testInfo);
  const trigger = page.getByRole("button", {
    name: "New project",
    exact: true,
  });
  await trigger.focus();
  await armEarlyEscape(page, "Create a System workspace");
  await trigger.click();
  const observation = await observedEscape(page, testInfo);
  await expect(
    page.getByRole("dialog", { name: "Create a System workspace" }),
  ).toHaveCount(0);
  expect(observation.prevented).toBe(true);
  await expect(trigger).toBeFocused();
});

test("modal early keyboard: async Preflight dialog handles Escape immediately after mount", async ({
  page,
}, testInfo) => {
  const starts: string[] = [];
  page.on("request", (request) => {
    if (
      request.method() === "POST" &&
      /\/api\/v1\/runs$/.test(new URL(request.url()).pathname)
    )
      starts.push(request.url());
  });
  await connectStudio(page, testInfo);
  await page
    .locator(".example-grid")
    .getByRole("button", { name: /Process control reference/ })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Process control reference",
      exact: true,
    }),
  ).toBeVisible();
  const trigger = page.getByRole("button", {
    name: "Preflight & run",
    exact: true,
  });
  await trigger.focus();
  await armEarlyEscape(page, "Execution preflight");
  await trigger.click();
  const observation = await observedEscape(page, testInfo);
  await expect(
    page.getByRole("dialog", { name: "Execution preflight" }),
  ).toHaveCount(0);
  expect(observation.prevented).toBe(true);
  await expect(trigger).toBeFocused();
  expect(starts).toEqual([]);
});
