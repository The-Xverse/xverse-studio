# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: source-accessibility.spec.ts >> source accessibility: late save preserves deliberate focus at 1024x768
- Location: tests/e2e/source-accessibility.spec.ts:294:9

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false

Call Log:
- Timeout 10000ms exceeded while waiting on the predicate
```

# Page snapshot

```yaml
- generic [ref=f1e3]:
  - link "Skip to workspace" [ref=f1e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=f1e5]:
    - button "X-Verse Studio home" [ref=f1e6] [cursor=pointer]:
      - generic [ref=f1e7]: X
      - generic [ref=f1e8]: X-VERSE STUDIO
    - generic [ref=f1e10]: Local workspace
    - button "Environment" [ref=f1e12] [cursor=pointer]
    - generic "Local operator" [ref=f1e19]: LO
  - generic [ref=f1e20]:
    - navigation "Main navigation" [ref=f1e21]:
      - button "Workspace" [ref=f1e22] [cursor=pointer]
      - button "Catalog" [ref=f1e29] [cursor=pointer]
      - button "Laboratory" [ref=f1e36] [cursor=pointer]:
        - generic [ref=f1e40]: Lab
      - button "Compatibility and environment" [ref=f1e41] [cursor=pointer]:
        - generic [ref=f1e47]: Settings
      - generic [ref=f1e48]: v0.1
    - main [ref=f1e49]:
      - generic [ref=f1e51]:
        - text: Source revision saved. Validate it before running.
        - button "Dismiss notice" [ref=f1e55] [cursor=pointer]
      - generic [ref=f1e58]:
        - generic [ref=f1e59]:
          - generic [ref=f1e60]:
            - button "Workspace" [ref=f1e61] [cursor=pointer]
            - generic [ref=f1e64]: System
          - generic [ref=f1e65]:
            - heading "Late source deliberate focus 1024" [level=1] [ref=f1e72]
            - generic [ref=f1e73]: Draft
        - generic [ref=f1e74]:
          - button "Dependencies" [ref=f1e75] [cursor=pointer]
          - button "Undo" [disabled] [ref=f1e76]
          - button "Redo" [disabled] [ref=f1e77]
          - button "Export" [ref=f1e78] [cursor=pointer]
          - button "Validate" [ref=f1e81] [cursor=pointer]
          - button "Preflight & run" [ref=f1e84] [cursor=pointer]
      - tablist "System workflows" [ref=f1e87]:
        - tab "Model" [selected] [ref=f1e88] [cursor=pointer]
        - tab "Connections" [ref=f1e94] [cursor=pointer]
        - tab "Deployment" [ref=f1e99] [cursor=pointer]
        - tab "Experiments" [ref=f1e102] [cursor=pointer]
        - tab "Results" [ref=f1e105] [cursor=pointer]
        - button "XDL source" [ref=f1e109] [cursor=pointer]
      - generic [ref=f1e112]:
        - generic [ref=f1e113]:
          - text: Draft revision
          - code [ref=f1e115]: "2"
        - generic [ref=f1e116]: 3 elements · 2 connections
        - generic [ref=f1e117]:
          - text: Execution scope
          - generic [ref=f1e118]: Owned reference
      - generic [ref=f1e119]:
        - complementary "Structured model navigation" [ref=f1e120]:
          - generic [ref=f1e121]:
            - heading "System explorer" [level=2] [ref=f1e122]
            - button "View XDL source" [ref=f1e123] [cursor=pointer]
          - textbox "Search elements" [ref=f1e130]:
            - /placeholder: Find an element…
          - generic [ref=f1e131]:
            - strong [ref=f1e137]: reference-loop
            - generic [ref=f1e138]: "3"
            - button "Group by node" [ref=f1e139] [cursor=pointer]
          - generic [ref=f1e140]:
            - button "controller controller" [ref=f1e141] [cursor=pointer]:
              - generic [ref=f1e147]: controller
              - generic [ref=f1e148]: controller
            - button "plant plant" [ref=f1e149] [cursor=pointer]:
              - generic [ref=f1e155]: plant
              - generic [ref=f1e156]: plant
            - button "observer-node observer" [ref=f1e157] [cursor=pointer]:
              - generic [ref=f1e160]: observer-node
              - generic [ref=f1e161]: observer
          - generic [ref=f1e162]:
            - generic [ref=f1e163]: RESOURCES
            - button "reference-controller Component" [ref=f1e164] [cursor=pointer]:
              - generic [ref=f1e167]: reference-controller
              - generic [ref=f1e168]: Component
            - button "reference-plant Component" [ref=f1e169] [cursor=pointer]:
              - generic [ref=f1e172]: reference-plant
              - generic [ref=f1e173]: Component
            - button "reference-loop System" [ref=f1e174] [cursor=pointer]:
              - generic [ref=f1e177]: reference-loop
              - generic [ref=f1e178]: System
            - button "local-reference Deployment" [ref=f1e179] [cursor=pointer]:
              - generic [ref=f1e182]: local-reference
              - generic [ref=f1e183]: Deployment
            - button "reference-response Scenario" [ref=f1e184] [cursor=pointer]:
              - generic [ref=f1e187]: reference-response
              - generic [ref=f1e188]: Scenario
            - button "experiment-lite Profile" [ref=f1e189] [cursor=pointer]:
              - generic [ref=f1e192]: experiment-lite
              - generic [ref=f1e193]: Profile
            - button "studio-experiments Profile" [ref=f1e194] [cursor=pointer]:
              - generic [ref=f1e197]: studio-experiments
              - generic [ref=f1e198]: Profile
          - button "Add element" [ref=f1e200] [cursor=pointer]
        - region "Model canvas" [ref=f1e203]:
          - generic:
            - generic [ref=f1e204]:
              - generic [ref=f1e205]: LOGICAL MODEL
              - generic [ref=f1e206]: 1.0.0
            - generic [ref=f1e207]:
              - button "Table view" [ref=f1e208] [cursor=pointer]
              - button "Auto layout" [ref=f1e209] [cursor=pointer]
              - button "Save layout" [ref=f1e210] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f1e211]:
            - generic [ref=f1e213]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=f1e214] [cursor=pointer]:
                      - generic [ref=f1e217]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=f1e219] [cursor=pointer]:
                      - generic [ref=f1e222]: state-flow
                - generic:
                  - group [ref=f1e224]:
                    - generic [ref=f1e225]:
                      - generic [ref=f1e227]: controller
                      - strong [ref=f1e236]: controller
                      - code [ref=f1e237]: controller
                      - list "Named ports" [ref=f1e238]:
                        - listitem [ref=f1e239]:
                          - generic [aria-hidden] [ref=f1e240]: ←
                          - code [ref=f1e241]: controller-out
                          - generic [ref=f1e242]: output
                      - generic [ref=f1e243]:
                        - generic [ref=f1e244]: Logical element
                        - generic [ref=f1e245]: 1 ports
                  - group [ref=f1e247]:
                    - generic [ref=f1e248]:
                      - generic [ref=f1e250]: plant
                      - strong [ref=f1e259]: plant
                      - code [ref=f1e260]: plant
                      - list "Named ports" [ref=f1e261]:
                        - listitem [ref=f1e262]:
                          - generic [aria-hidden] [ref=f1e263]: →
                          - code [ref=f1e264]: plant-in
                          - generic [ref=f1e265]: input
                        - listitem [ref=f1e266]:
                          - generic [aria-hidden] [ref=f1e267]: ←
                          - code [ref=f1e268]: plant-out
                          - generic [ref=f1e269]: output
                      - generic [ref=f1e270]:
                        - generic [ref=f1e271]: Logical element
                        - generic [ref=f1e272]: 2 ports
                  - group [ref=f1e274]:
                    - generic [ref=f1e275]:
                      - generic [ref=f1e277]: observer
                      - strong [ref=f1e283]: observer-node
                      - code [ref=f1e284]: observer-node
                      - list "Named ports" [ref=f1e285]:
                        - listitem [ref=f1e286]:
                          - generic [aria-hidden] [ref=f1e287]: →
                          - code [ref=f1e288]: observer-in
                          - generic [ref=f1e289]: input
                      - generic [ref=f1e290]:
                        - generic [ref=f1e291]: Logical element
                        - generic [ref=f1e292]: 1 ports
            - generic "Control Panel" [ref=f1e294]:
              - button "Zoom In" [ref=f1e295] [cursor=pointer]
              - button "Zoom Out" [ref=f1e298] [cursor=pointer]
              - button "Fit View" [ref=f1e301] [cursor=pointer]
            - img "Mini Map" [ref=f1e305]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f1e310]:
          - heading "System inspector" [level=2] [ref=f1e312]
          - generic [ref=f1e318]:
            - heading "reference-loop" [level=3] [ref=f1e322]
            - paragraph [ref=f1e323]: Authoritative XDL System
            - generic [ref=f1e324]: Draft model
          - navigation "Model location" [ref=f1e325]:
            - button "reference-loop" [ref=f1e326] [cursor=pointer]
          - generic [ref=f1e327]:
            - button "Properties" [ref=f1e328] [cursor=pointer]
            - button "Parameters" [ref=f1e329] [cursor=pointer]
          - generic [ref=f1e330]:
            - paragraph [ref=f1e331]: Select an element in the graph or explorer to inspect its stable identity, role, realization, and placement.
            - generic [ref=f1e332]:
              - generic [ref=f1e333]:
                - term [ref=f1e334]: Namespace
                - definition [ref=f1e335]: org.xverse.studio.process-control
              - generic [ref=f1e336]:
                - term [ref=f1e337]: XDL version
                - definition [ref=f1e338]: xverse.io/xdl/v1alpha1
              - generic [ref=f1e339]:
                - term [ref=f1e340]: Resources
                - definition [ref=f1e341]: "7"
              - generic [ref=f1e342]:
                - term [ref=f1e343]: Evidence scope
                - definition [ref=f1e344]: Owned reference only
            - heading "Reference parameters" [level=4] [ref=f1e345]
            - group [ref=f1e347]:
              - generic [ref=f1e348]:
                - generic [ref=f1e349]:
                  - text: Target
                  - generic [ref=f1e350]: "1"
                  - spinbutton "Target 1" [ref=f1e351]: "1"
                - paragraph [ref=f1e352]: Normalized reference setpoint, dimensionless.
                - generic [ref=f1e353]:
                  - generic [ref=f1e354]: Scenario XDL extension · default 1
                  - button "Apply" [disabled] [ref=f1e355]
              - generic [ref=f1e356]:
                - generic [ref=f1e357]:
                  - text: Response gain
                  - generic [ref=f1e358]: "1"
                  - spinbutton "Response gain 1" [ref=f1e359]: "0.8"
                - paragraph [ref=f1e360]: First-order response coefficient; gain × timestep must be at most one.
                - generic [ref=f1e361]:
                  - generic [ref=f1e362]: Scenario XDL extension · default 0.8
                  - button "Apply" [disabled] [ref=f1e363]
              - generic [ref=f1e364]:
                - generic [ref=f1e365]:
                  - text: Initial state
                  - generic [ref=f1e366]: "1"
                  - spinbutton "Initial state 1" [ref=f1e367]: "0"
                - paragraph [ref=f1e368]: Initial normalized scalar state.
                - generic [ref=f1e369]:
                  - generic [ref=f1e370]: Scenario XDL extension · default 0
                  - button "Apply" [disabled] [ref=f1e371]
              - generic [ref=f1e372]:
                - generic [ref=f1e373]:
                  - text: Duration
                  - generic [ref=f1e374]: s
                  - spinbutton "Duration s" [ref=f1e375]: "5"
                - paragraph [ref=f1e376]: Requested simulation horizon, in seconds; at most 3,000 samples.
                - generic [ref=f1e377]:
                  - generic [ref=f1e378]: Scenario XDL extension · default 5
                  - button "Apply" [disabled] [ref=f1e379]
              - generic [ref=f1e380]:
                - generic [ref=f1e381]:
                  - text: Time step
                  - generic [ref=f1e382]: s
                  - spinbutton "Time step s" [ref=f1e383]: "0.1"
                - paragraph [ref=f1e384]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                - generic [ref=f1e385]:
                  - generic [ref=f1e386]: Scenario XDL extension · default 0.1
                  - button "Apply" [disabled] [ref=f1e387]
              - generic [ref=f1e388]:
                - generic [ref=f1e389]:
                  - text: Reference fault
                  - generic [ref=f1e390]: "1"
                  - combobox "Reference fault 1" [ref=f1e391]:
                    - option "none" [selected]
                    - option "stuck-sensor"
                - paragraph [ref=f1e392]: Owned model fault only; stuck-sensor freezes the reported observation.
                - generic [ref=f1e393]:
                  - generic [ref=f1e394]: Scenario XDL extension · default none
                  - button "Apply" [disabled] [ref=f1e395]
          - generic [ref=f1e396]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f1e401]:
        - generic [ref=f1e402]: Local project · Saved on backend
        - generic [ref=f1e405]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e406]: 1 provider(s) available
  - dialog [ref=f1e408]:
    - banner [ref=f1e409]:
      - heading "Authored XDL source" [level=2] [ref=f1e410]
      - button "Close dialog" [ref=f1e411] [cursor=pointer]
    - generic [ref=f1e414]:
      - generic [ref=f1e415]:
        - generic [ref=f1e416]:
          - text: Resource
          - combobox "Resource" [ref=f1e417]:
            - option "xdl/controller.xdl.yaml"
            - option "xdl/plant.xdl.yaml"
            - option "xdl/system.xdl.yaml" [selected]
            - option "xdl/deployment.xdl.yaml"
            - option "xdl/scenario.xdl.yaml"
            - option "xdl/profile.xdl.yaml"
            - option "xdl/evaluation-profile.xdl.yaml"
        - generic [ref=f1e418]: Saved revision
        - generic [ref=f1e419]:
          - button "Undo" [ref=f1e420] [cursor=pointer]
          - button "Redo" [disabled] [ref=f1e421]
          - button "Compare changes" [ref=f1e422] [cursor=pointer]
      - paragraph [ref=f1e423]: Exact authored content is retained. Unknown extensions stay intact; platform validation decides whether the revision is executable. Saving changes only the draft.
      - generic [ref=f1e425]:
        - generic [ref=f1e426]: XDL source
        - textbox "XDL source" [active] [ref=f1e427]: "apiVersion: xverse.io/xdl/v1alpha1 kind: System metadata: namespace: org.xverse.studio.process-control name: reference-loop version: 1.0.0 description: Explore a normalized process response, tune the setpoint and compare measured reference observations. provenance: source: urn:xverse:studio:reference revision: 1.0.0 maturity: prototype limitations: - Owned executable reference only; no external simulator, device or scientific fidelity claim. spec: nodes: - id: controller-node roles: - controller - id: plant-node roles: - plant - id: observer-node roles: - observer componentInstances: - id: controller componentRef: apiVersion: xverse.io/xdl/v1alpha1 kind: Component namespace: org.xverse.studio.process-control name: reference-controller nodeId: controller-node - id: plant componentRef: apiVersion: xverse.io/xdl/v1alpha1 kind: Component namespace: org.xverse.studio.process-control name: reference-plant nodeId: plant-node interfaces: - id: command direction: bidirectional payloadSchema: urn:xverse:studio:normalized-scalar:v1 unitSemantics: '1' compatibility: exact - id: state direction: bidirectional payloadSchema: urn:xverse:studio:normalized-scalar:v1 unitSemantics: '1' compatibility: exact endpoints: - id: controller-out ownerId: controller interfaceId: command direction: output - id: plant-in ownerId: plant interfaceId: command direction: input - id: plant-out ownerId: plant interfaceId: state direction: output - id: observer-in ownerId: observer-node interfaceId: state direction: input flows: - id: command-flow sourceEndpointId: controller-out destinationEndpointIds: - plant-in interfaceId: command deliveryIntent: ordered timeDomainId: simulation-time - id: state-flow sourceEndpointId: plant-out destinationEndpointIds: - observer-in interfaceId: state deliveryIntent: ordered timeDomainId: simulation-time timeDomains: - id: simulation-time clockClass: simulation epoch: '0' rate: '1' monotonic: true defaultTimeDomainId: simulation-time # held-source-1024"
      - generic [ref=f1e428]:
        - generic [ref=f1e429]:
          - text: Draft revision
          - code [ref=f1e430]: "2"
          - text: · UTF-8 · 2,305 bytes
        - button "Save source revision" [disabled] [ref=f1e431]
