# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: lab-inventory-accessibility.spec.ts >> lab inventory: maximum Unicode metadata remains observable at 1440x900
- Location: tests/e2e/lab-inventory-accessibility.spec.ts:24:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.lab-page').locator('section.panel').filter({ has: getByRole('heading', { name: 'urn:fixture:inventory-presentation', exact: true }) })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "soft toBeVisible" locator('.lab-page').locator('section.panel').filter({ has: getByRole('heading', { name: 'urn:fixture:inventory-presentation', exact: true }) }) with timeout 10000ms
  - waiting for locator('.lab-page').locator('section.panel').filter({ has: getByRole('heading', { name: 'urn:fixture:inventory-presentation', exact: true }) })

```

```yaml
- link "Skip to workspace":
  - /url: "#main-content"
- banner:
  - button "X-Verse Studio home": X X-VERSE STUDIO
  - text: Local workspace REFERENCE PREVIEW
  - button "Environment"
  - text: LO
- navigation "Main navigation":
  - button "Workspace"
  - button "Catalog"
  - button "Laboratory": Lab
  - button "Compatibility and environment": Settings
  - text: v0.1
- main:
  - text: HYBRID LABORATORY
  - heading "Physical assets" [level=1]
  - paragraph: Inspect identity and metadata from registered provider observations.
  - button "Refresh inventory"
  - heading "No physical provider admitted" [level=2]
  - paragraph: Inventory is read-only. Reservations and active operations are unavailable until a physical provider with durable ownership and permitted actions is admitted. Declared capabilities and observed availability do not grant permission.
  - text: Observe-only is the default. No device scanning, flashing, reset, or physical stimulation is implied by opening this view.
  - region "Inventory observation":
    - heading "Inventory observation" [level=2]
    - paragraph: Refresh starts a new observation at the first page. Each page is a separate read; the inventory may change between requests. Provider OS declarations and fixture scope are separate from active-operation readiness.
    - alert: Inventory availability is unknown. The public inventory observation is incomplete, malformed or unsupported. Refresh inventory to retry.
  - heading "Provider capability boundaries" [level=2]
  - heading "Studio executable reference" [level=3]
  - text: owned_reference
  - paragraph: Inspect the descriptor for supported operations and host compatibility.
  - group: Inspect exact data
  - heading "X-Verse Lite / CARLA" [level=3]
  - text: unavailable
  - paragraph: Inspect the descriptor for supported operations and host compatibility.
  - group: Inspect exact data
