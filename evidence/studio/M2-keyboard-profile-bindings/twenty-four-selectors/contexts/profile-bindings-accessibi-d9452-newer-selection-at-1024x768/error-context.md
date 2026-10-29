# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: profile-bindings-accessibility.spec.ts >> profile bindings: newer selection at 1024x768
- Location: tests/e2e/profile-bindings-accessibility.spec.ts:177:9

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.profile-binding-panel').getByRole('checkbox', { name: 'Select profile Process control terminology', exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" locator('.profile-binding-panel').getByRole('checkbox', { name: 'Select profile Process control terminology', exact: true }) with timeout 10000ms
  - waiting for locator('.profile-binding-panel').getByRole('checkbox', { name: 'Select profile Process control terminology', exact: true })

```

```yaml
- link "Skip to workspace":
  - /url: "#main-content"
- banner:
  - button "X-Verse Studio home": X X-VERSE STUDIO
  - text: Local workspace
  - button "Environment"
  - text: LO
- navigation "Main navigation":
  - button "Workspace"
  - button "Catalog"
  - button "Laboratory": Lab
  - button "Compatibility and environment": Settings
  - text: v0.1
- main:
  - text: Binding immutable profile identities… COMPATIBILITY & AUTHORITY
  - heading "Environment" [level=1]
  - paragraph: Studio host support and each provider’s compatibility are independent.
  - heading "Studio backend" [level=2]
  - term: API version
  - definition: "1.0"
  - term: Host OS
  - definition: Linux
  - term: Architecture
  - definition: x86_64
  - term: Native target OS
  - definition: "[\"Linux\",\"Windows\"]"
  - term: Verified native OS
  - definition: "[\"Linux\"]"
  - term: Windows checks
  - definition: BLOCKED_USER_REQUEST
  - term: Execution owner
  - definition: Backend and admitted provider
  - term: Exposure
  - definition: Local authenticated session
  - group: Inspect exact data
  - heading "Provider compatibility" [level=2]
  - heading "Studio executable reference" [level=3]
  - text: Available
  - paragraph
  - term: Version
  - definition: 1.0.0
  - term: Scope
  - definition: owned_reference
  - term: Supported OS
  - definition: "[\"Linux\",\"Windows\"]"
  - term: Maturity
  - definition: fixture
  - group: Inspect exact data
  - heading "X-Verse Lite / CARLA" [level=3]
  - text: Unavailable
  - paragraph
  - term: Version
  - definition: unavailable
  - term: Scope
  - definition: unavailable
  - term: Supported OS
  - definition: "[\"Linux\"]"
  - term: Maturity
  - definition: unavailable
  - list:
    - listitem:
      - strong: DEP-RUN-CONFIG
      - text: The inspected Bash harness uses a private trusted-host path and generates its own XDL. An admitted public effective-input/plan contract and permitted live environment are required.
  - group: Inspect exact data
  - heading "Admitted profile locks" [level=2]
  - paragraph: Profiles supply versioned semantics and inert presentation metadata. Provider installation and execution authority are separate.
  - paragraph: Select one to 16 admitted profiles. Binding adds these exact locks and keeps existing locks. Unchecking a box only changes your next submission; it does not remove a project lock. Changes made while a request is pending are not included in that request.
  - status: Binding the submitted profile locks. This request is still pending.
  - form "Bind admitted profile locks":
    - article:
      - checkbox "Select profile Declared experiment intent"
      - text: Select profile Declared experiment intent admitted_integration
      - paragraph: Packaged declarative profile; provider execution is admitted independently.
      - term: Namespace
      - definition: io.xverse.experiment
      - term: Version
      - definition: 0.1.0
      - term: Schema identity
      - definition: sha256:a2123b3349ab016fda829d57084d9142565bf76fdafd474fe19fe222562dfc30
      - term: Presentation identity
      - definition: sha256:44887b3ffa7b157653f4e41f874b0e700e9d81659b732f3e3487e7c6ee703b46
      - term: Execution allowed
      - definition: No; provider authority is independent
      - group: Inspect exact data
    - article:
      - checkbox "Select profile Bounded experiment assessment"
      - text: Select profile Bounded experiment assessment admitted_integration
      - paragraph: Packaged declarative profile; provider execution is admitted independently.
      - term: Namespace
      - definition: io.xverse.studio.experiments
      - term: Version
      - definition: 1.0.0
      - term: Schema identity
      - definition: sha256:2f24e20f9c926aaa755728a01342b1ebb1cb114438dd4262901afd6a446874cd
      - term: Presentation identity
      - definition: sha256:658c1023c22e1651485498c46e2ec0e30bb6da1f96bc31957753316f43a91e1d
      - term: Execution allowed
      - definition: No; provider authority is independent
      - group: Inspect exact data
    - article:
      - checkbox "Select profile Owned connection contracts"
      - text: Select profile Owned connection contracts admitted_integration
      - paragraph: Packaged declarative profile; provider execution is admitted independently.
      - term: Namespace
      - definition: io.xverse.studio.connections
      - term: Version
      - definition: 1.0.0
      - term: Schema identity
      - definition: sha256:40a89b71efae28e8fa4b80372842988d12b588bf7c95f3de05695ea33462bbbe
      - term: Presentation identity
      - definition: sha256:00d83bda8c2c5d5dfd522bdf622ef6474243aa49a902c280471d3000f6982be3
      - term: Execution allowed
      - definition: No; provider authority is independent
      - group: Inspect exact data
    - article:
      - checkbox "Select profile Process-control terminology"
      - text: Select profile Process-control terminology fixture
      - paragraph: Owned presentation for the process-control reference blueprints; no plant, equipment or fidelity claim.
      - paragraph:
        - text: Domain
        - strong: Process control
        - text: ": terminology only; it never changes semantics or execution."
      - list:
        - listitem: System → Process
        - listitem: Element → Unit
        - listitem: Flow → Signal
        - listitem: Deployment → Plant deployment
        - listitem: Scenario → Operating scenario
      - paragraph:
        - text: "Documentation reference (not fetched):"
        - code: urn:xverse:studio:domain:process-control:1.0
      - term: Namespace
      - definition: io.xverse.studio.domain.process-control
      - term: Version
      - definition: 1.0.0
      - term: Schema identity
      - definition: sha256:43d97f8dcadfa1246450121be31fc8c333f617301d29cf9cee100d8a8365bb6b
      - term: Presentation identity
      - definition: sha256:d12dc2ded838c751e8bd51fec413f8e6842e8ff31407c1c4d7472b273d72972d
      - term: Execution allowed
      - definition: No; provider authority is independent
      - group: Inspect exact data
    - article:
      - checkbox "Select profile Automotive terminology" [checked]
      - text: Select profile Automotive terminology fixture
      - paragraph: Owned presentation for the automotive reference blueprint; no vehicle dynamics or ECU fidelity claim.
      - paragraph:
        - text: Domain
        - strong: Automotive
        - text: ": terminology only; it never changes semantics or execution."
      - list:
        - listitem: System → Vehicle function
        - listitem: Element → ECU
        - listitem: Flow → Bus signal
        - listitem: Deployment → Vehicle deployment
        - listitem: Scenario → Drive scenario
      - paragraph:
        - text: "Documentation reference (not fetched):"
        - code: urn:xverse:studio:domain:automotive:1.0
      - term: Namespace
      - definition: io.xverse.studio.domain.automotive
      - term: Version
      - definition: 1.0.0
      - term: Schema identity
      - definition: sha256:43d97f8dcadfa1246450121be31fc8c333f617301d29cf9cee100d8a8365bb6b
      - term: Presentation identity
      - definition: sha256:e234d3ab15834f2871bc9af88600568f7864f6d5c6a84a39001341a19ab23538
      - term: Execution allowed
      - definition: No; provider authority is independent
      - group: Inspect exact data
    - text: "Selected project: Profile newer selection 1024 · revision 1"
    - button "Bind selected profile locks" [disabled]
