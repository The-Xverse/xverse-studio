# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: lab-inventory-accessibility.spec.ts >> lab inventory: missing physical declaration stays unknown at 1440x900
- Location: tests/e2e/lab-inventory-accessibility.spec.ts:24:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('.lab-page').locator('section.panel').filter({ has: getByRole('heading', { name: 'urn:fixture:inventory-presentation', exact: true }) })
Timeout: 10000ms
- Expected substring  -  1
+ Received string     + 52

- Not confirmed physical
+ urn:fixture:inventory-presentationfixtureIdentityurn:fixture:inventory-presentationProviderfixtureProvider versionfixture-provider-1.0RealizationNon-physical asset observationIdentity observationobservedObserved identity{"serial":"SYNTHETIC-UI-001","model":"Inventory contract fixture"}FirmwareObserved · fixture-1.2.3Artifact revisionUnknownMetadata coveragepartialInterfacescommandProvider OS declarationLinuxDeclared capabilitiesobserve, stimulatePermission scopeunknownAvailabilityObserved availablePhysical stateUnknownProvider admissionunavailableActive-operation readinessBlockedPHYSICAL_PROVIDER_NOT_ADMITTEDAsset observation diagnosticReserve observe-onlyInspect exact data{
+   "assetId": "urn:fixture:inventory-presentation",
+   "providerId": "fixture",
+   "providerVersion": "fixture-provider-1.0",
+   "physical": false,
+   "identity": {
+     "serial": "SYNTHETIC-UI-001",
+     "model": "Inventory contract fixture"
+   },
+   "identityStatus": "observed",
+   "firmware": {
+     "status": "observed",
+     "version": "fixture-1.2.3"
+   },
+   "artifactRevision": {
+     "status": "unknown"
+   },
+   "metadata": {
+     "status": "partial",
+     "limitations": [
+       "Only allowlisted identity and revision observations are exposed."
+     ]
+   },
+   "interfaces": {
+     "command": {
+       "id": "command",
+       "direction": "input",
+       "payloadSchema": "urn:fixture:command"
+     }
+   },
+   "interfacesStatus": "declared",
+   "supportedOS": [
+     "Linux"
+   ],
+   "observationTruncated": false,
+   "capabilities": [
+     "observe",
+     "stimulate"
+   ],
+   "permissionScope": "unknown",
+   "available": true,
+   "evidenceScope": "fixture",
+   "providerAdmission": "unavailable",
+   "activeReady": false,
+   "reservable": false,
+   "diagnostics": [
+     {
+       "code": "PHYSICAL_PROVIDER_NOT_ADMITTED",
+       "message": "Asset observation diagnostic"
+     }
+   ]
+ }

Call log:
  - Expect "soft toContainText" locator('.lab-page').locator('section.panel').filter({ has: getByRole('heading', { name: 'urn:fixture:inventory-presentation', exact: true }) }) with timeout 10000ms
  - waiting for locator('.lab-page').locator('section.panel').filter({ has: getByRole('heading', { name: 'urn:fixture:inventory-presentation', exact: true }) })
    24 × locator resolved to <section class="panel">…</section>
       - unexpected value "urn:fixture:inventory-presentationfixtureIdentityurn:fixture:inventory-presentationProviderfixtureProvider versionfixture-provider-1.0RealizationNon-physical asset observationIdentity observationobservedObserved identity{"serial":"SYNTHETIC-UI-001","model":"Inventory contract fixture"}FirmwareObserved · fixture-1.2.3Artifact revisionUnknownMetadata coveragepartialInterfacescommandProvider OS declarationLinuxDeclared capabilitiesobserve, stimulatePermission scopeunknownAvailabilityObserved availablePhysical stateUnknownProvider admissionunavailableActive-operation readinessBlockedPHYSICAL_PROVIDER_NOT_ADMITTEDAsset observation diagnosticReserve observe-onlyInspect exact data{
  "assetId": "urn:fixture:inventory-presentation",
  "providerId": "fixture",
  "providerVersion": "fixture-provider-1.0",
  "physical": false,
  "identity": {
    "serial": "SYNTHETIC-UI-001",
    "model": "Inventory contract fixture"
  },
  "identityStatus": "observed",
  "firmware": {
    "status": "observed",
    "version": "fixture-1.2.3"
  },
  "artifactRevision": {
    "status": "unknown"
  },
  "metadata": {
    "status": "partial",
    "limitations": [
      "Only allowlisted identity and revision observations are exposed."
    ]
  },
  "interfaces": {
    "command": {
      "id": "command",
      "direction": "input",
      "payloadSchema": "urn:fixture:command"
    }
  },
  "interfacesStatus": "declared",
  "supportedOS": [
    "Linux"
  ],
  "observationTruncated": false,
  "capabilities": [
    "observe",
    "stimulate"
  ],
  "permissionScope": "unknown",
  "available": true,
  "evidenceScope": "fixture",
  "providerAdmission": "unavailable",
  "activeReady": false,
  "reservable": false,
  "diagnostics": [
    {
      "code": "PHYSICAL_PROVIDER_NOT_ADMITTED",
      "message": "Asset observation diagnostic"
    }
  ]
}"

