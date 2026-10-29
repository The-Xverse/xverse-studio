# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: project-context.spec.ts >> project context: cached run metadata respects Source at 1440x900
- Location: tests/e2e/project-context.spec.ts:439:9

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('tab', { name: 'Results', exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('tab', { name: 'Results', exact: true }) with timeout 10000ms
  - waiting for getByRole('tab', { name: 'Results', exact: true })

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
  - button "Workspace"
  - text: System
  - heading "Cached run context Source 1440" [level=1]
  - text: Draft Process control terms Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched. rev 1
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
    - tab "Results 1"
    - button "XDL source"
  - text: Draft revision
  - code: "1"
  - text: 3 elements · 2 connections Run snapshot
  - code: snap-56923bc
  - text: stopped
  - button "Draft matches run inputs"
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
      - spinbutton "Duration s": "5"
      - paragraph: Requested simulation horizon, in seconds; at most 3,000 samples.
      - text: Scenario XDL extension · default 5
      - button "Apply" [disabled]
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
  1   | import { test, expect, type Page, type Locator } from "@playwright/test";
  2   | import { createHash } from "node:crypto";
  3   | import { readFileSync, writeFileSync, realpathSync } from "node:fs";
  4   | import path from "node:path";
  5   | import { execFileSync } from "node:child_process";
  6   | import { connectStudio } from "./connect-studio";
  7   | import { renderedContrast } from "./contrast";
  8   |
  9   | async function tabTo(page: Page, target: Locator) {
> 10  |   await expect(target).toBeVisible();
      |                        ^ Error: expect(locator).toBeVisible() failed
  11  |   // A removed error control can leave traversal after the persistent header.
  12  |   // Native reverse traversal reaches it without walking every recent-project row.
  13  |   for (const [key, limit] of [
  14  |     ["Shift+Tab", 40],
  15  |     ["Tab", 220],
  16  |   ] as const) {
  17  |     for (let i = 0; i < limit; i++) {
  18  |       if (await target.evaluate((n) => document.activeElement === n)) return;
  19  |       await page.keyboard.press(key);
  20  |     }
  21  |   }
  22  |   await expect(target).toBeFocused();
  23  | }
  24  | async function activate(page: Page, target: Locator) {
  25  |   await tabTo(page, target);
  26  |   await expect(target).toBeFocused();
  27  |   await page.keyboard.press("Enter");
  28  | }
  29  | const group = (page: Page) =>
  30  |   page.getByRole("group", { name: "Source recovery", exact: true });
  31  | const home = (page: Page) =>
  32  |   page.getByRole("button", { name: "X-Verse Studio home", exact: true });
  33  | const source = (page: Page) =>
  34  |   page.getByRole("button", { name: "XDL source", exact: true });
  35  | const digest = (value: string | Buffer) =>
  36  |   "sha256:" + createHash("sha256").update(value).digest("hex");
  37  | const read = (page: Page, pid: string) =>
  38  |   page.request.get(`/api/v1/projects/${pid}`).then((r) => r.json());
  39  | async function runs(page: Page, pid: string) {
  40  |   return (await page.request.get("/api/v1/runs").then((r) => r.json())).items
  41  |     .filter((r: any) => r.projectId === pid)
  42  |     .map((r: any) => r.runId)
  43  |     .sort();
  44  | }
  45  | async function create(page: Page, name: string) {
  46  |   const project = await page.evaluate(async (name) => {
  47  |     const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
  48  |     const r = await fetch("/api/v1/projects", {
  49  |       method: "POST",
  50  |       headers: {
  51  |         "Content-Type": "application/json",
  52  |         "X-CSRF-Token": csrfToken,
  53  |       },
  54  |       body: JSON.stringify({ name }),
  55  |     });
  56  |     if (!r.ok) throw Error("Owned recovery project creation failed");
  57  |     const p = await r.json();
  58  |     localStorage.setItem("studio.projectId", p.projectId);
  59  |     return p;
  60  |   }, name);
  61  |   await page.reload();
  62  |   await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  63  |   return project;
  64  | }
  65  | function ownedPath(...parts: string[]) {
  66  |   const data = process.env.STUDIO_BROWSER_DATA;
  67  |   expect(data).toBeTruthy();
  68  |   const root = realpathSync(data!);
  69  |   const file = path.resolve(root, ...parts);
  70  |   expect(file.startsWith(root + path.sep)).toBe(true);
  71  |   return file;
  72  | }
  73  | async function prepare(page: Page, name: string, broken = false) {
  74  |   const project = await create(page, name),
  75  |     pid = project.projectId,
  76  |     id = Object.keys(project.documents).find((id) =>
  77  |       project.documents[id].path.endsWith("/system.xdl.yaml"),
  78  |     )!,
  79  |     document = project.documents[id];
  80  |   const file = ownedPath(
  81  |     "projects",
  82  |     pid,
  83  |     "revisions",
  84  |     String(project.revision),
  85  |     document.path,
  86  |   );
  87  |   expect(realpathSync(file)).toBe(file);
  88  |   expect(readFileSync(file, "utf8")).toBe(document.content);
  89  |   const observed = broken
  90  |     ? Buffer.from([0xff, 0xfe, 0x00, 0x61])
  91  |     : Buffer.from(
  92  |         document.content + "\n# isolated owned external recovery fixture\n",
  93  |       );
  94  |   writeFileSync(file, observed);
  95  |   try {
  96  |     await page.reload();
  97  |     await expect(group(page)).toBeVisible();
  98  |   } catch (error) {
  99  |     writeFileSync(file, document.content);
  100 |     throw error;
  101 |   }
  102 |   return {
  103 |     project,
  104 |     pid,
  105 |     id,
  106 |     file,
  107 |     observed,
  108 |     restore() {
  109 |       writeFileSync(file, document.content);
  110 |     },
```