```

# Test source

```ts
  1   | import { test, expect, type Page, type Locator } from "@playwright/test";
  2   | import { createHash } from "node:crypto";
  3   | import { readFileSync, writeFileSync, realpathSync } from "node:fs";
  4   | import path from "node:path";
  5   | import { parse } from "yaml";
  6   | import { connectStudio } from "./connect-studio";
  7   | import { renderedContrast } from "./contrast";
  8   |
  9   | async function tabTo(page: Page, target: Locator) {
> 10  |   await expect(target).toBeVisible();
      |                        ^ Error: expect(locator).toBeVisible() failed
  11  |   for (const [key, limit] of [
  12  |     ["Shift+Tab", 40],
  13  |     ["Tab", 220],
  14  |   ] as const) {
  15  |     for (let i = 0; i < limit; i++) {
  16  |       if (await target.evaluate((n) => document.activeElement === n)) return;
  17  |       await page.keyboard.press(key);
  18  |     }
  19  |   }
  20  |   await expect(target).toBeFocused();
  21  | }
  22  | async function activate(page: Page, target: Locator) {
  23  |   await tabTo(page, target);
  24  |   await page.keyboard.press("Enter");
  25  | }
  26  | async function request(
  27  |   page: Page,
  28  |   route: string,
  29  |   body?: unknown,
  30  |   revision?: number,
  31  | ) {
  32  |   return page.evaluate(
  33  |     async ({ route, body, revision }) => {
  34  |       const { csrfToken } = await fetch("/api/v1/session").then((r) =>
  35  |         r.json(),
  36  |       );
  37  |       const response = await fetch("/api/v1" + route, {
  38  |         method: body === undefined ? "GET" : "POST",
  39  |         headers: {
  40  |           "Content-Type": "application/json",
  41  |           "X-CSRF-Token": csrfToken,
  42  |           ...(revision === undefined ? {} : { "If-Match": `"${revision}"` }),
  43  |         },
  44  |         body: body === undefined ? undefined : JSON.stringify(body),
  45  |       });
  46  |       const value = await response.json();
  47  |       if (!response.ok)
  48  |         throw Error(
  49  |           `Owned profile fixture request failed: ${response.status} ${value.code}`,
  50  |         );
  51  |       return value;
  52  |     },
  53  |     { route, body, revision },
  54  |   );
  55  | }
  56  | async function create(page: Page, name: string) {
  57  |   const project = await request(page, "/projects", { name });
  58  |   await page.evaluate(
  59  |     (pid) => localStorage.setItem("studio.projectId", pid),
  60  |     project.projectId,
  61  |   );
  62  |   await page.reload();
  63  |   await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  64  |   return project;
  65  | }
  66  | const panel = (page: Page) => page.locator(".profile-binding-panel");
  67  | const bind = (page: Page) =>
  68  |   panel(page).getByRole("button", {
  69  |     name: "Bind selected profile locks",
  70  |     exact: true,
  71  |   });
  72  | async function environment(page: Page) {
  73  |   await activate(
  74  |     page,
  75  |     page.getByRole("button", { name: "Environment", exact: true }),
  76  |   );
  77  |   await expect(
  78  |     panel(page).getByRole("heading", {
  79  |       name: "Admitted profile locks",
  80  |       exact: true,
  81  |     }),
  82  |   ).toBeVisible();
  83  | }
  84  | async function settle(page: Page) {
  85  |   await page.waitForLoadState("networkidle");
  86  |   await page.evaluate(
  87  |     () =>
  88  |       new Promise<void>((resolve) =>
  89  |         requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
  90  |       ),
  91  |   );
  92  |   await page.waitForLoadState("networkidle");
  93  | }
  94  | async function runs(page: Page, pid: string) {
  95  |   return (await request(page, "/runs")).items
  96  |     .filter((r: any) => r.projectId === pid)
  97  |     .map((r: any) => r.runId)
  98  |     .sort();
  99  | }
  100 | const digest = (value: string) =>
  101 |   "sha256:" + createHash("sha256").update(value).digest("hex");
  102 | const identity = (entry: any) => ({
  103 |   profileId: entry.profileId,
  104 |   version: entry.version,
  105 |   schemaDigest: entry.schemaDigest,
  106 |   presentationDigest: entry.presentationDigest,
  107 | });
  108 | async function choose(page: Page, name: string) {
  109 |   const control = panel(page).getByRole("checkbox", {
  110 |     name: `Select profile ${name}`,
```
