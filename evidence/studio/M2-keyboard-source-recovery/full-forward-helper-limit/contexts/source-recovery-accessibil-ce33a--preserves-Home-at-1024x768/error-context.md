# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: source-recovery-accessibility.spec.ts >> recovery accessibility: late unreadable recovery preserves Home at 1024x768
- Location: tests/e2e/source-recovery-accessibility.spec.ts:502:11

# Error details

```
Error: Recovery control is unreachable through native Tab order
```

# Page snapshot

```yaml
- generic [ref=f2e3]:
  - link "Skip to workspace" [ref=f2e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=f2e5]:
    - button "X-Verse Studio home" [ref=f2e6] [cursor=pointer]:
      - generic [ref=f2e7]: X
      - generic [ref=f2e8]: X-VERSE STUDIO
    - generic [ref=f2e10]: Local workspace
    - button "Environment" [ref=f2e12] [cursor=pointer]
    - generic "Local operator" [ref=f2e19]: LO
  - generic [ref=f2e20]:
    - navigation "Main navigation" [ref=f2e21]:
      - button "Workspace" [ref=f2e22] [cursor=pointer]
      - button "Catalog" [ref=f2e29] [cursor=pointer]
      - button "Laboratory" [ref=f2e36] [cursor=pointer]:
        - generic [ref=f2e40]: Lab
      - button "Compatibility and environment" [ref=f2e41] [cursor=pointer]:
        - generic [ref=f2e47]: Settings
      - generic [ref=f2e48]: v0.1
    - main [ref=f2e49]:
      - generic [ref=f2e51]:
        - text: Recovered as revision 2. The observed external bytes are preserved in backup rec-8f8bbb6d-7083-4e61-b19f-c1ea3a703f67.
        - button "Dismiss notice" [ref=f2e55] [cursor=pointer]
      - generic [ref=f2e58]:
        - generic [ref=f2e59]:
          - generic [ref=f2e60]:
            - button "Workspace" [ref=f2e61] [cursor=pointer]
            - generic [ref=f2e64]: System
          - generic [ref=f2e65]:
            - heading "Late recovery true Home 1024" [level=1] [ref=f2e72]
            - generic [ref=f2e73]: Draft
        - generic [ref=f2e74]:
          - button "Dependencies" [ref=f2e75] [cursor=pointer]
          - button "Undo" [disabled] [ref=f2e76]
          - button "Redo" [disabled] [ref=f2e77]
          - button "Export" [ref=f2e78] [cursor=pointer]
          - button "Validate" [ref=f2e81] [cursor=pointer]
          - button "Preflight & run" [ref=f2e84] [cursor=pointer]
      - tablist "System workflows" [ref=f2e87]:
        - tab "Model" [selected] [ref=f2e88] [cursor=pointer]
        - tab "Connections" [ref=f2e94] [cursor=pointer]
        - tab "Deployment" [ref=f2e99] [cursor=pointer]
        - tab "Experiments" [ref=f2e102] [cursor=pointer]
        - tab "Results" [ref=f2e105] [cursor=pointer]
        - button "XDL source" [active] [ref=f2e109] [cursor=pointer]
      - generic [ref=f2e112]:
        - generic [ref=f2e113]:
          - text: Draft revision
          - code [ref=f2e115]: "2"
        - generic [ref=f2e116]: 3 elements · 2 connections
        - generic [ref=f2e117]:
          - text: Execution scope
          - generic [ref=f2e118]: Owned reference
      - generic [ref=f2e119]:
        - complementary "Structured model navigation" [ref=f2e120]:
          - generic [ref=f2e121]:
            - heading "System explorer" [level=2] [ref=f2e122]
            - button "View XDL source" [ref=f2e123] [cursor=pointer]
          - textbox "Search elements" [ref=f2e130]:
            - /placeholder: Find an element…
          - generic [ref=f2e131]:
            - strong [ref=f2e137]: reference-loop
            - generic [ref=f2e138]: "3"
            - button "Group by node" [ref=f2e139] [cursor=pointer]
          - generic [ref=f2e140]:
            - button "controller controller" [ref=f2e141] [cursor=pointer]:
              - generic [ref=f2e147]: controller
              - generic [ref=f2e148]: controller
            - button "plant plant" [ref=f2e149] [cursor=pointer]:
              - generic [ref=f2e155]: plant
              - generic [ref=f2e156]: plant
            - button "observer-node observer" [ref=f2e157] [cursor=pointer]:
              - generic [ref=f2e160]: observer-node
              - generic [ref=f2e161]: observer
          - generic [ref=f2e162]:
            - generic [ref=f2e163]: RESOURCES
            - button "reference-controller Component" [ref=f2e164] [cursor=pointer]:
              - generic [ref=f2e167]: reference-controller
              - generic [ref=f2e168]: Component
            - button "reference-plant Component" [ref=f2e169] [cursor=pointer]:
              - generic [ref=f2e172]: reference-plant
              - generic [ref=f2e173]: Component
            - button "reference-loop System" [ref=f2e174] [cursor=pointer]:
              - generic [ref=f2e177]: reference-loop
              - generic [ref=f2e178]: System
            - button "local-reference Deployment" [ref=f2e179] [cursor=pointer]:
              - generic [ref=f2e182]: local-reference
              - generic [ref=f2e183]: Deployment
            - button "reference-response Scenario" [ref=f2e184] [cursor=pointer]:
              - generic [ref=f2e187]: reference-response
              - generic [ref=f2e188]: Scenario
            - button "experiment-lite Profile" [ref=f2e189] [cursor=pointer]:
              - generic [ref=f2e192]: experiment-lite
              - generic [ref=f2e193]: Profile
            - button "studio-experiments Profile" [ref=f2e194] [cursor=pointer]:
              - generic [ref=f2e197]: studio-experiments
              - generic [ref=f2e198]: Profile
          - button "Add element" [ref=f2e200] [cursor=pointer]
        - region "Model canvas" [ref=f2e203]:
          - generic:
            - generic [ref=f2e204]:
              - generic [ref=f2e205]: LOGICAL MODEL
              - generic [ref=f2e206]: 1.0.0
            - generic [ref=f2e207]:
              - button "Table view" [ref=f2e208] [cursor=pointer]
              - button "Auto layout" [ref=f2e209] [cursor=pointer]
              - button "Save layout" [ref=f2e210] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f2e211]:
            - generic [ref=f2e213]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=f2e214] [cursor=pointer]:
                      - generic [ref=f2e217]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=f2e219] [cursor=pointer]:
                      - generic [ref=f2e222]: state-flow
                - generic:
                  - group [ref=f2e224]:
                    - generic [ref=f2e225]:
                      - generic [ref=f2e227]: controller
                      - strong [ref=f2e236]: controller
                      - code [ref=f2e237]: controller
                      - list "Named ports" [ref=f2e238]:
                        - listitem [ref=f2e239]:
                          - generic [aria-hidden] [ref=f2e240]: ←
                          - code [ref=f2e241]: controller-out
                          - generic [ref=f2e242]: output
                      - generic [ref=f2e243]:
                        - generic [ref=f2e244]: Logical element
                        - generic [ref=f2e245]: 1 ports
                  - group [ref=f2e247]:
                    - generic [ref=f2e248]:
                      - generic [ref=f2e250]: plant
                      - strong [ref=f2e259]: plant
                      - code [ref=f2e260]: plant
                      - list "Named ports" [ref=f2e261]:
                        - listitem [ref=f2e262]:
                          - generic [aria-hidden] [ref=f2e263]: →
                          - code [ref=f2e264]: plant-in
                          - generic [ref=f2e265]: input
                        - listitem [ref=f2e266]:
                          - generic [aria-hidden] [ref=f2e267]: ←
                          - code [ref=f2e268]: plant-out
                          - generic [ref=f2e269]: output
                      - generic [ref=f2e270]:
                        - generic [ref=f2e271]: Logical element
                        - generic [ref=f2e272]: 2 ports
                  - group [ref=f2e274]:
                    - generic [ref=f2e275]:
                      - generic [ref=f2e277]: observer
                      - strong [ref=f2e283]: observer-node
                      - code [ref=f2e284]: observer-node
                      - list "Named ports" [ref=f2e285]:
                        - listitem [ref=f2e286]:
                          - generic [aria-hidden] [ref=f2e287]: →
                          - code [ref=f2e288]: observer-in
                          - generic [ref=f2e289]: input
                      - generic [ref=f2e290]:
                        - generic [ref=f2e291]: Logical element
                        - generic [ref=f2e292]: 1 ports
            - generic "Control Panel" [ref=f2e294]:
              - button "Zoom In" [ref=f2e295] [cursor=pointer]
              - button "Zoom Out" [ref=f2e298] [cursor=pointer]
              - button "Fit View" [ref=f2e301] [cursor=pointer]
            - img "Mini Map" [ref=f2e305]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f2e310]:
          - heading "System inspector" [level=2] [ref=f2e312]
          - generic [ref=f2e318]:
            - heading "reference-loop" [level=3] [ref=f2e322]
            - paragraph [ref=f2e323]: Authoritative XDL System
            - generic [ref=f2e324]: Draft model
          - navigation "Model location" [ref=f2e325]:
            - button "reference-loop" [ref=f2e326] [cursor=pointer]
          - generic [ref=f2e327]:
            - button "Properties" [ref=f2e328] [cursor=pointer]
            - button "Parameters" [ref=f2e329] [cursor=pointer]
          - generic [ref=f2e330]:
            - paragraph [ref=f2e331]: Select an element in the graph or explorer to inspect its stable identity, role, realization, and placement.
            - generic [ref=f2e332]:
              - generic [ref=f2e333]:
                - term [ref=f2e334]: Namespace
                - definition [ref=f2e335]: org.xverse.studio.process-control
              - generic [ref=f2e336]:
                - term [ref=f2e337]: XDL version
                - definition [ref=f2e338]: xverse.io/xdl/v1alpha1
              - generic [ref=f2e339]:
                - term [ref=f2e340]: Resources
                - definition [ref=f2e341]: "7"
              - generic [ref=f2e342]:
                - term [ref=f2e343]: Evidence scope
                - definition [ref=f2e344]: Owned reference only
            - heading "Reference parameters" [level=4] [ref=f2e345]
            - group [ref=f2e347]:
              - generic [ref=f2e348]:
                - generic [ref=f2e349]:
                  - text: Target
                  - generic [ref=f2e350]: "1"
                  - spinbutton "Target 1" [ref=f2e351]: "1"
                - paragraph [ref=f2e352]: Normalized reference setpoint, dimensionless.
                - generic [ref=f2e353]:
                  - generic [ref=f2e354]: Scenario XDL extension · default 1
                  - button "Apply" [disabled] [ref=f2e355]
              - generic [ref=f2e356]:
                - generic [ref=f2e357]:
                  - text: Response gain
                  - generic [ref=f2e358]: "1"
                  - spinbutton "Response gain 1" [ref=f2e359]: "0.8"
                - paragraph [ref=f2e360]: First-order response coefficient; gain × timestep must be at most one.
                - generic [ref=f2e361]:
                  - generic [ref=f2e362]: Scenario XDL extension · default 0.8
                  - button "Apply" [disabled] [ref=f2e363]
              - generic [ref=f2e364]:
                - generic [ref=f2e365]:
                  - text: Initial state
                  - generic [ref=f2e366]: "1"
                  - spinbutton "Initial state 1" [ref=f2e367]: "0"
                - paragraph [ref=f2e368]: Initial normalized scalar state.
                - generic [ref=f2e369]:
                  - generic [ref=f2e370]: Scenario XDL extension · default 0
                  - button "Apply" [disabled] [ref=f2e371]
              - generic [ref=f2e372]:
                - generic [ref=f2e373]:
                  - text: Duration
                  - generic [ref=f2e374]: s
                  - spinbutton "Duration s" [ref=f2e375]: "5"
                - paragraph [ref=f2e376]: Requested simulation horizon, in seconds; at most 3,000 samples.
                - generic [ref=f2e377]:
                  - generic [ref=f2e378]: Scenario XDL extension · default 5
                  - button "Apply" [disabled] [ref=f2e379]
              - generic [ref=f2e380]:
                - generic [ref=f2e381]:
                  - text: Time step
                  - generic [ref=f2e382]: s
                  - spinbutton "Time step s" [ref=f2e383]: "0.1"
                - paragraph [ref=f2e384]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                - generic [ref=f2e385]:
                  - generic [ref=f2e386]: Scenario XDL extension · default 0.1
                  - button "Apply" [disabled] [ref=f2e387]
              - generic [ref=f2e388]:
                - generic [ref=f2e389]:
                  - text: Reference fault
                  - generic [ref=f2e390]: "1"
                  - combobox "Reference fault 1" [ref=f2e391]:
                    - option "none" [selected]
                    - option "stuck-sensor"
                - paragraph [ref=f2e392]: Owned model fault only; stuck-sensor freezes the reported observation.
                - generic [ref=f2e393]:
                  - generic [ref=f2e394]: Scenario XDL extension · default none
                  - button "Apply" [disabled] [ref=f2e395]
          - generic [ref=f2e396]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f2e401]:
        - generic [ref=f2e402]: Local project · Saved on backend
        - generic [ref=f2e405]: Authoritative XDL · Layout stored separately
        - generic [ref=f2e406]: 1 provider(s) available
```

