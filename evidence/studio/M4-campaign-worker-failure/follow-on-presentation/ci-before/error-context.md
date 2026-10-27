# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: wizard-accessibility.spec.ts >> wizard accessibility: late history newer head at 1024x768
- Location: tests/e2e/wizard-accessibility.spec.ts:69:5

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('.alerts')
Expected substring: "Draft saved"
Received string:    ""
Timeout: 10000ms

Call log:
  - Expect "toContainText" locator('.alerts') with timeout 10000ms
  - waiting for locator('.alerts')
    24 × locator resolved to <div class="alerts" aria-live="polite"></div>
       - unexpected value ""

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
  - button "Workspace"
  - text: System
  - heading "Late keyboard history newer head 1024" [level=1]
  - text: Draft Process control terms Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched.
  - 'button "Dependencies: none unresolved"': Dependencies
  - button "Undo" [disabled]
  - button "Redo" [disabled]
  - button "Export"
  - button "Validate"
  - button "Preflight & run"
  - tablist "System workflows":
    - tab "Model" [selected]
    - tab "Connections"
    - tab "Deployment"
    - tab "Experiments"
    - tab "Results"
    - button "XDL source"
  - text: Draft revision
  - code: "3"
  - text: 3 elements · 2 connections Execution scope Owned reference
  - complementary "Structured model navigation":
    - heading "Process explorer" [level=2]
    - button "View XDL source"
    - textbox "Search elements":
      - /placeholder: Find an element…
    - strong: reference-loop
    - text: "3"
    - button "Group by node"
    - button "controller controller"
    - button "plant plant"
    - button "observer-node observer"
    - text: RESOURCES
    - button "reference-controller Component"
    - button "reference-plant Component"
    - button "reference-loop System"
    - button "local-reference Deployment"
    - button "reference-response Scenario"
    - button "experiment-lite Profile"
    - button "studio-experiments Profile"
    - button "Add element"
  - region "Model canvas":
    - text: LOGICAL MODEL 1.0.0
    - button "Table view"
    - button "Auto layout"
    - button "Save layout"
    - application "Logical System graph. Use the System explorer for keyboard selection.":
      - img:
        - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant": command-flow
      - img:
        - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node": state-flow
      - group:
        - text: controller
        - strong: controller
        - code: controller
        - list "Named ports":
          - listitem:
            - code: controller-out
            - text: output
        - text: Logical element 1 ports
      - group:
        - text: plant
        - strong: plant
        - code: plant
        - list "Named ports":
          - listitem:
            - code: plant-in
            - text: input
          - listitem:
            - code: plant-out
            - text: output
        - text: Logical element 2 ports
      - group:
        - text: observer
        - strong: observer-node
        - code: observer-node
        - list "Named ports":
          - listitem:
            - code: observer-in
            - text: input
        - text: Logical element 1 ports
      - img
      - button "Zoom In":
        - img
      - button "Zoom Out":
        - img
      - button "Fit View":
        - img
      - img "Mini Map"
    - text: Declared communication Logical element Graph positions are presentation only
  - complementary "Element inspector":
    - heading "System inspector" [level=2]
    - heading "reference-loop" [level=3]
    - paragraph: Authoritative XDL System
    - text: Draft model
    - navigation "Model location":
      - button "reference-loop"
    - button "Properties"
    - button "Parameters"
    - paragraph: Select an element in the graph or explorer to inspect its stable identity, role, realization, and placement.
    - term: Namespace
    - definition: org.xverse.studio.process-control
    - term: XDL version
    - definition: xverse.io/xdl/v1alpha1
    - term: Resources
    - definition: "7"
    - term: Evidence scope
    - definition: Owned reference only
    - heading "Reference parameters" [level=4]
    - group "Setpoint and response":
      - text: Setpoint and response Target 1
      - spinbutton "Target 1": "1"
      - paragraph: Normalized reference setpoint, dimensionless.
      - text: Scenario XDL extension · default 1
      - button "Apply" [disabled]
      - text: Response gain 1
      - spinbutton "Response gain 1": "0.8"
      - paragraph: First-order response coefficient; gain × timestep must be at most one.
      - text: Scenario XDL extension · default 0.8
      - button "Apply" [disabled]
      - text: Initial state 1
      - spinbutton "Initial state 1": "0"
      - paragraph: Initial normalized scalar state.
      - text: Scenario XDL extension · default 0
      - button "Apply" [disabled]
    - group "Run horizon":
      - text: Run horizon Duration s
      - spinbutton "Duration s": "7"
      - paragraph: Requested simulation horizon, in seconds; at most 3,000 samples.
      - status: "Unsaved value. Current saved value: 5."
      - text: Scenario XDL extension · default 5
      - button "Apply"
      - text: Time step s
      - spinbutton "Time step s": "0.1"
      - paragraph: Fixed simulation step in seconds. Duration must be an integer number of steps.
      - text: Scenario XDL extension · default 0.1
      - button "Apply" [disabled]
    - group "Instrument faults":
      - text: Instrument faults Reference fault 1
      - combobox "Reference fault 1":
        - option "none" [selected]
        - option "stuck-sensor"
      - paragraph: Owned model fault only; stuck-sensor freezes the reported observation.
      - text: Scenario XDL extension · default none
      - button "Apply" [disabled]
    - text: Backend validation determines semantic compatibility and execution readiness.
  - text: Local project · Saved on backend Authoritative XDL · Layout stored separately 1 provider(s) available
