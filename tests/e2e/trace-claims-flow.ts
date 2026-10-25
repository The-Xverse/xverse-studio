import { expect, type Page } from "@playwright/test";
export async function traceApi(
  page: Page,
  path: string,
  method = "GET",
  body?: unknown,
  revision?: number,
) {
  return page.evaluate(
    async ({ path, method, body, revision }) => {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (method !== "GET") {
        const session = await fetch("/api/v1/session").then((r) => r.json());
        headers["X-CSRF-Token"] = session.csrfToken;
      }
      if (revision !== undefined) headers["If-Match"] = String(revision);
      if (method !== "GET") headers["Idempotency-Key"] = crypto.randomUUID();
      const response = await fetch("/api/v1" + path, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      return { status: response.status, body: await response.json() };
    },
    { path, method, body, revision },
  );
}
export async function inspectTraceForm(page: Page) {
  await page.getByRole("tab", { name: "Annotations", exact: true }).click();
  await page
    .getByRole("button", { name: "Add external reference", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByLabel("Requirement or test URI", { exact: true }),
  ).toBeFocused();
  await expect(
    page.getByRole("group", {
      name: "Frozen model and Scenario references",
      exact: true,
    }),
  ).toBeVisible();
}