```

# Test source

```ts
  1   | import {
  2   |   test,
  3   |   expect,
  4   |   type Page,
  5   |   type Locator,
  6   |   type TestInfo,
  7   | } from "@playwright/test";
  8   | import { readFileSync } from "node:fs";
  9   | import path from "node:path";
  10  | import { connectStudio } from "./connect-studio";
  11  | import { renderedContrast } from "./contrast";
  12  |
  13  | const observations = JSON.parse(
  14  |   readFileSync(
  15  |     path.resolve("tests/fixtures/providers/lab-inventory-observation.json"),
  16  |     "utf8",
  17  |   ),
  18  | );
  19  |
  20  | for (const viewport of [
  21  |   { width: 1024, height: 768 },
  22  |   { width: 1440, height: 900 },
  23  | ]) {
  24  |   test(`lab inventory: maximum Unicode metadata remains observable at ${viewport.width}x${viewport.height}`, async ({
  25  |     page,
  26  |   }, info) => {
  27  |     const finish = await begin(page, info, viewport),
  28  |       value = observations.unicode;
  29  |     expect(Array.from(value.items[0].firmware.version)).toHaveLength(256);
  30  |     expect(value.items[0].firmware.version).toHaveLength(512);
  31  |     await page.route(assetPattern, (route) =>
  32  |       route.fulfill({
  33  |         status: 200,
  34  |         contentType: "application/json",
  35  |         body: JSON.stringify(value),
  36  |       }),
  37  |     );
  38  |     await openLab(page);
  39  |     const card = assetCard(page);
> 40  |     await expect.soft(card).toBeVisible();
      |                             ^ Error: expect(locator).toBeVisible() failed
  41  |     if (await card.count()) {
  42  |       await expect(field(card, "Firmware")).toHaveText(
  43  |         `Observed · ${value.items[0].firmware.version}`,
  44  |       );
  45  |       await expect(field(card, "Observed identity")).toContainText(
  46  |         value.items[0].identity.model,
  47  |       );
  48  |       await expect(
  49  |         card.getByRole("button", { name: "Reserve observe-only", exact: true }),
  50  |       ).toBeDisabled();
  51  |     }
  52  |     expect(
  53  |       await page.evaluate(
  54  |         () => document.documentElement.scrollWidth > innerWidth + 1,
  55  |       ),
  56  |     ).toBe(false);
  57  |     await finish({
  58  |       labelledBackendProjectionFixture: true,
  59  |       unicodeCodePoints: 256,
  60  |       utf16CodeUnits: 512,
  61  |       renderedCards: await card.count(),
  62  |     });
  63  |   });
  64  | }
  65  |
  66  | for (const viewport of [
  67  |   { width: 1024, height: 768 },
  68  |   { width: 1440, height: 900 },
  69  | ]) {
  70  |   test(`lab inventory: missing physical declaration stays unknown at ${viewport.width}x${viewport.height}`, async ({
  71  |     page,
  72  |   }, info) => {
  73  |     const finish = await begin(page, info, viewport);
  74  |     expect(observations.unclassifiedSource.physicalPropertyPresent).toBe(false);
  75  |     expect(observations.unclassified.items[0].physical).toBe(false);
  76  |     await page.route(assetPattern, (route) =>
  77  |       route.fulfill({
  78  |         status: 200,
  79  |         contentType: "application/json",
  80  |         body: JSON.stringify(observations.unclassified),
  81  |       }),
  82  |     );
  83  |     await openLab(page);
  84  |     const card = assetCard(page);
  85  |     await expect(card).toBeVisible();
  86  |     await expect.soft(card).toContainText("Not confirmed physical");
  87  |     await expect(
  88  |       card.getByRole("button", { name: "Reserve observe-only", exact: true }),
  89  |     ).toBeDisabled();
  90  |     await finish({
  91  |       omittedPhysicalSource: true,
  92  |       normalizedPhysicalFlag: false,
  93  |       labelledBackendProjectionFixture: true,
  94  |     });
  95  |   });
  96  | }
  97  |
  98  | async function tabTo(page: Page, target: Locator) {
  99  |   await expect(target).toBeVisible();
  100 |   for (const [key, limit] of [
  101 |     ["Shift+Tab", 40],
  102 |     ["Tab", 220],
  103 |   ] as const) {
  104 |     for (let i = 0; i < limit; i++) {
  105 |       if (await target.evaluate((n) => document.activeElement === n)) return;
  106 |       await page.keyboard.press(key);
  107 |     }
  108 |   }
  109 |   await expect(target).toBeFocused();
  110 | }
  111 |
  112 | const lab = (page: Page) => page.locator(".lab-page");
  113 | const refresh = (page: Page) =>
  114 |   lab(page).getByRole("button", { name: "Refresh inventory", exact: true });
  115 | const observationHeading = (page: Page) =>
  116 |   lab(page).getByRole("heading", {
  117 |     name: "Inventory observation",
  118 |     exact: true,
  119 |   });
  120 | const nextPage = (page: Page) =>
  121 |   lab(page).getByRole("button", { name: "Next inventory page", exact: true });
  122 | const previousPage = (page: Page) =>
  123 |   lab(page).getByRole("button", {
  124 |     name: "Previous inventory page",
  125 |     exact: true,
  126 |   });
  127 | const assetCard = (page: Page, id = "urn:fixture:inventory-presentation") =>
  128 |   lab(page)
  129 |     .locator("section.panel")
  130 |     .filter({ has: page.getByRole("heading", { name: id, exact: true }) });
  131 | const field = (card: Locator, name: string) =>
  132 |   card
  133 |     .locator(".key-values > div")
  134 |     .filter({ has: card.page().getByText(name, { exact: true }) })
  135 |     .locator("dd");
  136 | const assetPattern = "**/api/v1/assets*";
  137 |
  138 | async function begin(
  139 |   page: Page,
  140 |   info: TestInfo,
```
