# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: lab-inventory-accessibility.spec.ts >> lab inventory: observed public observation at 1024x768
- Location: tests/e2e/lab-inventory-accessibility.spec.ts:43:9

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('section.panel').filter({ has: getByRole('heading', { name: 'urn:fixture:inventory-presentation', exact: true }) }).locator('.key-values > div').filter({ has: getByText('Firmware', { exact: true }) }).locator('dd')
Expected substring: "fixture-1.2.3"
Received string:    "Unknown"
Timeout: 10000ms

Call log:
  - Expect "soft toContainText" locator('section.panel').filter({ has: getByRole('heading', { name: 'urn:fixture:inventory-presentation', exact: true }) }).locator('.key-values > div').filter({ has: getByText('Firmware', { exact: true }) }).locator('dd') with timeout 10000ms
  - waiting for locator('section.panel').filter({ has: getByRole('heading', { name: 'urn:fixture:inventory-presentation', exact: true }) }).locator('.key-values > div').filter({ has: getByText('Firmware', { exact: true }) }).locator('dd')
    24 × locator resolved to <dd>Unknown</dd>
       - unexpected value "Unknown"

```

```yaml
- definition: Unknown
```

# Test source

```ts
  5   |
  6   | const observations = JSON.parse(
  7   |   readFileSync(
  8   |     path.resolve("tests/fixtures/providers/lab-inventory-observation.json"),
  9   |     "utf8",
  10  |   ),
  11  | );
  12  |
  13  | async function tabTo(page: Page, target: Locator) {
  14  |   await expect(target).toBeVisible();
  15  |   for (const [key, limit] of [
  16  |     ["Shift+Tab", 40],
  17  |     ["Tab", 220],
  18  |   ] as const) {
  19  |     for (let i = 0; i < limit; i++) {
  20  |       if (await target.evaluate((n) => document.activeElement === n)) return;
  21  |       await page.keyboard.press(key);
  22  |     }
  23  |   }
  24  |   await expect(target).toBeFocused();
  25  | }
  26  | async function activate(page: Page, target: Locator) {
  27  |   await tabTo(page, target);
  28  |   await page.keyboard.press("Enter");
  29  | }
  30  | async function get(page: Page, route: string) {
  31  |   return page.evaluate(async (route) => {
  32  |     const response = await fetch("/api/v1" + route);
  33  |     if (!response.ok) throw new Error(`Owned read failed: ${response.status}`);
  34  |     return response.json();
  35  |   }, route);
  36  | }
  37  |
  38  | for (const viewport of [
  39  |   { width: 1024, height: 768 },
  40  |   { width: 1440, height: 900 },
  41  | ]) {
  42  |   for (const mode of ["incomplete", "observed"] as const) {
  43  |     test(`lab inventory: ${mode} public observation at ${viewport.width}x${viewport.height}`, async ({
  44  |       page,
  45  |     }, info) => {
  46  |       await page.setViewportSize(viewport);
  47  |       await connectStudio(page, info);
  48  |       const before = {
  49  |         assets: await get(page, "/assets"),
  50  |         runs: await get(page, "/runs"),
  51  |         projects: await get(page, "/projects"),
  52  |       };
  53  |       expect(before.assets).toMatchObject({
  54  |         items: [],
  55  |         complete: true,
  56  |         truncated: false,
  57  |         activeReady: false,
  58  |         physicalProviderStatus: "unavailable",
  59  |       });
  60  |       let writes = 0,
  61  |         reads = 0;
  62  |       page.on("request", (r) => {
  63  |         if (!["GET", "HEAD"].includes(r.method())) writes++;
  64  |       });
  65  |       const pattern = "**/api/v1/assets";
  66  |       await page.route(pattern, async (route) => {
  67  |         reads++;
  68  |         expect(route.request().method()).toBe("GET");
  69  |         await route.fulfill({
  70  |           status: 200,
  71  |           contentType: "application/json",
  72  |           body: JSON.stringify(observations[mode]),
  73  |         });
  74  |       });
  75  |       try {
  76  |         await activate(
  77  |           page,
  78  |           page.getByRole("button", { name: "Laboratory", exact: true }),
  79  |         );
  80  |         await expect(
  81  |           page.getByRole("heading", { name: "Physical assets", exact: true }),
  82  |         ).toBeVisible();
  83  |         await expect.poll(() => reads).toBe(1);
  84  |         if (mode === "incomplete") {
  85  |           await expect
  86  |             .soft(
  87  |               page
  88  |                 .locator(".diagnostic-list strong")
  89  |                 .filter({ hasText: /^PROVIDER_INVENTORY_UNAVAILABLE$/ }),
  90  |             )
  91  |             .toBeVisible();
  92  |         } else {
  93  |           const card = page
  94  |             .locator("section.panel")
  95  |             .filter({
  96  |               has: page.getByRole("heading", {
  97  |                 name: "urn:fixture:inventory-presentation",
  98  |                 exact: true,
  99  |               }),
  100 |             });
  101 |           const firmware = card
  102 |             .locator(".key-values > div")
  103 |             .filter({ has: page.getByText("Firmware", { exact: true }) })
  104 |             .locator("dd");
> 105 |           await expect.soft(firmware).toContainText("fixture-1.2.3");
      |                                       ^ Error: expect(locator).toContainText(expected) failed
  106 |           await expect(
  107 |             card.getByRole("button", {
  108 |               name: "Reserve observe-only",
  109 |               exact: true,
  110 |             }),
  111 |           ).toBeDisabled();
  112 |         }
  113 |         await page.unroute(pattern);
  114 |         const after = {
  115 |           assets: await get(page, "/assets"),
  116 |           runs: await get(page, "/runs"),
  117 |           projects: await get(page, "/projects"),
  118 |         };
  119 |         expect(after).toEqual(before);
  120 |         expect(writes).toBe(0);
  121 |         await info.attach("lab-inventory-observation.json", {
  122 |           body: JSON.stringify({
  123 |             viewport,
  124 |             mode,
  125 |             labelledTransportFixture: true,
  126 |             fixtureGeneratedByBackendProjection: true,
  127 |             actualInventoryEmptyAndUnadmitted: true,
  128 |             canonicalListsUnchanged: true,
  129 |             mutativeRequests: writes,
  130 |             physicalActions: 0,
  131 |             reads,
  132 |             scope:
  133 |               "UI projection observation only; synthetic owned provider used by offline generator, no runtime admission, device access or Start",
  134 |           }),
  135 |           contentType: "application/json",
  136 |         });
  137 |       } finally {
  138 |         await page.unroute(pattern);
  139 |       }
  140 |     });
  141 |   }
  142 | }
  143 |
```