```

# Test source

```ts
  27  |   expect(index).toBeGreaterThanOrEqual(0);
  28  |   await tabTo(page, target);
  29  |   await page.keyboard.press("Home");
  30  |   for (let i = 0; i < index; i++) await page.keyboard.press("ArrowDown");
  31  |   await expect(target).toHaveValue(value);
  32  | }
  33  | const dialog = (page: Page) =>
  34  |   page.getByRole("dialog", { name: "Authored XDL source", exact: true });
  35  | const text = (page: Page) =>
  36  |   dialog(page).getByRole("textbox", { name: /^(XDL source|Edited draft)$/ });
  37  | const save = (page: Page) =>
  38  |   dialog(page).getByRole("button", {
  39  |     name: "Save source revision",
  40  |     exact: true,
  41  |   });
  42  | async function read(page: Page, id: string) {
  43  |   return page.request.get(`/api/v1/projects/${id}`).then((r) => r.json());
  44  | }
  45  | async function runIds(page: Page, id: string) {
  46  |   return (await page.request.get("/api/v1/runs").then((r) => r.json())).items
  47  |     .filter((r: any) => r.projectId === id)
  48  |     .map((r: any) => r.runId)
  49  |     .sort();
  50  | }
  51  | const docId = (project: any, suffix: string): string =>
  52  |   Object.keys(project.documents).find((id) =>
  53  |     project.documents[id].path.endsWith("/" + suffix),
  54  |   )!;
  55  | const cache = (page: Page, projectId: string, id: string) =>
  56  |   page.evaluate(
  57  |     ({ projectId, id }) =>
  58  |       sessionStorage.getItem(`studio.draft.${projectId}.${id}`),
  59  |     { projectId, id },
  60  |   );
  61  | async function create(page: Page, name: string) {
  62  |   const project = await page.evaluate(async (name) => {
  63  |     const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
  64  |     const r = await fetch("/api/v1/projects", {
  65  |       method: "POST",
  66  |       headers: {
  67  |         "Content-Type": "application/json",
  68  |         "X-CSRF-Token": csrfToken,
  69  |       },
  70  |       body: JSON.stringify({ name }),
  71  |     });
  72  |     if (!r.ok) throw Error("Owned source fixture creation failed");
  73  |     const p = await r.json();
  74  |     localStorage.setItem("studio.projectId", p.projectId);
  75  |     return p;
  76  |   }, name);
  77  |   await page.reload();
  78  |   await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  79  |   return project;
  80  | }
  81  | async function open(page: Page, id: string) {
  82  |   await activate(
  83  |     page,
  84  |     page.getByRole("button", { name: "XDL source", exact: true }),
  85  |   );
  86  |   await choose(page, dialog(page).getByLabel("Resource", { exact: true }), id);
  87  |   await expect(text(page)).toBeEnabled();
  88  | }
  89  | async function append(page: Page, comment: string) {
  90  |   await tabTo(page, text(page));
  91  |   await page.keyboard.press("ControlOrMeta+End");
  92  |   await page.keyboard.insertText(`\n# ${comment}\n`);
  93  |   return text(page).inputValue();
  94  | }
  95  | async function holdPut(page: Page, projectId: string, id: string) {
  96  |   const pattern = `**/api/v1/projects/${projectId}/documents/${id}`;
  97  |   let release!: () => void,
  98  |     ready = false,
  99  |     seen = false,
  100 |     actual: any = null,
  101 |     finished: Promise<void> | undefined;
  102 |   const held = new Promise<void>((resolve) => {
  103 |     release = resolve;
  104 |   });
  105 |   await page.route(pattern, async (route) => {
  106 |     if (seen || route.request().method() !== "PUT") {
  107 |       await route.continue();
  108 |       return;
  109 |     }
  110 |     seen = true;
  111 |     let finish!: () => void;
  112 |     finished = new Promise<void>((resolve) => {
  113 |       finish = resolve;
  114 |     });
  115 |     try {
  116 |       const response = await route.fetch();
  117 |       actual = { status: response.status(), body: await response.json() };
  118 |       ready = true;
  119 |       await held;
  120 |       await route.fulfill({ response });
  121 |     } finally {
  122 |       finish();
  123 |     }
  124 |   });
  125 |   return {
  126 |     async ready() {
> 127 |       await expect.poll(() => ready).toBe(true);
      |                                      ^ Error: expect(received).toBe(expected) // Object.is equality
  128 |       return actual;
  129 |     },
  130 |     async release() {
  131 |       release();
  132 |       await finished;
  133 |     },
  134 |     async close() {
  135 |       release();
  136 |       await finished;
  137 |       await page.unroute(pattern);
  138 |     },
  139 |   };
  140 | }
  141 | async function geometry(target: Locator) {
  142 |   return target.evaluate((n) => {
  143 |     const box = n.getBoundingClientRect(),
  144 |       style = getComputedStyle(n);
  145 |     return {
  146 |       focused: document.activeElement === n,
  147 |       activeTag: document.activeElement?.tagName,
  148 |       box: box.toJSON(),
  149 |       viewport: { width: innerWidth, height: innerHeight },
  150 |       outline: style.outlineStyle,
  151 |       outlineWidth: parseFloat(style.outlineWidth),
  152 |     };
  153 |   });
  154 | }
  155 |
  156 | for (const viewport of [
  157 |   { width: 1024, height: 768 },
  158 |   { width: 1440, height: 900 },
  159 | ]) {
  160 |   for (const trigger of ["shortcut", "button"] as const) {
  161 |     test(`source accessibility: native undo redo and ${trigger} save at ${viewport.width}x${viewport.height}`, async ({
  162 |       page,
  163 |     }, testInfo) => {
  164 |       test.setTimeout(90000);
  165 |       await page.setViewportSize(viewport);
  166 |       await connectStudio(page, testInfo);
  167 |       const project = await create(
  168 |           page,
  169 |           `Keyboard source ${trigger} ${viewport.width}`,
  170 |         ),
  171 |         pid = project.projectId,
  172 |         id = docId(project, "system.xdl.yaml"),
  173 |         runs = await runIds(page, pid);
  174 |       await open(page, id);
  175 |       const original = project.documents[id].content;
  176 |       const edited = await append(page, `source-${trigger}-${viewport.width}`);
  177 |       expect(edited).toBe(
  178 |         original + `\n# source-${trigger}-${viewport.width}\n`,
  179 |       );
  180 |       await page.keyboard.press("ControlOrMeta+z");
  181 |       await expect(text(page)).toHaveValue(original);
  182 |       await page.keyboard.press("ControlOrMeta+Shift+Z");
  183 |       await expect.soft(text(page)).toHaveValue(edited);
  184 |       const shortcutRedoWorked = (await text(page).inputValue()) === edited;
  185 |       if (!shortcutRedoWorked) {
  186 |         await activate(
  187 |           page,
  188 |           dialog(page).getByRole("button", { name: "Redo", exact: true }),
  189 |         );
  190 |         await expect(text(page)).toHaveValue(edited);
  191 |       }
  192 |       await expect
  193 |         .soft(text(page))
  194 |         .toHaveAccessibleDescription(/Exact authored content is retained/);
  195 |       const writes: { path: string; body: any }[] = [];
  196 |       page.on("request", (r) => {
  197 |         if (r.method() === "PUT")
  198 |           writes.push({
  199 |             path: new URL(r.url()).pathname,
  200 |             body: r.postDataJSON(),
  201 |           });
  202 |       });
  203 |       const response = page.waitForResponse(
  204 |         (r) =>
  205 |           new URL(r.url()).pathname ===
  206 |             `/api/v1/projects/${pid}/documents/${id}` &&
  207 |           r.request().method() === "PUT",
  208 |       );
  209 |       if (trigger === "shortcut") {
  210 |         await tabTo(page, text(page));
  211 |         await page.keyboard.press("ControlOrMeta+s");
  212 |       } else await activate(page, save(page));
  213 |       expect((await response).status()).toBe(200);
  214 |       await page.waitForLoadState("networkidle");
  215 |       await expect(text(page)).toBeEnabled();
  216 |       await expect(save(page)).toBeDisabled();
  217 |       await expect.soft(text(page)).toBeFocused();
  218 |       const focus = await geometry(text(page));
  219 |       expect.soft(focus.outline).not.toBe("none");
  220 |       expect.soft(focus.outlineWidth).toBeGreaterThan(0);
  221 |       expect.soft(focus.box.top).toBeGreaterThanOrEqual(0);
  222 |       expect.soft(focus.box.bottom).toBeLessThanOrEqual(viewport.height);
  223 |       await expect.poll(() => cache(page, pid, id)).toBe(null);
  224 |       const saved = await read(page, pid);
  225 |       expect(saved.revision).toBe(project.revision + 1);
  226 |       expect(saved.documents[id].content).toBe(edited);
  227 |       expect(Object.keys(saved.documents).sort()).toEqual(
```