```

# Test source

```ts
  10  |     if (await target.evaluate((node) => document.activeElement === node)) return;
  11  |     await page.keyboard.press("Tab");
  12  |   }
  13  |   throw new Error("Wizard control is unreachable through native Tab order");
  14  | }
  15  | async function activate(page: Page, target: Locator) {
  16  |   await tabTo(page, target);
  17  |   await page.keyboard.press("Enter");
  18  | }
  19  | async function type(page: Page, target: Locator, value: string) {
  20  |   await tabTo(page, target);
  21  |   await page.keyboard.press("ControlOrMeta+A");
  22  |   await page.keyboard.insertText(value);
  23  | }
  24  | async function choose(page: Page, target: Locator, value: string) {
  25  |   const options = await target.locator("option").evaluateAll((nodes) => nodes.map((n) => (n as HTMLOptionElement).value));
  26  |   const index = options.indexOf(value);
  27  |   expect(index).toBeGreaterThanOrEqual(0);
  28  |   await tabTo(page, target);
  29  |   await page.keyboard.press("Home");
  30  |   for (let i = 0; i < index; i++) await page.keyboard.press("ArrowDown");
  31  |   await expect(target).toHaveValue(value);
  32  | }
  33  | async function radio(page: Page, group: Locator, target: Locator) {
  34  |   // A native radio group has one Tab stop. Arrow keys visit its other options.
  35  |   for (let i = 0; i < 160; i++) {
  36  |     if (await group.evaluate((node) => node.contains(document.activeElement) && (document.activeElement as HTMLInputElement)?.type === "radio")) break;
  37  |     await page.keyboard.press("Tab");
  38  |   }
  39  |   const count = await group.getByRole("radio").count();
  40  |   for (let i = 0; i < count; i++) {
  41  |     if (await target.evaluate((node) => node === document.activeElement)) {
  42  |       await page.keyboard.press("Space");
  43  |       await expect(target).toBeChecked();
  44  |       return;
  45  |     }
  46  |     await page.keyboard.press("ArrowDown");
  47  |   }
  48  |   throw new Error("Radio option is unreachable through the group's native arrow navigation");
  49  | }
  50  | async function focusGeometry(target: Locator) {
  51  |   return target.evaluate((node) => {
  52  |     const rect = node.getBoundingClientRect(), style = getComputedStyle(node), clips: { top: number; right: number; bottom: number; left: number }[] = [];
  53  |     for (let parent = node.parentElement; parent; parent = parent.parentElement) {
  54  |       const paint = getComputedStyle(parent);
  55  |       if (/(auto|scroll|hidden|clip)/.test(paint.overflowX + paint.overflowY)) {
  56  |         const box = parent.getBoundingClientRect();
  57  |         clips.push({ left: box.left + parent.clientLeft, top: box.top + parent.clientTop,
  58  |           right: box.left + parent.clientLeft + parent.clientWidth, bottom: box.top + parent.clientTop + parent.clientHeight });
  59  |       }
  60  |     }
  61  |     return { focused: document.activeElement === node, activeTag: document.activeElement?.tagName, rect: rect.toJSON(), clips,
  62  |       outline: style.outlineStyle, outlineWidth: parseFloat(style.outlineWidth),
  63  |       viewport: { width: innerWidth, height: innerHeight } };
  64  |   });
  65  | }
  66  |
  67  | for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  68  | for (const mode of ["depart", "focus elsewhere", "newer head"] as const) {
  69  | test(`wizard accessibility: late history ${mode} at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
  70  |   test.setTimeout(90000);
  71  |   await page.setViewportSize(viewport);
  72  |   await connectStudio(page, testInfo);
  73  |   const project = await page.evaluate(async (name) => {
  74  |     const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
  75  |     const response = await fetch("/api/v1/projects", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify({ name }) });
  76  |     if (!response.ok) throw Error("Owned history fixture failed");
  77  |     const value = await response.json(); localStorage.setItem("studio.projectId", value.projectId); return value;
  78  |   }, `Late keyboard history ${mode} ${viewport.width}`);
  79  |   await page.reload();
  80  |   await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
  81  |   await activate(page, page.getByRole("button", { name: "Parameters", exact: true }));
  82  |   await type(page, page.getByLabel("Duration"), "6");
  83  |   await activate(page, page.getByLabel("Duration").locator("xpath=ancestor::form").getByRole("button", { name: "Apply", exact: true }));
  84  |   await expect(page.locator(".alerts")).toContainText("Draft saved");
  85  |   let release!: () => void, prepared = false, routeFinished: Promise<void> | undefined;
  86  |   const held = new Promise<void>((resolve) => { release = resolve; });
  87  |   const pattern = `**/api/v1/projects/${project.projectId}/revisions/*/restore`;
  88  |   await page.route(pattern, async (route) => {
  89  |     let finish!: () => void;
  90  |     routeFinished = new Promise<void>((resolve) => { finish = resolve; });
  91  |     try { const response = await route.fetch(); prepared = true; await held; await route.fulfill({ response }); }
  92  |     finally { finish(); }
  93  |   });
  94  |   try {
  95  |     await activate(page, page.getByRole("button", { name: "Undo", exact: true }));
  96  |     await expect.poll(() => prepared).toBe(true);
  97  |     const home = page.getByRole("button", { name: "X-Verse Studio home", exact: true });
  98  |     await tabTo(page, home);
  99  |     let newerHead: string | null = null, newerRevision: number | null = null;
  100 |     if (mode !== "focus elsewhere") {
  101 |       await page.keyboard.press("Enter");
  102 |       await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
  103 |     }
  104 |     if (mode === "newer head") {
  105 |       await activate(page, page.locator(`.project-list-row[data-project-id="${project.projectId}"] .project-open`));
  106 |       await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
  107 |       if (!(await page.getByLabel("Duration").isVisible())) await activate(page, page.getByRole("button", { name: "Parameters", exact: true }));
  108 |       await type(page, page.getByLabel("Duration"), "7");
  109 |       await activate(page, page.getByLabel("Duration").locator("xpath=ancestor::form").getByRole("button", { name: "Apply", exact: true }));
> 110 |       await expect(page.locator(".alerts")).toContainText("Draft saved");
      |                                             ^ Error: expect(locator).toContainText(expected) failed
  111 |       newerHead = await page.evaluate((id) => sessionStorage.getItem("studio.graphHistory." + id), project.projectId);
  112 |       newerRevision = (await page.request.get(`/api/v1/projects/${project.projectId}`).then((r) => r.json())).revision;
  113 |       expect(newerRevision).toBe(project.revision + 3);
  114 |       await tabTo(page, home);
  115 |     }
  116 |     const focused = await page.evaluate(() => document.activeElement?.getAttribute("aria-label"));
  117 |     const done = page.waitForResponse((r) => new URL(r.url()).pathname.endsWith("/restore") && r.request().method() === "POST");
  118 |     release(); await done;
  119 |     await expect(page.locator(".notice.busy")).toHaveCount(0);
  120 |     if (mode === "depart") {
  121 |       await expect(page.getByRole("heading", { name: "Recent projects", exact: true })).toBeVisible();
  122 |       const retained = await page.evaluate((id) => JSON.parse(sessionStorage.getItem("studio.graphHistory." + id) || "null"), project.projectId);
  123 |       expect(retained.redo[retained.redo.length - 1].at).toBe(project.revision + 2);
  124 |     } else await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
  125 |     await expect(home).toBeFocused();
  126 |     if (mode === "newer head") {
  127 |       expect(await page.evaluate((id) => sessionStorage.getItem("studio.graphHistory." + id), project.projectId)).toBe(newerHead);
  128 |       await expect(page.getByLabel("Duration")).toHaveValue("7");
  129 |       await expect(page.locator(".project-header .revision")).toHaveText(`rev ${newerRevision}`);
  130 |     }
  131 |     await testInfo.attach("late-history-navigation.json", { body: JSON.stringify({ viewport, mode, realOwnedRestore: true, currentIntentPreserved: true, newerRevision, newerHeadPreserved: mode === "newer head", focusedBeforeRelease: focused, noRunRequested: true,
  132 |       browser: await page.context().browser()?.version(), platform: process.platform }), contentType: "application/json" });
  133 |   } finally { release(); if (routeFinished) await routeFinished; await page.unroute(pattern); }
  134 | });
  135 | }
  136 | }
  137 | function checkFocus(value: Awaited<ReturnType<typeof focusGeometry>>) {
  138 |   expect(value.focused).toBe(true);
  139 |   expect(value.outline).not.toBe("none");
  140 |   expect(value.outlineWidth).toBeGreaterThanOrEqual(2);
  141 |   for (const clip of [{ left: 0, top: 0, right: value.viewport.width, bottom: value.viewport.height }, ...value.clips]) {
  142 |     expect(value.rect.left).toBeGreaterThanOrEqual(clip.left - 1);
  143 |     expect(value.rect.top).toBeGreaterThanOrEqual(clip.top - 1);
  144 |     expect(value.rect.right).toBeLessThanOrEqual(clip.right + 1);
  145 |     expect(value.rect.bottom).toBeLessThanOrEqual(clip.bottom + 1);
  146 |   }
  147 | }
  148 | function source(project: any, suffix: string): string {
  149 |   return (Object.values(project.documents) as any[]).find((d) => d.path.endsWith("/" + suffix)).content;
  150 | }
  151 | const hash = (text: string) => createHash("sha256").update(text).digest("hex");
  152 |
  153 | for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  154 |   test(`wizard accessibility: native keyboard instance, placement and binding at ${viewport.width}x${viewport.height}`, async ({ page }, testInfo) => {
  155 |     test.setTimeout(120000);
  156 |     await page.setViewportSize(viewport);
  157 |     await connectStudio(page, testInfo);
  158 |     const project = await page.evaluate(async (width) => {
  159 |       const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
  160 |       const response = await fetch("/api/v1/projects", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify({ name: `Keyboard instance ${width}` }) });
  161 |       if (!response.ok) throw Error("Owned project setup failed");
  162 |       const value = await response.json(); localStorage.setItem("studio.projectId", value.projectId); return value;
  163 |     }, viewport.width);
  164 |     const runsBefore = await page.request.get("/api/v1/runs").then((r) => r.json());
  165 |     await page.reload();
  166 |     await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
  167 |     const writes: { method: string; path: string; body: any }[] = [];
  168 |     page.on("request", (r) => {
  169 |       if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method())) writes.push({ method: r.method(), path: new URL(r.url()).pathname, body: r.postDataJSON() });
  170 |     });
  171 |     const geometry: { step: string; value: Awaited<ReturnType<typeof focusGeometry>> }[] = [];
  172 |     const measurements: Awaited<ReturnType<typeof renderedContrast>>[] = [];
  173 |     const add = page.getByRole("button", { name: "Add element", exact: true });
  174 |     const dialog = page.getByRole("dialog", { name: "Add Unit", exact: true });
  175 |     const instance = `keyboard-plant-${viewport.width}`;
  176 |     try {
  177 |       await activate(page, add);
  178 |       await expect(dialog.getByLabel("Element family")).toHaveValue("component");
  179 |       const definitions = dialog.getByRole("radiogroup", { name: "Definitions" });
  180 |       const plant = definitions.getByRole("radio", { name: /reference-plant org\.xverse\.studio\.process-control/ });
  181 |       await radio(page, definitions, plant);
  182 |       geometry.push({ step: "definition radio", value: await focusGeometry(plant) });
  183 |       const identifier = dialog.getByLabel("Instance identifier"), submit = dialog.getByRole("button", { name: "Add instance", exact: true });
  184 |       await type(page, identifier, "Bad_ID");
  185 |       await expect(submit).toBeDisabled();
  186 |       await expect(dialog.getByRole("region", { name: "Review" }).getByRole("status")).toContainText("lowercase, hyphenated instance identifier");
  187 |       expect(writes).toEqual([]);
  188 |       measurements.push(await renderedContrast(dialog.getByRole("status"), "Rejected identifier status"));
  189 |       await type(page, identifier, instance);
  190 |       measurements.push(await renderedContrast(identifier.locator("xpath=ancestor::fieldset").locator(".field-hint"), "Instance identity explanation"));
  191 |       await choose(page, dialog.getByLabel("Role filter"), "plant");
  192 |       await choose(page, dialog.getByLabel("Placement node"), "plant-node");
  193 |       measurements.push(await renderedContrast(dialog.getByLabel("Placement node").locator("xpath=ancestor::fieldset").locator(".field-hint"), "Role and placement explanation"));
  194 |       const variant = dialog.getByLabel("Deployment variant");
  195 |       const variantId = await variant.locator("option").filter({ hasText: /^local-reference$/ }).getAttribute("value");
  196 |       expect(variantId).toBeTruthy();
  197 |       await choose(page, variant, variantId!);
  198 |       await expect(submit).toBeDisabled();
  199 |       await radio(page, dialog.getByRole("radiogroup", { name: "Realization class" }), dialog.getByRole("radio", { name: "simulated", exact: true }));
  200 |       await choose(page, dialog.getByLabel("Deployment target"), "reference-target");
  201 |       const artifact = dialog.getByRole("checkbox", { name: /reference-model/ });
  202 |       await tabTo(page, artifact); await page.keyboard.press("Space"); await expect(artifact).toBeChecked();
  203 |       const review = dialog.getByRole("region", { name: "Review" });
  204 |       await expect(review.getByRole("listitem")).toHaveText([
  205 |         `Add instance ${instance} of reference-plant on node plant-node`,
  206 |         new RegExp(`^Bind ${instance} as simulated to target reference-target \\(${instance}-binding\\)`),
  207 |       ]);
  208 |       await expect(review).toContainText("Nothing is built, flashed or executed");
  209 |       await tabTo(page, submit);
  210 |       geometry.push({ step: "long wizard submit", value: await focusGeometry(submit) });
```