```

```yaml
- heading "urn:fixture:inventory-presentation" [level=3]
- text: fixture
- term: Identity
- definition: urn:fixture:inventory-presentation
- term: Provider
- definition: fixture
- term: Provider version
- definition: fixture-provider-1.0
- term: Realization
- definition: Non-physical asset observation
- term: Identity observation
- definition: observed
- term: Observed identity
- definition: "{\"serial\":\"SYNTHETIC-UI-001\",\"model\":\"Inventory contract fixture\"}"
- term: Firmware
- definition: Observed · fixture-1.2.3
- term: Artifact revision
- definition: Unknown
- term: Metadata coverage
- definition: partial
- term: Interfaces
- definition: command
- term: Provider OS declaration
- definition: Linux
- term: Declared capabilities
- definition: observe, stimulate
- term: Permission scope
- definition: unknown
- term: Availability
- definition: Observed available
- term: Physical state
- definition: Unknown
- term: Provider admission
- definition: unavailable
- term: Active-operation readiness
- definition: Blocked
- list:
  - listitem:
    - strong: PHYSICAL_PROVIDER_NOT_ADMITTED
    - text: Asset observation diagnostic
- button "Reserve observe-only" [disabled]
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
  24  |   test(`lab inventory: missing physical declaration stays unknown at ${viewport.width}x${viewport.height}`, async ({
  25  |     page,
  26  |   }, info) => {
  27  |     const finish = await begin(page, info, viewport);
  28  |     expect(observations.unclassifiedSource.physicalPropertyPresent).toBe(false);
  29  |     expect(observations.unclassified.items[0].physical).toBe(false);
  30  |     await page.route(assetPattern, (route) =>
  31  |       route.fulfill({
  32  |         status: 200,
  33  |         contentType: "application/json",
  34  |         body: JSON.stringify(observations.unclassified),
  35  |       }),
  36  |     );
  37  |     await openLab(page);
  38  |     const card = assetCard(page);
  39  |     await expect(card).toBeVisible();
> 40  |     await expect.soft(card).toContainText("Not confirmed physical");
      |                             ^ Error: expect(locator).toContainText(expected) failed
  41  |     await expect(
  42  |       card.getByRole("button", { name: "Reserve observe-only", exact: true }),
  43  |     ).toBeDisabled();
  44  |     await finish({
  45  |       omittedPhysicalSource: true,
  46  |       normalizedPhysicalFlag: false,
  47  |       labelledBackendProjectionFixture: true,
  48  |     });
  49  |   });
  50  | }
  51  |
  52  | async function tabTo(page: Page, target: Locator) {
  53  |   await expect(target).toBeVisible();
  54  |   for (const [key, limit] of [
  55  |     ["Shift+Tab", 40],
  56  |     ["Tab", 220],
  57  |   ] as const) {
  58  |     for (let i = 0; i < limit; i++) {
  59  |       if (await target.evaluate((n) => document.activeElement === n)) return;
  60  |       await page.keyboard.press(key);
  61  |     }
  62  |   }
  63  |   await expect(target).toBeFocused();
  64  | }
  65  |
  66  | const lab = (page: Page) => page.locator(".lab-page");
  67  | const refresh = (page: Page) =>
  68  |   lab(page).getByRole("button", { name: "Refresh inventory", exact: true });
  69  | const observationHeading = (page: Page) =>
  70  |   lab(page).getByRole("heading", {
  71  |     name: "Inventory observation",
  72  |     exact: true,
  73  |   });
  74  | const nextPage = (page: Page) =>
  75  |   lab(page).getByRole("button", { name: "Next inventory page", exact: true });
  76  | const previousPage = (page: Page) =>
  77  |   lab(page).getByRole("button", {
  78  |     name: "Previous inventory page",
  79  |     exact: true,
  80  |   });
  81  | const assetCard = (page: Page, id = "urn:fixture:inventory-presentation") =>
  82  |   lab(page)
  83  |     .locator("section.panel")
  84  |     .filter({ has: page.getByRole("heading", { name: id, exact: true }) });
  85  | const field = (card: Locator, name: string) =>
  86  |   card
  87  |     .locator(".key-values > div")
  88  |     .filter({ has: card.page().getByText(name, { exact: true }) })
  89  |     .locator("dd");
  90  | const assetPattern = "**/api/v1/assets*";
  91  |
  92  | async function begin(
  93  |   page: Page,
  94  |   info: TestInfo,
  95  |   viewport: { width: number; height: number },
  96  | ) {
  97  |   await page.setViewportSize(viewport);
  98  |   await connectStudio(page, info);
  99  |   const before = {
  100 |     assets: await get(page, "/assets"),
  101 |     projects: await get(page, "/projects"),
  102 |     runs: await get(page, "/runs"),
  103 |   };
  104 |   let writes = 0;
  105 |   page.on("request", (r) => {
  106 |     if (!["GET", "HEAD"].includes(r.method())) writes++;
  107 |   });
  108 |   return async (details: Record<string, unknown>) => {
  109 |     await page.unroute(assetPattern);
  110 |     await page.waitForLoadState("networkidle");
  111 |     expect({
  112 |       assets: await get(page, "/assets"),
  113 |       projects: await get(page, "/projects"),
  114 |       runs: await get(page, "/runs"),
  115 |     }).toEqual(before);
  116 |     expect(writes).toBe(0);
  117 |     await info.attach("lab-inventory-journey.json", {
  118 |       body: JSON.stringify({
  119 |         viewport,
  120 |         ...details,
  121 |         mutativeRequests: writes,
  122 |         canonicalListsUnchanged: true,
  123 |         noStartOrDeviceOperation: true,
  124 |         scope:
  125 |           "Native browser UI over actual empty/unadmitted inventory and explicitly labelled controlled public observations; no physical integration claim",
  126 |       }),
  127 |       contentType: "application/json",
  128 |     });
  129 |   };
  130 | }
  131 | async function openLab(page: Page) {
  132 |   await activate(
  133 |     page,
  134 |     page.getByRole("button", { name: "Laboratory", exact: true }),
  135 |   );
  136 |   await expect(
  137 |     lab(page).getByRole("heading", { name: "Physical assets", exact: true }),
  138 |   ).toBeVisible();
  139 | }
  140 | async function controlBounds(
```
