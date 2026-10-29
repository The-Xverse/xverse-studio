# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: profile-bindings-accessibility.spec.ts >> profile bindings: discovery failure stays unknown and retries actual registry at 1440x900
- Location: tests/e2e/profile-bindings-accessibility.spec.ts:98:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('.profile-binding-panel').getByRole('alert')
Expected pattern: /unknown|unavailable|could not/i
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toContainText" locator('.profile-binding-panel').getByRole('alert') with timeout 10000ms
  - waiting for locator('.profile-binding-panel').getByRole('alert')

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
  - text: COMPATIBILITY & AUTHORITY
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
  - text: "Selected project: Profile discovery 1440 · revision 1"
  - button "Bind selected profile locks" [disabled]
```

# Test source

```ts
  37  |       const value = await response.json();
  38  |       if (!response.ok)
  39  |         throw Error(
  40  |           `Owned profile fixture request failed: ${response.status} ${value.code}`,
  41  |         );
  42  |       return value;
  43  |     },
  44  |     { route, body },
  45  |   );
  46  | }
  47  | async function create(page: Page, name: string) {
  48  |   const project = await request(page, "/projects", { name });
  49  |   await page.evaluate(
  50  |     (pid) => localStorage.setItem("studio.projectId", pid),
  51  |     project.projectId,
  52  |   );
  53  |   await page.reload();
  54  |   await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  55  |   return project;
  56  | }
  57  | const panel = (page: Page) => page.locator(".profile-binding-panel");
  58  | const bind = (page: Page) =>
  59  |   panel(page).getByRole("button", {
  60  |     name: "Bind selected profile locks",
  61  |     exact: true,
  62  |   });
  63  | async function environment(page: Page) {
  64  |   await activate(
  65  |     page,
  66  |     page.getByRole("button", { name: "Environment", exact: true }),
  67  |   );
  68  |   await expect(
  69  |     panel(page).getByRole("heading", {
  70  |       name: "Admitted profile locks",
  71  |       exact: true,
  72  |     }),
  73  |   ).toBeVisible();
  74  | }
  75  | async function settle(page: Page) {
  76  |   await page.waitForLoadState("networkidle");
  77  |   await page.evaluate(
  78  |     () =>
  79  |       new Promise<void>((resolve) =>
  80  |         requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
  81  |       ),
  82  |   );
  83  |   await page.waitForLoadState("networkidle");
  84  | }
  85  | async function runs(page: Page, pid: string) {
  86  |   return (await request(page, "/runs")).items
  87  |     .filter((r: any) => r.projectId === pid)
  88  |     .map((r: any) => r.runId)
  89  |     .sort();
  90  | }
  91  | const digest = (value: string) =>
  92  |   "sha256:" + createHash("sha256").update(value).digest("hex");
  93  |
  94  | for (const viewport of [
  95  |   { width: 1024, height: 768 },
  96  |   { width: 1440, height: 900 },
  97  | ]) {
  98  |   test(`profile bindings: discovery failure stays unknown and retries actual registry at ${viewport.width}x${viewport.height}`, async ({
  99  |     page,
  100 |   }, info) => {
  101 |     test.setTimeout(60000);
  102 |     await page.setViewportSize(viewport);
  103 |     await connectStudio(page, info);
  104 |     const project = await create(page, `Profile discovery ${viewport.width}`),
  105 |       beforeRuns = await runs(page, project.projectId);
  106 |     let reads = 0,
  107 |       writes = 0;
  108 |     page.on("request", (r) => {
  109 |       if (
  110 |         r.method() === "POST" &&
  111 |         new URL(r.url()).pathname.endsWith("/profile-bindings")
  112 |       )
  113 |         writes++;
  114 |     });
  115 |     const pattern = "**/api/v1/profiles";
  116 |     await page.route(pattern, async (route) => {
  117 |       reads++;
  118 |       if (reads === 1)
  119 |         await route.fulfill({
  120 |           status: 503,
  121 |           contentType: "application/json",
  122 |           body: JSON.stringify({
  123 |             code: "PROFILE_DISCOVERY_UNAVAILABLE",
  124 |             message: "Controlled registry transport failure",
  125 |             retryable: true,
  126 |           }),
  127 |         });
  128 |       else {
  129 |         const response = await route.fetch();
  130 |         expect(response.status()).toBe(200);
  131 |         await route.fulfill({ response });
  132 |       }
  133 |     });
  134 |     try {
  135 |       await environment(page);
  136 |       await expect.poll(() => reads).toBe(1);
> 137 |       await expect(panel(page).getByRole("alert")).toContainText(
      |                                                    ^ Error: expect(locator).toContainText(expected) failed
  138 |         /unknown|unavailable|could not/i,
  139 |       );
  140 |       await expect(panel(page).getByRole("checkbox")).toHaveCount(0);
  141 |       await expect(bind(page)).toBeDisabled();
  142 |       await activate(
  143 |         page,
  144 |         panel(page).getByRole("button", {
  145 |           name: "Retry profile discovery",
  146 |           exact: true,
  147 |         }),
  148 |       );
  149 |       await expect(
  150 |         panel(page).getByRole("checkbox", {
  151 |           name: "Select profile Automotive terminology",
  152 |           exact: true,
  153 |         }),
  154 |       ).toBeVisible();
  155 |       expect(reads).toBe(2);
  156 |       await expect(panel(page).getByRole("alert")).toHaveCount(0);
  157 |       expect(writes).toBe(0);
  158 |       expect(
  159 |         (await request(page, `/projects/${project.projectId}`)).documents,
  160 |       ).toEqual(project.documents);
  161 |       expect(await runs(page, project.projectId)).toEqual(beforeRuns);
  162 |       await info.attach("profile-discovery.json", {
  163 |         body: JSON.stringify({
  164 |           viewport,
  165 |           controlledInitialStatus: 503,
  166 |           retryStatus: 200,
  167 |           actualRegistryRetried: true,
  168 |           observationsStayUnknownOnFailure: true,
  169 |           bindingWrites: writes,
  170 |           noStart: true,
  171 |           scope:
  172 |             "Labelled discovery transport failure then actual admitted registry; no provider installation or execution authority",
  173 |         }),
  174 |         contentType: "application/json",
  175 |       });
  176 |     } finally {
  177 |       await page.unroute(pattern);
  178 |     }
  179 |   });
  180 |
  181 |   test(`profile bindings: committed reply cannot announce success on departed Home at ${viewport.width}x${viewport.height}`, async ({
  182 |     page,
  183 |   }, info) => {
  184 |     test.setTimeout(90000);
  185 |     await page.setViewportSize(viewport);
  186 |     await connectStudio(page, info);
  187 |     const project = await create(
  188 |         page,
  189 |         `Profile binding departure ${viewport.width}`,
  190 |       ),
  191 |       beforeRuns = await runs(page, project.projectId),
  192 |       beforeProviders = await request(page, "/providers"),
  193 |       beforePlan = await request(
  194 |         page,
  195 |         `/projects/${project.projectId}/compilations`,
  196 |         { revision: project.revision },
  197 |       ),
  198 |       entries = (await request(page, "/profiles")).items,
  199 |       selected = entries.find(
  200 |         (p: any) => p.namespace === "io.xverse.studio.domain.automotive",
  201 |       );
  202 |     expect(selected.presentation.name).toBe("Automotive terminology");
  203 |     expect(selected.executionAllowed).toBe(false);
  204 |     await environment(page);
  205 |     const checkbox = panel(page).getByRole("checkbox", {
  206 |       name: "Select profile Automotive terminology",
  207 |       exact: true,
  208 |     });
  209 |     await tabTo(page, checkbox);
  210 |     await page.keyboard.press("Space");
  211 |     await expect(checkbox).toBeChecked();
  212 |     let release!: () => void,
  213 |       finish!: () => void,
  214 |       ready = false,
  215 |       committed: any;
  216 |     const gate = new Promise<void>((r) => (release = r)),
  217 |       finished = new Promise<void>((r) => (finish = r)),
  218 |       pattern = `**/api/v1/projects/${project.projectId}/profile-bindings`;
  219 |     const writes: { ifMatch?: string; body: any }[] = [];
  220 |     await page.route(pattern, async (route) => {
  221 |       try {
  222 |         expect(route.request().method()).toBe("POST");
  223 |         writes.push({
  224 |           ifMatch: route.request().headers()["if-match"],
  225 |           body: route.request().postDataJSON(),
  226 |         });
  227 |         const response = await route.fetch();
  228 |         expect(response.status()).toBe(200);
  229 |         committed = await response.json();
  230 |         ready = true;
  231 |         await gate;
  232 |         await route.fulfill({ response });
  233 |       } finally {
  234 |         finish();
  235 |       }
  236 |     });
  237 |     try {
```
