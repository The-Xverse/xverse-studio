# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: source-recovery-accessibility.spec.ts >> recovery accessibility: late unreadable recovery preserves Home at 1440x900
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
    - generic [ref=f2e12]: REFERENCE PREVIEW
    - button "Environment" [ref=f2e13] [cursor=pointer]
    - generic "Local operator" [ref=f2e20]: LO
  - generic [ref=f2e21]:
    - navigation "Main navigation" [ref=f2e22]:
      - button "Workspace" [ref=f2e23] [cursor=pointer]
      - button "Catalog" [ref=f2e30] [cursor=pointer]
      - button "Laboratory" [ref=f2e37] [cursor=pointer]:
        - generic [ref=f2e41]: Lab
      - button "Compatibility and environment" [ref=f2e42] [cursor=pointer]:
        - generic [ref=f2e48]: Settings
      - generic [ref=f2e49]: v0.1
    - main [ref=f2e50]:
      - generic [ref=f2e52]:
        - text: Recovered as revision 2. The observed external bytes are preserved in backup rec-120b3357-4590-4112-be23-76612b580094.
        - button "Dismiss notice" [ref=f2e56] [cursor=pointer]
      - generic [ref=f2e59]:
        - generic [ref=f2e60]:
          - generic [ref=f2e61]:
            - button "Workspace" [ref=f2e62] [cursor=pointer]
            - generic [ref=f2e65]: System
          - generic [ref=f2e66]:
            - heading "Late recovery true Home 1440" [level=1] [ref=f2e73]
            - generic [ref=f2e74]: Draft
            - generic [ref=f2e75]: rev 2
        - generic [ref=f2e76]:
          - button "Dependencies" [ref=f2e77] [cursor=pointer]
          - button "Undo" [disabled] [ref=f2e78]
          - button "Redo" [disabled] [ref=f2e79]
          - button "Export" [ref=f2e80] [cursor=pointer]
          - button "Validate" [ref=f2e83] [cursor=pointer]
          - button "Preflight & run" [ref=f2e86] [cursor=pointer]
      - tablist "System workflows" [ref=f2e89]:
        - tab "Model" [selected] [ref=f2e90] [cursor=pointer]
        - tab "Connections" [ref=f2e96] [cursor=pointer]
        - tab "Deployment" [ref=f2e101] [cursor=pointer]
        - tab "Experiments" [ref=f2e104] [cursor=pointer]
        - tab "Results" [ref=f2e107] [cursor=pointer]
        - button "XDL source" [active] [ref=f2e111] [cursor=pointer]
      - generic [ref=f2e114]:
        - generic [ref=f2e115]:
          - text: Draft revision
          - code [ref=f2e117]: "2"
        - generic [ref=f2e118]: 3 elements · 2 connections
        - generic [ref=f2e119]:
          - text: Execution scope
          - generic [ref=f2e120]: Owned reference
      - generic [ref=f2e121]:
        - complementary "Structured model navigation" [ref=f2e122]:
          - generic [ref=f2e123]:
            - heading "System explorer" [level=2] [ref=f2e124]
            - button "View XDL source" [ref=f2e125] [cursor=pointer]
          - textbox "Search elements" [ref=f2e132]:
            - /placeholder: Find an element…
          - generic [ref=f2e133]:
            - strong [ref=f2e139]: reference-loop
            - generic [ref=f2e140]: "3"
            - button "Group by node" [ref=f2e141] [cursor=pointer]
          - generic [ref=f2e142]:
            - button "controller controller" [ref=f2e143] [cursor=pointer]:
              - generic [ref=f2e149]: controller
              - generic [ref=f2e150]: controller
            - button "plant plant" [ref=f2e151] [cursor=pointer]:
              - generic [ref=f2e157]: plant
              - generic [ref=f2e158]: plant
            - button "observer-node observer" [ref=f2e159] [cursor=pointer]:
              - generic [ref=f2e162]: observer-node
              - generic [ref=f2e163]: observer
          - generic [ref=f2e164]:
            - generic [ref=f2e165]: RESOURCES
            - button "reference-controller Component" [ref=f2e166] [cursor=pointer]:
              - generic [ref=f2e169]: reference-controller
              - generic [ref=f2e170]: Component
            - button "reference-plant Component" [ref=f2e171] [cursor=pointer]:
              - generic [ref=f2e174]: reference-plant
              - generic [ref=f2e175]: Component
            - button "reference-loop System" [ref=f2e176] [cursor=pointer]:
              - generic [ref=f2e179]: reference-loop
              - generic [ref=f2e180]: System
            - button "local-reference Deployment" [ref=f2e181] [cursor=pointer]:
              - generic [ref=f2e184]: local-reference
              - generic [ref=f2e185]: Deployment
            - button "reference-response Scenario" [ref=f2e186] [cursor=pointer]:
              - generic [ref=f2e189]: reference-response
              - generic [ref=f2e190]: Scenario
            - button "experiment-lite Profile" [ref=f2e191] [cursor=pointer]:
              - generic [ref=f2e194]: experiment-lite
              - generic [ref=f2e195]: Profile
            - button "studio-experiments Profile" [ref=f2e196] [cursor=pointer]:
              - generic [ref=f2e199]: studio-experiments
              - generic [ref=f2e200]: Profile
          - button "Add element" [ref=f2e202] [cursor=pointer]
        - region "Model canvas" [ref=f2e205]:
          - generic:
            - generic [ref=f2e206]:
              - generic [ref=f2e207]: LOGICAL MODEL
              - generic [ref=f2e208]: 1.0.0
            - generic [ref=f2e209]:
              - button "Table view" [ref=f2e210] [cursor=pointer]
              - button "Auto layout" [ref=f2e211] [cursor=pointer]
              - button "Save layout" [ref=f2e212] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f2e213]:
            - generic [ref=f2e215]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=f2e216] [cursor=pointer]:
                      - generic [ref=f2e219]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=f2e221] [cursor=pointer]:
                      - generic [ref=f2e224]: state-flow
                - generic:
                  - group [ref=f2e226]:
                    - generic [ref=f2e227]:
                      - generic [ref=f2e229]: controller
                      - strong [ref=f2e238]: controller
                      - code [ref=f2e239]: controller
                      - list "Named ports" [ref=f2e240]:
                        - listitem [ref=f2e241]:
                          - generic [aria-hidden] [ref=f2e242]: ←
                          - code [ref=f2e243]: controller-out
                          - generic [ref=f2e244]: output
                      - generic [ref=f2e245]:
                        - generic [ref=f2e246]: Logical element
                        - generic [ref=f2e247]: 1 ports
                  - group [ref=f2e249]:
                    - generic [ref=f2e250]:
                      - generic [ref=f2e252]: plant
                      - strong [ref=f2e261]: plant
                      - code [ref=f2e262]: plant
                      - list "Named ports" [ref=f2e263]:
                        - listitem [ref=f2e264]:
                          - generic [aria-hidden] [ref=f2e265]: →
                          - code [ref=f2e266]: plant-in
                          - generic [ref=f2e267]: input
                        - listitem [ref=f2e268]:
                          - generic [aria-hidden] [ref=f2e269]: ←
                          - code [ref=f2e270]: plant-out
                          - generic [ref=f2e271]: output
                      - generic [ref=f2e272]:
                        - generic [ref=f2e273]: Logical element
                        - generic [ref=f2e274]: 2 ports
                  - group [ref=f2e276]:
                    - generic [ref=f2e277]:
                      - generic [ref=f2e279]: observer
                      - strong [ref=f2e285]: observer-node
                      - code [ref=f2e286]: observer-node
                      - list "Named ports" [ref=f2e287]:
                        - listitem [ref=f2e288]:
                          - generic [aria-hidden] [ref=f2e289]: →
                          - code [ref=f2e290]: observer-in
                          - generic [ref=f2e291]: input
                      - generic [ref=f2e292]:
                        - generic [ref=f2e293]: Logical element
                        - generic [ref=f2e294]: 1 ports
            - generic "Control Panel" [ref=f2e296]:
              - button "Zoom In" [ref=f2e297] [cursor=pointer]
              - button "Zoom Out" [ref=f2e300] [cursor=pointer]
              - button "Fit View" [ref=f2e303] [cursor=pointer]
            - img "Mini Map" [ref=f2e307]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f2e312]:
          - heading "System inspector" [level=2] [ref=f2e314]
          - generic [ref=f2e320]:
            - heading "reference-loop" [level=3] [ref=f2e324]
            - paragraph [ref=f2e325]: Authoritative XDL System
            - generic [ref=f2e326]: Draft model
          - navigation "Model location" [ref=f2e327]:
            - button "reference-loop" [ref=f2e328] [cursor=pointer]
          - generic [ref=f2e329]:
            - button "Properties" [ref=f2e330] [cursor=pointer]
            - button "Parameters" [ref=f2e331] [cursor=pointer]
          - generic [ref=f2e332]:
            - paragraph [ref=f2e333]: Select an element in the graph or explorer to inspect its stable identity, role, realization, and placement.
            - generic [ref=f2e334]:
              - generic [ref=f2e335]:
                - term [ref=f2e336]: Namespace
                - definition [ref=f2e337]: org.xverse.studio.process-control
              - generic [ref=f2e338]:
                - term [ref=f2e339]: XDL version
                - definition [ref=f2e340]: xverse.io/xdl/v1alpha1
              - generic [ref=f2e341]:
                - term [ref=f2e342]: Resources
                - definition [ref=f2e343]: "7"
              - generic [ref=f2e344]:
                - term [ref=f2e345]: Evidence scope
                - definition [ref=f2e346]: Owned reference only
            - heading "Reference parameters" [level=4] [ref=f2e347]
            - group [ref=f2e349]:
              - generic [ref=f2e350]:
                - generic [ref=f2e351]:
                  - text: Target
                  - generic [ref=f2e352]: "1"
                  - spinbutton "Target 1" [ref=f2e353]: "1"
                - paragraph [ref=f2e354]: Normalized reference setpoint, dimensionless.
                - generic [ref=f2e355]:
                  - generic [ref=f2e356]: Scenario XDL extension · default 1
                  - button "Apply" [disabled] [ref=f2e357]
              - generic [ref=f2e358]:
                - generic [ref=f2e359]:
                  - text: Response gain
                  - generic [ref=f2e360]: "1"
                  - spinbutton "Response gain 1" [ref=f2e361]: "0.8"
                - paragraph [ref=f2e362]: First-order response coefficient; gain × timestep must be at most one.
                - generic [ref=f2e363]:
                  - generic [ref=f2e364]: Scenario XDL extension · default 0.8
                  - button "Apply" [disabled] [ref=f2e365]
              - generic [ref=f2e366]:
                - generic [ref=f2e367]:
                  - text: Initial state
                  - generic [ref=f2e368]: "1"
                  - spinbutton "Initial state 1" [ref=f2e369]: "0"
                - paragraph [ref=f2e370]: Initial normalized scalar state.
                - generic [ref=f2e371]:
                  - generic [ref=f2e372]: Scenario XDL extension · default 0
                  - button "Apply" [disabled] [ref=f2e373]
              - generic [ref=f2e374]:
                - generic [ref=f2e375]:
                  - text: Duration
                  - generic [ref=f2e376]: s
                  - spinbutton "Duration s" [ref=f2e377]: "5"
                - paragraph [ref=f2e378]: Requested simulation horizon, in seconds; at most 3,000 samples.
                - generic [ref=f2e379]:
                  - generic [ref=f2e380]: Scenario XDL extension · default 5
                  - button "Apply" [disabled] [ref=f2e381]
              - generic [ref=f2e382]:
                - generic [ref=f2e383]:
                  - text: Time step
                  - generic [ref=f2e384]: s
                  - spinbutton "Time step s" [ref=f2e385]: "0.1"
                - paragraph [ref=f2e386]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                - generic [ref=f2e387]:
                  - generic [ref=f2e388]: Scenario XDL extension · default 0.1
                  - button "Apply" [disabled] [ref=f2e389]
              - generic [ref=f2e390]:
                - generic [ref=f2e391]:
                  - text: Reference fault
                  - generic [ref=f2e392]: "1"
                  - combobox "Reference fault 1" [ref=f2e393]:
                    - option "none" [selected]
                    - option "stuck-sensor"
                - paragraph [ref=f2e394]: Owned model fault only; stuck-sensor freezes the reported observation.
                - generic [ref=f2e395]:
                  - generic [ref=f2e396]: Scenario XDL extension · default none
                  - button "Apply" [disabled] [ref=f2e397]
          - generic [ref=f2e398]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f2e403]:
        - generic [ref=f2e404]: Local project · Saved on backend
        - generic [ref=f2e407]: Authoritative XDL · Layout stored separately
        - generic [ref=f2e408]: 1 provider(s) available
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