# Test source

```ts
  1   | import { test, expect, type Page, type Locator } from "@playwright/test";
  2   | import { createHash } from "node:crypto";
  3   | import { readFileSync, writeFileSync, realpathSync } from "node:fs";
  4   | import path from "node:path";
  5   | import { connectStudio } from "./connect-studio";
  6   | import { renderedContrast } from "./contrast";
  7   |
  8   | async function tabTo(page: Page, target: Locator) {
  9   |   await expect(target).toBeVisible();
  10  |   for (let i = 0; i < 220; i++) {
  11  |     if (await target.evaluate((n) => document.activeElement === n)) return;
  12  |     await page.keyboard.press("Tab");
  13  |   }
> 14  |   throw Error("Recovery control is unreachable through native Tab order");
      |         ^ Error: Recovery control is unreachable through native Tab order
  15  | }
  16  | async function activate(page: Page, target: Locator) {
  17  |   await tabTo(page, target);
  18  |   await page.keyboard.press("Enter");
  19  | }
  20  | const group = (page: Page) =>
  21  |   page.getByRole("group", { name: "Source recovery", exact: true });
  22  | const home = (page: Page) =>
  23  |   page.getByRole("button", { name: "X-Verse Studio home", exact: true });
  24  | const source = (page: Page) =>
  25  |   page.getByRole("button", { name: "XDL source", exact: true });
  26  | async function geometry(target: Locator) {
  27  |   return target.evaluate((n) => {
  28  |     const box = n.getBoundingClientRect(),
  29  |       style = getComputedStyle(n);
  30  |     return {
  31  |       focused: document.activeElement === n,
  32  |       box: box.toJSON(),
  33  |       outline: style.outlineStyle,
  34  |       outlineWidth: parseFloat(style.outlineWidth),
  35  |       viewport: { width: innerWidth, height: innerHeight },
  36  |     };
  37  |   });
  38  | }
  39  | const digest = (value: string | Buffer) =>
  40  |   "sha256:" + createHash("sha256").update(value).digest("hex");
  41  | const read = (page: Page, pid: string) =>
  42  |   page.request.get(`/api/v1/projects/${pid}`).then((r) => r.json());
  43  | async function runs(page: Page, pid: string) {
  44  |   return (await page.request.get("/api/v1/runs").then((r) => r.json())).items
  45  |     .filter((r: any) => r.projectId === pid)
  46  |     .map((r: any) => r.runId)
  47  |     .sort();
  48  | }
  49  | async function create(page: Page, name: string) {
  50  |   const project = await page.evaluate(async (name) => {
  51  |     const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
  52  |     const r = await fetch("/api/v1/projects", {
  53  |       method: "POST",
  54  |       headers: {
  55  |         "Content-Type": "application/json",
  56  |         "X-CSRF-Token": csrfToken,
  57  |       },
  58  |       body: JSON.stringify({ name }),
  59  |     });
  60  |     if (!r.ok) throw Error("Owned recovery project creation failed");
  61  |     const p = await r.json();
  62  |     localStorage.setItem("studio.projectId", p.projectId);
  63  |     return p;
  64  |   }, name);
  65  |   await page.reload();
  66  |   await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  67  |   return project;
  68  | }
  69  | function ownedPath(...parts: string[]) {
  70  |   const data = process.env.STUDIO_BROWSER_DATA;
  71  |   expect(data).toBeTruthy();
  72  |   const root = realpathSync(data!);
  73  |   const file = path.resolve(root, ...parts);
  74  |   expect(file.startsWith(root + path.sep)).toBe(true);
  75  |   return file;
  76  | }
  77  | async function prepare(page: Page, name: string, broken = false) {
  78  |   const project = await create(page, name),
  79  |     pid = project.projectId,
  80  |     id = Object.keys(project.documents).find((id) =>
  81  |       project.documents[id].path.endsWith("/system.xdl.yaml"),
  82  |     )!,
  83  |     document = project.documents[id];
  84  |   const file = ownedPath(
  85  |     "projects",
  86  |     pid,
  87  |     "revisions",
  88  |     String(project.revision),
  89  |     document.path,
  90  |   );
  91  |   expect(realpathSync(file)).toBe(file);
  92  |   expect(readFileSync(file, "utf8")).toBe(document.content);
  93  |   const observed = broken
  94  |     ? Buffer.from([0xff, 0xfe, 0x00, 0x61])
  95  |     : Buffer.from(
  96  |         document.content + "\n# isolated owned external recovery fixture\n",
  97  |       );
  98  |   writeFileSync(file, observed);
  99  |   try {
  100 |     await page.reload();
  101 |     await expect(group(page)).toBeVisible();
  102 |   } catch (error) {
  103 |     writeFileSync(file, document.content);
  104 |     throw error;
  105 |   }
  106 |   return {
  107 |     project,
  108 |     pid,
  109 |     id,
  110 |     file,
  111 |     observed,
  112 |     restore() {
  113 |       writeFileSync(file, document.content);
  114 |     },
```
