# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: probe.spec.ts >> actual rerun acknowledgement preserves a newer Model view at 1440
- Location: .studio-local/frozen-rerun-review/probe.spec.ts:6:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: 'Connect to Studio', exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('heading', { name: 'Connect to Studio', exact: true }) with timeout 10000ms
  - waiting for getByRole('heading', { name: 'Connect to Studio', exact: true })

```

```yaml
- text: "{\"code\":\"NOT_FOUND\",\"message\":\"Build the frontend with npm run build before launching Studio.\",\"requestId\":\"req-eb6d98e9-35f2-427e-90f7-a60bf23c53a4\",\"retryable\":false}"
```

# Test source

```ts
  1  | import { expect, type Page, type TestInfo } from "@playwright/test";
  2  | import { existsSync, readFileSync, writeFileSync } from "node:fs";
  3  | import path from "node:path";
  4  | /** Private launcher data only; no authentication state goes in test reports or exports. */
  5  | export async function connectStudio(page: Page, testInfo: TestInfo) {
  6  |   const data =
  7  |       process.env.STUDIO_BROWSER_DATA || path.resolve("test-results/backend"),
  8  |     session = path.join(data, "browser-session.private.json");
  9  |   if (existsSync(session)) {
  10 |     const state = JSON.parse(readFileSync(session, "utf8"));
  11 |     await page.context().addCookies(state.cookies);
  12 |   }
  13 |   await page.goto("/");
  14 |   if (!existsSync(session)) {
  15 |     await expect(
  16 |       page.getByRole("heading", { name: "Connect to Studio", exact: true }),
> 17 |     ).toBeVisible();
     |       ^ Error: expect(locator).toBeVisible() failed
  18 |     await page.screenshot({
  19 |       path: testInfo.outputPath("login.png"),
  20 |       fullPage: true,
  21 |     });
  22 |     const bootstrap = JSON.parse(
  23 |       readFileSync(path.join(data, "bootstrap.json"), "utf8"),
  24 |     );
  25 |     await page.getByLabel("Bootstrap token").fill(bootstrap.bootstrapToken);
  26 |     await page
  27 |       .getByRole("button", { name: "Open workspace", exact: true })
  28 |       .click();
  29 |     await expect(
  30 |       page.getByRole("heading", { name: "Start with an example", exact: true }),
  31 |     ).toBeVisible();
  32 |     writeFileSync(
  33 |       session,
  34 |       JSON.stringify(await page.context().storageState()),
  35 |       { mode: 0o600 },
  36 |     );
  37 |   }
  38 |   await expect(
  39 |     page.getByRole("button", { name: "X-Verse Studio home", exact: true }),
  40 |   ).toBeVisible();
  41 | }
  42 |
```
